"""Slack Events API boundary for manual inventory photo/verification/catalogue threads."""
from __future__ import annotations
import json
import re
import os
import sys
import time
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from shared.slack import SlackClient
from shared.slack.security import verify_signature
from shared.slack.routing import INVENTORY_CHANNEL, PROPERTY_VERIFICATION_CHANNEL
from shared.google_sheets.client import GoogleSheetsClient
from shared.google_sheets import schema
from shared.cloudinary.client import CloudinaryClient
from shared.cloudinary.media import upload_property_images
sys.path.insert(0, str(__file__).rsplit("/", 1)[0] + "/modules/efps-inventory-mgmnt/src")
from pipeline import write_phase1_update, process_phase1
import boto3

_SESSIONS_TABLE = os.environ.get("SESSIONS_TABLE_NAME", "efps-sessions")

# ─────────────────────────────────────────────────────────
# Session helpers
# ─────────────────────────────────────────────────────────

_SESSION_TTL_SECONDS = 86400  # 24 h — matches expires_at set on creation


def _get_session(channel_id: str, session_type: str = "photo") -> dict | None:
    dynamo = boto3.resource("dynamodb")
    table = dynamo.Table(_SESSIONS_TABLE)
    try:
        key = f"slack_{session_type}_session#{channel_id}"
        item = table.get_item(Key={"user_id": key}).get("Item")
        if not item:
            return None
        # ── Session orphan guard: discard sessions past their TTL ──
        expires_at = item.get("expires_at")
        if expires_at and int(time.time()) > int(expires_at):
            print(f"DIAG[get_session] TTL expired for {key} — purging orphan")
            _delete_session_by_key(key)
            return None
        return item
    except Exception as e:
        print(f"DynamoDB get_item failed: {e!r}")
        return None


def _delete_session(channel_id: str, session_type: str = "photo") -> None:
    _delete_session_by_key(f"slack_{session_type}_session#{channel_id}")


def _delete_session_by_key(key: str) -> None:
    try:
        boto3.resource("dynamodb").Table(_SESSIONS_TABLE).delete_item(Key={"user_id": key})
    except Exception as e:
        print(f"DynamoDB delete_item failed for {key}: {e!r}")


def _update_session(channel_id: str, session_type: str, session_data: dict) -> None:
    dynamo = boto3.resource("dynamodb")
    table = dynamo.Table(_SESSIONS_TABLE)
    key = f"slack_{session_type}_session#{channel_id}"
    session_data["user_id"] = key
    # Always refresh TTL on every update so active sessions stay alive.
    # Using setdefault here would freeze the TTL at creation time — wrong.
    session_data["expires_at"] = int(time.time()) + _SESSION_TTL_SECONDS
    table.put_item(Item=session_data)


def _get_sheet_link(row_number: int) -> str:
    return f"https://docs.google.com/spreadsheets/d/{schema.SHEET_ID}/edit#gid=0&range=A{row_number}"


# ─────────────────────────────────────────────────────────
# Sheet row helpers
# ─────────────────────────────────────────────────────────

LID_RE = re.compile(r"`(EF-[A-Z0-9-]+|BLR-[A-Z0-9-]+)`")


def _row(client: GoogleSheetsClient, lid: str) -> tuple[int | None, dict | None]:
    values = client.read_range(schema.SHEET_ID, schema.WORKSHEET_NAME, "A2:AT")
    for n, r in enumerate(values, start=2):
        if str(r[0] if r else "").strip().upper() != lid.upper():
            continue
        values_row = (
            list(r) + [""] * (schema.GRID_WIDTH - len(r))
            if len(r) < schema.GRID_WIDTH
            else list(r)[: schema.GRID_WIDTH]
        )
        return n, schema.row_to_mapping(values_row)
    return None, None


def _thread_listing(root_text: str) -> str:
    m = LID_RE.search(str(root_text or ""))
    return m.group(1) if m else ""


def _photo_files(replies: list[dict]) -> list[str]:
    files: list[str] = []
    seen: set[str] = set()
    for message in replies:
        for item in message.get("files") or []:
            fid = str(item.get("id") or "")
            url = str(
                item.get("url_private_download") or item.get("url_private") or ""
            )
            if fid and fid not in seen and url:
                seen.add(fid)
                files.append(url)
    return files


# ─────────────────────────────────────────────────────────
# Photo save
# ─────────────────────────────────────────────────────────

def _save_photos(
    slack: SlackClient, thread_ts: str, channel: str
) -> tuple[int, str]:
    print(f"DIAG[save_photos] START thread_ts={thread_ts} channel={channel}")
    replies = slack.replies(channel, thread_ts)
    print(f"DIAG[save_photos] replies_count={len(replies)}")
    lid = _thread_listing(replies[0].get("text", "") if replies else "")
    print(f"DIAG[save_photos] resolved_listing_id={lid!r}")
    if not lid:
        print("DIAG[save_photos] ABORT: no listing_id found in root message")
        return 0, "Could not identify the property from this photo thread."
    urls = _photo_files(replies)
    print(f"DIAG[save_photos] photo_urls_found={len(urls)}")
    if not urls:
        return 0, f"No photos found for `{lid}`. Nothing was changed."
    blobs = []
    for i, u in enumerate(urls):
        try:
            b = slack.download_file(u)
            blobs.append(b)
            print(f"DIAG[save_photos] downloaded photo {i+1}/{len(urls)} size={len(b)}")
        except Exception as dl_exc:
            print(f"DIAG[save_photos] DOWNLOAD FAILED for photo {i+1}: {dl_exc!r}")
    print(f"DIAG[save_photos] total_blobs={len(blobs)}")
    sheet = GoogleSheetsClient()
    row_number, row = _row(sheet, lid)
    print(f"DIAG[save_photos] sheet_row row_number={row_number} found={row is not None}")
    if not row:
        return 0, f"Listing `{lid}` was not found in Housing_Listings."
    existing = [
        x.strip()
        for x in str(row.get("cloudinary_image_urls") or "").split(",")
        if x.strip()
    ]
    print(f"DIAG[save_photos] existing_url_count={len(existing)}")
    try:
        uploads = upload_property_images(
            CloudinaryClient(), lid, blobs, start_index=len(existing) + 1
        )
        print(f"DIAG[save_photos] cloudinary_uploads={len(uploads)}")
    except Exception as up_exc:
        print(f"DIAG[save_photos] CLOUDINARY UPLOAD FAILED: {up_exc!r}")
        raise
    combined = existing + [u.url for u in uploads]
    try:
        sheet.write_range(
            schema.SHEET_ID,
            schema.WORKSHEET_NAME,
            schema.range_for("cloudinary_image_urls", "cloudinary_image_urls", row_number),
            [[", ".join(combined)]],
        )
        print(f"DIAG[save_photos] write SUCCEEDED url_count={len(combined)}")
    except Exception as write_exc:
        print(f"DIAG[save_photos] WRITE FAILED: {write_exc!r}")
        raise
    print(f"DIAG[save_photos] DONE lid={lid} uploaded={len(uploads)}")
    return len(uploads), f"Saved {len(uploads)} photo(s) for `{lid}`."


# ─────────────────────────────────────────────────────────
# Catalogue-Ready flip (shared helper, single source of truth)
# ─────────────────────────────────────────────────────────

def _maybe_flip_to_catalogue_ready(
    sheet: GoogleSheetsClient, row_number: int, row: dict
) -> bool:
    if (
        row.get("intake_status") == "Processed"
        and row.get("status") == "Pending"
        and row.get("listing_state") != "Rented Out"
        and not str(row.get("meta_catalog_id") or "").strip()
        and str(row.get("cloudinary_image_urls") or "").strip()
    ):
        sheet.write_range(
            schema.SHEET_ID,
            schema.WORKSHEET_NAME,
            schema.range_for("intake_status", "intake_status", row_number),
            [["Catalogue Ready"]],
        )
        return True
    return False


# ─────────────────────────────────────────────────────────
# Verification save
# ─────────────────────────────────────────────────────────

def _verification_fields(text: str) -> dict:
    out = {}
    for line in str(text or "").splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip()
            if k in schema.BY_NAME and k not in schema.RESERVED_COLUMNS:
                out[k] = v
    return out


def _save_verification(slack: SlackClient, thread_ts: str, channel: str) -> str:
    replies = slack.replies(channel, thread_ts)
    lid = _thread_listing(replies[0].get("text", "") if replies else "")
    if not lid:
        return "Could not identify the property from this verification thread."
    changes = {}
    for msg in replies[1:]:
        changes.update(_verification_fields(msg.get("text", "")))
    sheet = GoogleSheetsClient()
    row_number, row = _row(sheet, lid)
    if not row:
        return f"Listing `{lid}` was not found."
    candidate = dict(row)
    candidate.update(changes)
    candidate = process_phase1(str(candidate.get("raw_message_text", "")), row=candidate).row
    # Apply changes on top of the phase-1 result (user corrections win)
    candidate.update(changes)
    # Set terminal statuses BEFORE validation so validate() sees the correct values
    candidate["status"] = "Pending"
    candidate["intake_status"] = "Processed"
    from validate import validate
    errors = validate(candidate)
    if errors:
        return "Verification refused: " + "; ".join(errors)
    write_phase1_update(sheet, row_number, candidate)
    _maybe_flip_to_catalogue_ready(sheet, row_number, candidate)
    return f"Verified `{lid}`. Deterministic validation passed and the row was updated."


# ─────────────────────────────────────────────────────────
# Event deduplication (idempotency)
# ─────────────────────────────────────────────────────────

def _claim_event(event_id: str) -> bool:
    """Atomically claim an event_id.  True = first time (proceed); False = duplicate (skip)."""
    if not event_id:
        return True
    dynamo = boto3.resource("dynamodb")
    table = dynamo.Table(_SESSIONS_TABLE)
    try:
        table.update_item(
            Key={"user_id": f"slack_event_lock#{event_id}"},
            UpdateExpression="SET locked_at = :now",
            ConditionExpression="attribute_not_exists(locked_at)",
            ExpressionAttributeValues={":now": Decimal(str(time.time()))},
        )
        return True
    except Exception as e:
        if "ConditionalCheckFailedException" in repr(e):
            print(f"Event {event_id} already claimed — genuine Slack retry, ignoring.")
            return False
        print(f"_claim_event error for {event_id} (proceeding anyway): {e!r}")
        return True


# ─────────────────────────────────────────────────────────
# Local rows helper (avoids cross-module import)
# ─────────────────────────────────────────────────────────

def _rows_local(client: GoogleSheetsClient) -> list[tuple[int, dict]]:
    raw = client.read_range(schema.SHEET_ID, schema.WORKSHEET_NAME, "A2:AT")
    width = schema.GRID_WIDTH - len(schema.RESERVED_COLUMNS)
    results = []
    for i, r in enumerate(raw, start=2):
        if len(r) <= width:
            padded = list(r) + [""] * (width - len(r)) + [""] * len(schema.RESERVED_COLUMNS)
            results.append((i, schema.row_to_mapping(padded)))
    return results


# ─────────────────────────────────────────────────────────
# Main event processor (async worker path)
# ─────────────────────────────────────────────────────────

def _process_event(event: dict, context: object) -> None:
    payload = event["_slack_payload"]
    ev = payload.get("event") or {}
    if ev.get("type") != "message" or ev.get("bot_id") or ev.get("subtype"):
        return
    text = str(ev.get("text") or "").strip().casefold()
    thread_ts = str(ev.get("thread_ts") or ev.get("ts", ""))
    if not thread_ts:
        return
    slack = SlackClient()
    channel = str(ev.get("channel") or "")

    photo_session = _get_session(channel, "photo")
    catalogue_session = _get_session(channel, "catalogue")
    add_property_session = _get_session(channel, "add_property")
    catalogue_update_session = _get_session(channel, "catalogue_update")
    print(
        f"DIAG[process_event] text={text!r} channel={channel} "
        f"photo={photo_session is not None} catalogue={catalogue_session is not None} "
        f"add_property={add_property_session is not None} "
        f"catalogue_update={catalogue_update_session is not None}"
    )

    # ── Catalogue update (rented-out deletion) thread ──────────────────────
    if (
        channel == INVENTORY_CHANNEL
        and catalogue_update_session
        and thread_ts == catalogue_update_session.get("thread_ts")
    ):
        _handle_catalogue_update_thread(
            slack, channel, text, thread_ts, catalogue_update_session
        )
        return

    # ── Catalogue creation thread ──────────────────────────────────────────
    if (
        channel == INVENTORY_CHANNEL
        and catalogue_session
        and text in ("go", "skip", "exit")
        and thread_ts == catalogue_session.get("thread_ts")
    ):
        _handle_catalogue_thread(slack, channel, text, thread_ts, catalogue_session)
        return

    # ── Photo thread ───────────────────────────────────────────────────────
    if (
        channel == INVENTORY_CHANNEL
        and photo_session
        and text in ("done", "next", "skip", "exit")
        and thread_ts == photo_session.get("thread_ts")
    ):
        _handle_photo_thread(slack, channel, text, thread_ts, photo_session)
        return

    # ── Add-property: control commands ────────────────────────────────────
    if (
        channel == INVENTORY_CHANNEL
        and add_property_session
        and text in ("done", "cancel", "add more", "exit")
    ):
        phase = str(add_property_session.get("phase", "collecting"))
        thread = add_property_session.get("thread_ts", thread_ts)
        if thread != thread_ts:
            return  # message is from a different thread
        _handle_add_property_command(
            slack, channel, text, thread, phase, add_property_session
        )
        return

    # ── Add-property: free-text collection ────────────────────────────────
    if (
        channel == INVENTORY_CHANNEL
        and add_property_session
        and not text.startswith("/")
    ):
        phase = str(add_property_session.get("phase", "collecting"))
        thread = add_property_session.get("thread_ts", thread_ts)
        if thread != thread_ts:
            return
        _handle_add_property_freetext(
            slack, channel, thread, phase, add_property_session, ev
        )
        return

    # ── Verification submit ────────────────────────────────────────────────
    if channel == PROPERTY_VERIFICATION_CHANNEL and text == "submit":
        try:
            reply = _save_verification(slack, thread_ts, channel)
            slack.post_message(channel, reply, thread_ts=thread_ts)
        except Exception as verify_exc:
            print(f"Verification submission failed: {verify_exc!r}")
            slack.post_message(
                channel,
                "Something went wrong saving your verification — check your values and try again.",
                thread_ts=thread_ts,
            )


# ─────────────────────────────────────────────────────────
# Catalogue creation thread handler
# ─────────────────────────────────────────────────────────

def _handle_catalogue_thread(
    slack: SlackClient,
    channel: str,
    text: str,
    thread_ts: str,
    session: dict,
) -> None:
    try:
        if text == "exit":
            _delete_session(channel, "catalogue")
            slack.post_message(
                channel,
                "Catalogue session stopped.",
                thread_ts=session["thread_ts"],
            )
            return

        sheet = GoogleSheetsClient()
        sys.path.insert(
            0, str(__file__).rsplit("/", 1)[0] + "/modules/efps_meta_catalogue_mgmnt/src"
        )
        from generator import publish_and_assign, assign_to_collection

        pos = int(session.get("position", 0))
        queue = session.get("queue", [])

        if pos >= len(queue):
            _delete_session(channel, "catalogue")
            slack.post_message(
                channel,
                "All catalogues processed. Session closed.",
                thread_ts=session["thread_ts"],
            )
            return

        listing_id = queue[pos]
        row_number, row = _row(sheet, listing_id)

        if not row:
            slack.post_message(
                channel,
                f"⚠️ Could not find `{listing_id}` in sheet. Skipping.",
                thread_ts=session["thread_ts"],
            )
            session["position"] = pos + 1
            _update_session(channel, "catalogue", session)
            _post_catalogue_continue(slack, channel, session, pos + 1, queue)
            return

        # Already has a meta_catalog_id — skip silently
        existing_meta_id = str(row.get("meta_catalog_id", "") or "").strip()
        if existing_meta_id:
            slack.post_message(
                channel,
                f"⏭️ `{listing_id}` already has a catalogue (Product ID: `{existing_meta_id[:20]}`). Skipping.",
                thread_ts=session["thread_ts"],
            )
            session["position"] = pos + 1
            _update_session(channel, "catalogue", session)
            _post_catalogue_continue(slack, channel, session, pos + 1, queue)
            return

        # Guard: must have images
        if not str(row.get("cloudinary_image_urls", "") or "").strip():
            slack.post_message(
                channel,
                f"⚠️ `{listing_id}` has no images — cannot create catalogue. Skipping.",
                thread_ts=session["thread_ts"],
            )
            session["position"] = pos + 1
            _update_session(channel, "catalogue", session)
            _post_catalogue_continue(slack, channel, session, pos + 1, queue)
            return

        slack.post_message(
            channel,
            f"⏳ Creating catalogue for `{listing_id}`…",
            thread_ts=session["thread_ts"],
        )

        # ── Publish product and assign to collection ───────────────────────
        try:
            result, coll_ok, coll_msg = publish_and_assign(row_number, row)
        except Exception as pub_exc:
            error_msg = str(pub_exc)
            print(f"publish_and_assign failed for {listing_id}: {pub_exc!r}")
            slack.post_message(
                channel,
                f"❌ `{listing_id}` catalogue creation failed:\n```{error_msg[:300]}```",
                thread_ts=session["thread_ts"],
            )
            # Write error note to sheet
            try:
                sheet.write_range(
                    schema.SHEET_ID,
                    schema.WORKSHEET_NAME,
                    schema.range_for("error_notes", "error_notes", row_number),
                    [[f"Catalogue creation failed: {error_msg[:200]}"]],
                )
            except Exception:
                pass
            session["position"] = pos + 1
            _update_session(channel, "catalogue", session)
            _post_catalogue_continue(slack, channel, session, pos + 1, queue)
            return

        product_id = result.get("product_id", "")
        status = result.get("status", "created")

        if status == "already_exists":
            slack.post_message(
                channel,
                f"✅ `{listing_id}` already in WhatsApp — synced Product ID: `{product_id}`",
                thread_ts=session["thread_ts"],
            )
        elif status == "recovered_duplicate":
            slack.post_message(
                channel,
                f"✅ `{listing_id}` recovered from duplicate — Product ID: `{product_id}`",
                thread_ts=session["thread_ts"],
            )
        else:
            slack.post_message(
                channel,
                f"✅ `{listing_id}` catalogue created — Product ID: `{product_id}`",
                thread_ts=session["thread_ts"],
            )

        # ── Collection assignment result ───────────────────────────────────
        if coll_ok:
            slack.post_message(
                channel,
                f"✅ `{listing_id}` added to BHK collection.",
                thread_ts=session["thread_ts"],
            )
        else:
            slack.post_message(
                channel,
                f"⚠️ `{listing_id}` collection assignment failed: {coll_msg}\n"
                f"Run `/efps assign {listing_id}` later to retry.",
                thread_ts=session["thread_ts"],
            )

        session["position"] = pos + 1
        _update_session(channel, "catalogue", session)
        _post_catalogue_continue(slack, channel, session, pos + 1, queue)

    except Exception as e:
        print(f"Catalogue thread handler failed: {e!r}")
        import traceback; traceback.print_exc()
        slack.post_message(
            channel,
            "An unexpected error occurred in the catalogue workflow. Please contact support.",
            thread_ts=thread_ts,
        )


def _post_catalogue_continue(
    slack: SlackClient,
    channel: str,
    session: dict,
    next_pos: int,
    queue: list,
) -> None:
    remaining = len(queue) - next_pos
    if remaining > 0:
        slack.post_message(
            channel,
            f"{remaining} propert{'y' if remaining == 1 else 'ies'} remaining. Reply `go` to continue, `exit` to stop.",
            thread_ts=session["thread_ts"],
        )
    else:
        _delete_session(channel, "catalogue")
        slack.post_message(
            channel,
            "✅ All catalogues done. Session closed.",
            thread_ts=session["thread_ts"],
        )


# ─────────────────────────────────────────────────────────
# Catalogue update (rented-out deletion) thread handler
# ─────────────────────────────────────────────────────────

def _handle_catalogue_update_thread(
    slack: SlackClient,
    channel: str,
    text: str,
    thread_ts: str,
    session: dict,
) -> None:
    """Handle confirmation replies for /efps catalogue update delete flow."""
    try:
        phase = str(session.get("phase", "awaiting_confirm"))

        if text in ("exit", "cancel", "no"):
            _delete_session(channel, "catalogue_update")
            slack.post_message(
                channel,
                "Catalogue update cancelled. No catalogues were deleted.",
                thread_ts=session["thread_ts"],
            )
            return

        if text == "yes" and phase == "awaiting_confirm":
            queue = session.get("queue", [])  # list of {listing_id, product_id}
            if not queue:
                _delete_session(channel, "catalogue_update")
                slack.post_message(
                    channel,
                    "Nothing to delete — session was empty.",
                    thread_ts=session["thread_ts"],
                )
                return

            sys.path.insert(
                0, str(__file__).rsplit("/", 1)[0] + "/modules/efps_meta_catalogue_mgmnt/src"
            )

            slack.post_message(
                channel,
                f"🗑️ Starting deletion of {len(queue)} catalogue(s)…",
                thread_ts=session["thread_ts"],
            )

            from shared.whatsapp_whapi.client import WhApiClient
            whapi = WhApiClient()
            sheet = GoogleSheetsClient()

            succeeded = []
            failed = []

            for entry in queue:
                listing_id = entry.get("listing_id", "?")
                product_id = entry.get("product_id", "")

                if not product_id:
                    failed.append(f"`{listing_id}` — no product ID recorded")
                    continue

                try:
                    # Delete product from WhatsApp Business catalogue
                    whapi.post(
                        f"/business/products/{product_id}",
                        {"_method": "DELETE"},
                    )
                    # Try proper DELETE endpoint — WhAPI may use DELETE verb
                    # If the above fails, we fall through to the except block
                except Exception:
                    # Try via DELETE verb on client
                    try:
                        whapi._request("DELETE", f"/business/products/{product_id}")
                    except Exception as del_exc:
                        failed.append(f"`{listing_id}` — API error: {str(del_exc)[:80]}")
                        print(f"DIAG[catalogue_update] delete failed for {listing_id}/{product_id}: {del_exc!r}")
                        continue

                # Clear meta fields from sheet
                try:
                    row_number, _ = _row(sheet, listing_id)
                    if row_number:
                        sheet.write_range(
                            schema.SHEET_ID,
                            schema.WORKSHEET_NAME,
                            schema.range_for("meta_catalog_id", "meta_catalog_status", row_number),
                            [["", ""]],
                        )
                        sheet.write_range(
                            schema.SHEET_ID,
                            schema.WORKSHEET_NAME,
                            schema.range_for("intake_status", "intake_status", row_number),
                            [["Rented Out"]],
                        )
                except Exception as sheet_exc:
                    print(f"DIAG[catalogue_update] sheet clear failed for {listing_id}: {sheet_exc!r}")
                    # Still count as succeeded for WhatsApp — sheet update is secondary

                succeeded.append(f"`{listing_id}`")

            # Build result summary
            lines = []
            if succeeded:
                lines.append(f"✅ Deleted {len(succeeded)} catalogue(s): {', '.join(succeeded)}")
            if failed:
                lines.append(f"❌ Failed {len(failed)}:")
                lines.extend(f"  • {f}" for f in failed)

            _delete_session(channel, "catalogue_update")
            slack.post_message(
                channel,
                "\n".join(lines) + "\n\nSession closed.",
                thread_ts=session["thread_ts"],
            )
        else:
            # Any other text — remind user what to reply
            slack.post_message(
                channel,
                "Reply `yes` to confirm deletion, or `no`/`exit` to cancel.",
                thread_ts=session["thread_ts"],
            )
    except Exception as e:
        print(f"Catalogue update thread handler failed: {e!r}")
        import traceback; traceback.print_exc()
        _delete_session(channel, "catalogue_update")
        slack.post_message(
            channel,
            f"An unexpected error occurred during catalogue update: {str(e)[:200]}",
            thread_ts=thread_ts,
        )


# ─────────────────────────────────────────────────────────
# Photo thread handler
# ─────────────────────────────────────────────────────────

def _handle_photo_thread(
    slack: SlackClient,
    channel: str,
    text: str,
    thread_ts: str,
    session: dict,
) -> None:
    try:
        if text == "exit":
            _delete_session(channel, "photo")
            slack.post_message(
                channel,
                "Stopped. Come back any time with `/efps photos start`.",
                thread_ts=session["thread_ts"],
            )
            return

        if text == "done":
            slack.post_message(
                channel,
                f"Saving photos for `{session['listing_id']}`…\n"
                "• Reading attachments from the thread.\n"
                "• Uploading to Cloudinary and writing URLs to the sheet.\n"
                "• I will confirm here in a moment.",
                thread_ts=session["thread_ts"],
            )
            uploaded_count, reply = _save_photos(
                slack, session["thread_ts"], channel
            )
            print(f"DIAG[photo_thread] _save_photos → count={uploaded_count} reply={reply!r}")

            sheet = GoogleSheetsClient()
            row_number, row = _row(sheet, session["listing_id"])
            sheet_link = _get_sheet_link(row_number) if row_number else ""

            # Auto-flip after photos saved
            if row:
                flipped = _maybe_flip_to_catalogue_ready(sheet, row_number, row)
                if flipped:
                    print(
                        f"DIAG[photo_thread] flipped {session['listing_id']} → Catalogue Ready"
                    )

            confirmation = (
                f"Saved — `{session['listing_id']}`\n"
                f"• {uploaded_count} photo(s) uploaded to Cloudinary.\n"
                f"• URLs written to the sheet."
            )
            if sheet_link:
                confirmation += f" <{sheet_link}|Open row>"
            slack.post_message(channel, confirmation, thread_ts=session["thread_ts"])

            # Refresh queue for follow-up count
            new_queue = [
                r
                for _, r in _rows_local(GoogleSheetsClient())
                if r.get("listing_id")
                and r.get("intake_status") == "Processed"
                and not str(r.get("cloudinary_image_urls") or "").strip()
                and r.get("listing_state") != "Rented Out"
            ]
            remaining_count = len(new_queue)
            if remaining_count == 0:
                _delete_session(channel, "photo")
                slack.post_message(
                    channel,
                    "All caught up — no more properties need photos right now.",
                    thread_ts=session["thread_ts"],
                )
            else:
                slack.post_message(
                    channel,
                    f"{remaining_count} {'property' if remaining_count == 1 else 'properties'} still need photos.\n"
                    "• `next` — show the next one\n"
                    "• `exit` — stop here\n\n"
                    "_Just the word on its own — no slash._",
                    thread_ts=session["thread_ts"],
                )
            return

        if text in ("next", "skip"):
            current_lid = session.get("listing_id")
            try:
                current_index = session["queue"].index(current_lid)
                next_index = current_index + 1
            except (ValueError, KeyError):
                next_index = 0

            if next_index >= len(session.get("queue", [])):
                _delete_session(channel, "photo")
                slack.post_message(
                    channel,
                    "All caught up — no more properties need photos right now.",
                    thread_ts=session["thread_ts"],
                )
                return

            next_lid = session["queue"][next_index]
            all_rows = _rows_local(GoogleSheetsClient())
            next_prop = next(
                (r for _, r in all_rows if r.get("listing_id") == next_lid), None
            )
            if not next_prop:
                slack.post_message(
                    channel,
                    "Could not find the next property — it may have been updated. "
                    "Please run `/efps photos start` again.",
                    thread_ts=session["thread_ts"],
                )
                _delete_session(channel, "photo")
                return

            position = session.get("queue_position", 0) + 1
            msg_text = (
                f"*Photos needed — {position} of {session['total_in_queue']}*\n"
                f"`{next_lid}`\n"
                f"• Society: {next_prop.get('society_name') or '—'}\n"
                f"• BHK: {next_prop.get('BHK') or '—'}\n"
                f"• Rent: {next_prop.get('monthly_rent') or '—'}\n"
                f"• Floor: {next_prop.get('floor_number') or '—'}\n"
                f"• Locality: {next_prop.get('locality') or '—'}\n"
                f"• Furnishing: {next_prop.get('furnish_type') or '—'}\n\n"
                f"*Original message:*\n```\n{str(next_prop.get('raw_message_text',''))[:1200]}\n```\n\n"
                f"*Reply to this message with the photos.*\n"
                f"Then reply `done` to save them. (`skip` to pass, `exit` to stop.)\n\n"
                f"_Just the word on its own — no slash._"
            )
            new_ts = slack.post_message(INVENTORY_CHANNEL, msg_text)
            slack.post_message(
                channel,
                f"Showing `{next_lid}` above — reply to it with the photos.",
                thread_ts=session["thread_ts"],
            )
            session["listing_id"] = next_lid
            session["thread_ts"] = new_ts
            session["queue_position"] = position
            boto3.resource("dynamodb").Table(_SESSIONS_TABLE).put_item(Item=session)
            return

    except Exception as e:
        print(f"Photo thread handler failed: {e!r}")
        import traceback; traceback.print_exc()
        slack.post_message(
            channel,
            "An error occurred in the photo workflow. Please contact support.",
            thread_ts=thread_ts,
        )


# ─────────────────────────────────────────────────────────
# Add-property: command handler
# ─────────────────────────────────────────────────────────

def _handle_add_property_command(
    slack: SlackClient,
    channel: str,
    text: str,
    thread: str,
    phase: str,
    session: dict,
) -> None:
    try:
        # ── cancel ─────────────────────────────────────────────────────────
        if text == "cancel":
            if phase in ("awaiting_photos", "completed"):
                slack.post_message(
                    channel,
                    "Row already added. Use `done` to continue or `exit` to close.",
                    thread_ts=thread,
                )
            else:
                _delete_session(channel, "add_property")
                slack.post_message(
                    channel,
                    "Property entry cancelled. Session closed.",
                    thread_ts=thread,
                )
            return

        # ── done (collecting) ───────────────────────────────────────────────
        if text == "done" and phase == "collecting":
            messages = json.loads(session.get("messages_json", "[]"))
            if not messages:
                slack.post_message(
                    channel,
                    "No property details provided yet. Send details first, or `cancel` to discard.",
                    thread_ts=thread,
                )
                return

            raw_text = "\n".join(messages)
            slack.post_message(channel, "Processing property details…", thread_ts=thread)

            try:
                sheet = GoogleSheetsClient()
                from pipeline import process_closed_session, next_listing_id, initial_row

                listing_id = next_listing_id(sheet)

                # ── Double-write guard (DynamoDB atomic claim) ─────────────────────
                # Two concurrent Lambda invocations (e.g. Slack retry) can both read
                # the same sheet state and derive the same listing_id. Claim it in
                # DynamoDB with a conditional write so only one invocation wins.
                lock_table = boto3.resource("dynamodb").Table(_SESSIONS_TABLE)
                lock_key = f"add_property_lock#{listing_id}"
                try:
                    lock_table.put_item(
                        Item={
                            "user_id": lock_key,
                            "locked_at": str(time.time()),
                            "expires_at": int(time.time()) + 300,
                        },
                        ConditionExpression="attribute_not_exists(user_id)",
                    )
                    print(f"DIAG[add_property] claimed lock for {listing_id}")
                except Exception as lock_exc:
                    if "ConditionalCheckFailedException" in repr(lock_exc):
                        print(
                            f"DIAG[add_property] listing_id {listing_id} already claimed — "
                            "duplicate invocation, aborting"
                        )
                        slack.post_message(
                            channel,
                            f"⚠️ Row `{listing_id}` is already being processed. "
                            "This appears to be a duplicate — no action taken.",
                            thread_ts=thread,
                        )
                        return
                    # Non-lock DynamoDB error — log but continue (lock is best-effort)
                    print(f"DIAG[add_property] DynamoDB lock error (continuing): {lock_exc!r}")

                ist = timezone(timedelta(hours=5, minutes=30))
                onboarded_on = datetime.now(ist).strftime("%-d %b %Y, %-I:%M %p")

                initial = initial_row(listing_id, raw_text, onboarded_on)
                out, issues = process_closed_session(raw_text, row=initial)

                sheet.insert_rows(
                    schema.SHEET_ID,
                    schema.WORKSHEET_NAME,
                    [schema.mapping_to_row(out)],
                )

                status = out.get("status", "")
                issue_lines = ""
                if issues:
                    issue_lines = "\n".join(f"  • {i}" for i in issues[:5])
                    issue_lines = f"\n⚠️ Review flags:\n{issue_lines}"

                slack.post_message(
                    channel,
                    f"✅ Property row added: `{listing_id}` (Status: {status}){issue_lines}\n\n"
                    "Now attach photos in this thread, then reply `done`.\n"
                    "Reply `done` now to skip photos.",
                    thread_ts=thread,
                )

                session["phase"] = "awaiting_photos"
                session["listing_id"] = listing_id
                _update_session(channel, "add_property", session)

            except Exception as process_exc:
                print(f"add-property processing failed: {process_exc!r}")
                import traceback; traceback.print_exc()
                slack.post_message(
                    channel,
                    f"❌ Processing failed: {str(process_exc)[:300]}",
                    thread_ts=thread,
                )
                _delete_session(channel, "add_property")
            return

        # ── done (awaiting_photos) ─────────────────────────────────────────
        if text == "done" and phase == "awaiting_photos":
            listing_id = session.get("listing_id", "")
            replies = slack.replies(channel, thread)
            photo_urls = _photo_files(replies)
            uploaded_count = 0

            if photo_urls:
                slack.post_message(
                    channel,
                    f"Processing {len(photo_urls)} image(s)…",
                    thread_ts=thread,
                )
                blobs = []
                for u in photo_urls:
                    try:
                        blobs.append(slack.download_file(u))
                    except Exception as dl_exc:
                        print(f"DIAG[add_property] photo download failed: {dl_exc!r}")
                if blobs:
                    try:
                        sheet = GoogleSheetsClient()
                        uploads = upload_property_images(
                            CloudinaryClient(), listing_id, blobs
                        )
                        uploaded_count = len(uploads)
                        row_number, row = _row(sheet, listing_id)
                        if row:
                            existing = [
                                x.strip()
                                for x in str(row.get("cloudinary_image_urls") or "").split(",")
                                if x.strip()
                            ]
                            combined = existing + [u.url for u in uploads]
                            sheet.write_range(
                                schema.SHEET_ID,
                                schema.WORKSHEET_NAME,
                                schema.range_for(
                                    "cloudinary_image_urls",
                                    "cloudinary_image_urls",
                                    row_number,
                                ),
                                [[", ".join(combined)]],
                            )
                            _maybe_flip_to_catalogue_ready(
                                sheet,
                                row_number,
                                {**row, "cloudinary_image_urls": ", ".join(combined)},
                            )
                    except Exception as up_exc:
                        slack.post_message(
                            channel,
                            f"❌ Photo upload failed: {str(up_exc)[:200]}",
                            thread_ts=thread,
                        )

            if uploaded_count > 0:
                slack.post_message(
                    channel,
                    f"✅ {uploaded_count} photo(s) uploaded for `{listing_id}`.",
                    thread_ts=thread,
                )
            else:
                slack.post_message(
                    channel, "No photos found — skipping.", thread_ts=thread
                )

            session["phase"] = "completed"
            _update_session(channel, "add_property", session)
            slack.post_message(
                channel,
                "─────────────────────────────\n"
                "Reply `add more` for next property  |  `exit` to close",
                thread_ts=thread,
            )
            return

        # ── done (completed) ───────────────────────────────────────────────
        if text == "done" and phase == "completed":
            slack.post_message(
                channel,
                "Already done. Reply `add more` or `exit`.",
                thread_ts=thread,
            )
            return

        # ── exit ───────────────────────────────────────────────────────────
        if text == "exit":
            if phase == "completed":
                _delete_session(channel, "add_property")
                slack.post_message(channel, "Session closed.", thread_ts=thread)
            elif phase == "awaiting_photos":
                _delete_session(channel, "add_property")
                slack.post_message(
                    channel,
                    f"Photos skipped. Session closed. "
                    f"Property `{session.get('listing_id', '')}` is saved.",
                    thread_ts=thread,
                )
            else:
                slack.post_message(
                    channel,
                    "Use `cancel` to discard, or `done` to process.",
                    thread_ts=thread,
                )
            return

        # ── add more ───────────────────────────────────────────────────────
        if text == "add more":
            if phase == "completed":
                _delete_session(channel, "add_property")
                ts = slack.post_message(
                    INVENTORY_CHANNEL,
                    "📝 New Property Entry Session\n\n"
                    "Share property details in THIS THREAD:\n"
                    "• One message or multiple — all will be captured\n"
                    "• Reply `done` when finished\n\n"
                    "Commands: `done` | `cancel`",
                )
                new_session = {
                    "thread_ts": ts,
                    "messages_json": "[]",
                    "listing_id": "",
                    "phase": "collecting",
                    "expires_at": int(time.time()) + _SESSION_TTL_SECONDS,
                }
                _update_session(channel, "add_property", new_session)
            else:
                slack.post_message(
                    channel,
                    "Finish the current property first. `done` or `cancel`.",
                    thread_ts=thread,
                )
            return

    except Exception as e:
        print(f"Add-property command handler failed: {e!r}")
        import traceback; traceback.print_exc()
        slack.post_message(
            channel,
            f"An error occurred: {str(e)[:200]}\nPlease contact support.",
            thread_ts=thread,
        )


# ─────────────────────────────────────────────────────────
# Add-property: free-text collection handler
# ─────────────────────────────────────────────────────────

def _handle_add_property_freetext(
    slack: SlackClient,
    channel: str,
    thread: str,
    phase: str,
    session: dict,
    ev: dict,
) -> None:
    if phase == "collecting":
        msg_text = str(ev.get("text", "")).strip()
        if msg_text:
            messages = json.loads(session.get("messages_json", "[]"))
            messages.append(msg_text)
            session["messages_json"] = json.dumps(messages)
            _update_session(channel, "add_property", session)
            slack.post_message(
                channel,
                f"✓ Message {len(messages)} captured. Send more or reply `done` to process.",
                thread_ts=thread,
            )
    elif phase == "awaiting_photos":
        files = ev.get("files", [])
        if files:
            slack.post_message(
                channel,
                f"✓ {len(files)} image(s) received. Attach more or reply `done` to process.",
                thread_ts=thread,
            )


# ─────────────────────────────────────────────────────────
# Lambda handler
# ─────────────────────────────────────────────────────────

def lambda_handler(event: dict, context: object) -> dict:
    # Async self-invocation path — the slow worker
    if isinstance(event, dict) and event.get("_async_worker"):
        _process_event(event, context)
        return {"statusCode": 200, "body": ""}

    # Fast path — Slack/API Gateway webhook; must return within 3 s
    headers = {
        str(k).lower(): str(v)
        for k, v in (event.get("headers") or {}).items()
    }
    body = event.get("body") or "{}"
    raw = body.encode()
    if event.get("isBase64Encoded"):
        import base64
        raw = base64.b64decode(body)
        body = raw.decode()
    payload = json.loads(body)
    print(
        f"DIAG event_id={payload.get('event_id')} "
        f"retry_num={headers.get('x-slack-retry-num')} "
        f"retry_reason={headers.get('x-slack-retry-reason')} "
        f"type={payload.get('type')} "
        f"event_type={(payload.get('event') or {}).get('type')} "
        f"ts={(payload.get('event') or {}).get('ts')} "
        f"thread_ts={(payload.get('event') or {}).get('thread_ts')}"
    )
    if payload.get("type") == "url_verification":
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"challenge": payload.get("challenge", "")}),
        }
    if not verify_signature(
        raw,
        headers.get("x-slack-request-timestamp", ""),
        headers.get("x-slack-signature", ""),
    ):
        return {"statusCode": 401, "body": "invalid signature"}

    slack_event_id = str(payload.get("event_id") or "")
    if not _claim_event(slack_event_id):
        return {"statusCode": 200, "body": ""}

    lambda_client = boto3.client("lambda")
    lambda_client.invoke(
        FunctionName=context.invoked_function_arn,
        InvocationType="Event",
        Payload=json.dumps({"_async_worker": True, "_slack_payload": payload}),
    )
    return {"statusCode": 200, "body": ""}
