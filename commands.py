"""Slack /efps slash command router and business logic."""
from __future__ import annotations
import json
import os
import re
import sys
import time
import boto3
from shared.slack import SlackClient
from shared.slack.routing import INVENTORY_CHANNEL
from shared.google_sheets.client import GoogleSheetsClient
from shared.google_sheets import schema

HELP = (
    "*EFPS Commands*\n"
    "\n"
    "- `/efps add-property` - start a new property entry session\n"
    "- `/efps photos start` - upload photos for the next unphoto'd property\n"
    "- `/efps catalogue start` - create WhatsApp catalogue entries for ready properties\n"
    "- `/efps catalogue update` - remove catalogue entries for rented-out properties\n"
    "- `/efps assign <listing_id>` - assign a property to its BHK collection\n"
    "- `/efps status` - show inventory pipeline stage counts\n"
    "- `/efps show <listing_id>` - show full details for one property\n"
    "- `/efps help` - show this message"
)

_SESSION_TTL_SECONDS = 86400  # 24 h
_SESSIONS_TABLE = os.environ.get("SESSIONS_TABLE_NAME", "efps-sessions")

# Valid listing ID format: EF-YYMM-XXXX or BLR-YYMM-XXXX
_LISTING_ID_RE = re.compile(r"^[A-Z]{2,4}-\d{4}-[A-Z0-9]{4}$", re.IGNORECASE)


def _validate_listing_id(lid: str) -> str | None:
    """Return the normalised listing ID, or None if invalid."""
    clean = str(lid or "").strip()
    if not clean or len(clean) > 30 or not _LISTING_ID_RE.match(clean):
        return None
    return clean.upper()


def _update_session(channel_id: str, session_type: str, session_data: dict) -> None:
    dynamo = boto3.resource("dynamodb")
    table = dynamo.Table(_SESSIONS_TABLE)
    key = f"slack_{session_type}_session#{channel_id}"
    session_data["user_id"] = key
    # Always refresh TTL — setdefault would freeze it at creation time
    session_data["expires_at"] = int(time.time()) + _SESSION_TTL_SECONDS
    table.put_item(Item=session_data)


def _rows(client: GoogleSheetsClient) -> list[tuple[int, dict]]:
    raw = client.read_range(schema.SHEET_ID, schema.WORKSHEET_NAME, "A2:AT")
    width = schema.GRID_WIDTH - len(schema.RESERVED_COLUMNS)
    results = []
    for i, r in enumerate(raw, start=2):
        if len(r) <= width:
            padded = list(r) + [""] * (width - len(r)) + [""] * len(schema.RESERVED_COLUMNS)
            results.append((i, schema.row_to_mapping(padded)))
    return results


def _row_by_listing_id(client: GoogleSheetsClient, lid: str) -> tuple[int | None, dict | None]:
    for n, r in _rows(client):
        if str(r.get("listing_id") or "").strip().upper() == lid.upper():
            return n, r
    return None, None


def _sheet_link(row_number: int) -> str:
    return f"https://docs.google.com/spreadsheets/d/{schema.SHEET_ID}/edit#gid=0&range=A{row_number}"


def handle(text: str, user_id: str, channel_id: str, *, response_url: str = "") -> str:
    """Route /efps <command> to its handler. Return the user-facing reply."""
    try:
        return _dispatch(text, user_id, channel_id, response_url=response_url)
    except Exception as e:  # noqa: BLE001
        print(f"EFPS command handler unhandled error: {e!r}")
        import traceback; traceback.print_exc()
        return f"❌ An unexpected error occurred processing your command. Please try again or contact support."


def handle_async(payload: dict) -> None:
    """Execute the slow part of a command that was deferred via async Lambda self-invoke.

    Called by commands_handler when the Lambda event contains "_efps_async".
    Posts the result back to Slack via response_url.
    """
    op = payload.get("_efps_async")
    response_url = payload.get("response_url", "")
    try:
        if op == "assign":
            result = _assign_do_work(
                payload["listing_id"],
                payload["product_id"],
                payload["bhk"],
            )
        else:
            result = f"❌ Unknown async operation: {op!r}"
    except Exception as e:  # noqa: BLE001
        print(f"handle_async error ({op}): {e!r}")
        import traceback; traceback.print_exc()
        result = f"❌ Async operation failed unexpectedly: {str(e)[:200]}"

    if response_url:
        _post_response_url(response_url, result)
    else:
        print(f"handle_async result (no response_url): {result}")


def _dispatch(text: str, user_id: str, channel_id: str, *, response_url: str = "") -> str:
    """Inner router — exceptions here are caught by handle()."""
    parts = str(text or "").strip().split()
    command = parts[0].casefold() if parts else "help"

    if command in {"help", ""}:
        return HELP

    if command == "add-property":
        return _add_property(channel_id)

    if command == "photos" and len(parts) > 1 and parts[1].casefold() == "start":
        return _photos_start(channel_id)

    if command == "catalogue":
        if len(parts) > 1:
            sub = parts[1].casefold()
            if sub == "start":
                return _catalogue_start(channel_id)
            if sub == "update":
                return _catalogue_update(channel_id)
        return "Usage: `/efps catalogue start` or `/efps catalogue update`"

    if command == "assign":
        if len(parts) < 2:
            return "Usage: `/efps assign <listing_id>`"
        return _assign(parts[1], response_url=response_url)

    if command == "status":
        return _status()

    if command == "show":
        if len(parts) < 2:
            return "Usage: `/efps show <listing_id>`"
        return _show(parts[1])

    if command == "run":
        return _run_worker()

    return f"Unknown command: `{command}`. Type `/efps help` for usage."


# ──────────────────────────────────────────────────────────────────────────────
# Command implementations
# ──────────────────────────────────────────────────────────────────────────────

def _add_property(channel_id: str) -> str:
    slack = SlackClient()
    ts = slack.post_message(
        INVENTORY_CHANNEL,
        "📝 *New Property Entry Session*\n\n"
        "Share property details in THIS THREAD:\n"
        "• One message or multiple — all will be captured\n"
        "• Reply `done` when finished\n\n"
        "Commands: `done` | `cancel`",
    )
    try:
        _update_session(INVENTORY_CHANNEL, "add_property", {
            "thread_ts": ts,
            "messages_json": "[]",
            "listing_id": "",
            "phase": "collecting",
        })
    except Exception as e:
        # Rollback: remove the orphaned thread so Slack and DynamoDB stay consistent.
        try:
            slack.call("chat.delete", {"channel": INVENTORY_CHANNEL, "ts": ts})
        except Exception:
            pass
        raise RuntimeError(f"Session record could not be created; thread was rolled back. ({e!r})")
    return "Property entry started. Check the new thread above."


def _photos_start(channel_id: str) -> str:
    slack = SlackClient()
    sheet = GoogleSheetsClient()

    queue = [
        r
        for _, r in _rows(sheet)
        if r.get("listing_id")
        and r.get("intake_status") == "Processed"
        and not str(r.get("cloudinary_image_urls") or "").strip()
        and r.get("listing_state") != "Rented Out"
    ]

    if not queue:
        return "All caught up — no properties need photos right now."

    first = queue[0]
    lid = first["listing_id"]
    msg_text = (
        f"*Photos needed — 1 of {len(queue)}*\n"
        f"`{lid}`\n"
        f"• Society: {first.get('society_name') or '—'}\n"
        f"• BHK: {first.get('BHK') or '—'}\n"
        f"• Rent: {first.get('monthly_rent') or '—'}\n"
        f"• Floor: {first.get('floor_number') or '—'}\n"
        f"• Locality: {first.get('locality') or '—'}\n"
        f"• Furnishing: {first.get('furnish_type') or '—'}\n\n"
        f"*Original message:*\n```\n{str(first.get('raw_message_text', ''))[:1200]}\n```\n\n"
        f"*Reply to this message with the photos.*\n"
        f"Then reply `done` to save them. (`skip` to pass, `exit` to stop.)\n\n"
        f"_Just the word on its own — no slash._"
    )
    thread_ts = slack.post_message(INVENTORY_CHANNEL, msg_text)

    try:
        _update_session(INVENTORY_CHANNEL, "photo", {
            "thread_ts": thread_ts,
            "listing_id": lid,
            "queue": [r["listing_id"] for r in queue],
            "queue_position": 0,
            "total_in_queue": len(queue),
        })
    except Exception as e:
        try:
            slack.call("chat.delete", {"channel": INVENTORY_CHANNEL, "ts": thread_ts})
        except Exception:
            pass
        raise RuntimeError(f"Session record could not be created; thread was rolled back. ({e!r})")
    return f"Photo session started — showing the first of {len(queue)} properties above."


def _catalogue_start(channel_id: str) -> str:
    slack = SlackClient()
    sheet = GoogleSheetsClient()

    queue = [
        r.get("listing_id")
        for _, r in _rows(sheet)
        if r.get("listing_id")
        and r.get("intake_status") == "Catalogue Ready"
        and not str(r.get("meta_catalog_id") or "").strip()
        and r.get("listing_state") != "Rented Out"
    ]

    if not queue:
        return "All caught up — no properties need catalogues right now."

    thread_ts = slack.post_message(
        INVENTORY_CHANNEL,
        f"*Catalogue Creation Session*\n\n"
        f"{len(queue)} {'property' if len(queue) == 1 else 'properties'} ready for WhatsApp catalogue.\n\n"
        f"Reply `go` to start creating catalogues.\n"
        f"Reply `exit` to cancel.",
    )

    try:
        _update_session(INVENTORY_CHANNEL, "catalogue", {
            "thread_ts": thread_ts,
            "queue": queue,
            "position": 0,
            "total": len(queue),
        })
    except Exception as e:
        try:
            slack.call("chat.delete", {"channel": INVENTORY_CHANNEL, "ts": thread_ts})
        except Exception:
            pass
        raise RuntimeError(f"Session record could not be created; thread was rolled back. ({e!r})")
    return f"Catalogue session started — {len(queue)} properties in queue."


def _catalogue_update(channel_id: str) -> str:
    """Start rented-out catalogue deletion flow."""
    slack = SlackClient()
    sheet = GoogleSheetsClient()

    candidates = [
        {
            "listing_id": r.get("listing_id"),
            "product_id": str(r.get("meta_catalog_id") or "").strip(),
        }
        for _, r in _rows(sheet)
        if r.get("listing_id")
        and r.get("listing_state") == "Rented Out"
        and str(r.get("meta_catalog_id") or "").strip()
    ]

    if not candidates:
        return "No rented-out properties with catalogues found. Nothing to delete."

    summary = "\n".join(f"  • `{c['listing_id']}`" for c in candidates)
    thread_ts = slack.post_message(
        INVENTORY_CHANNEL,
        f"*Catalogue Deletion — Rented Out Properties*\n\n"
        f"Found {len(candidates)} rented-out {'property' if len(candidates) == 1 else 'properties'} with catalogues:\n{summary}\n\n"
        f"⚠️ This will DELETE the WhatsApp Business products for these properties.\n\n"
        f"Reply `yes` to confirm deletion.\n"
        f"Reply `no` or `exit` to cancel.",
    )

    try:
        _update_session(INVENTORY_CHANNEL, "catalogue_update", {
            "thread_ts": thread_ts,
            "queue": candidates,
            "phase": "awaiting_confirm",
        })
    except Exception as e:
        try:
            slack.call("chat.delete", {"channel": INVENTORY_CHANNEL, "ts": thread_ts})
        except Exception:
            pass
        raise RuntimeError(f"Session record could not be created; thread was rolled back. ({e!r})")
    return f"Catalogue update started — {len(candidates)} properties listed above."


def _post_response_url(response_url: str, text: str) -> None:
    """POST a delayed response back to Slack via response_url."""
    from urllib import request as _req
    payload = json.dumps({"response_type": "ephemeral", "text": text}).encode("utf-8")
    req = _req.Request(
        response_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with _req.urlopen(req, timeout=10) as r:
            r.read()
    except Exception as e:  # noqa: BLE001
        print(f"⚠️  response_url POST failed: {e!r}")


def _assign(listing_id: str, *, response_url: str = "") -> str:
    """Retry collection assignment for a property that already has a meta_catalog_id.

    Slack enforces a 3-second response deadline on the original HTTP call.
    assign_to_collection() can take up to 70s (GET collections + PATCH +
    10s backoff retry).  We beat the deadline by:

      1. Doing fast validation (ID check + sheet lookup) inline — under 3s.
      2. Invoking THIS same Lambda asynchronously (Event invocation) with a
         synthetic payload that carries the pre-validated data and response_url.
      3. Returning an ack string immediately so Slack gets its 200 in time.

    The async re-invocation picks up via the "_assign_async" synthetic command,
    does the WhAPI work, then POSTs the result to response_url.

    If response_url is empty (local/test calls), fall back to synchronous.
    """
    clean = _validate_listing_id(listing_id)
    if not clean:
        return f"Invalid listing ID `{listing_id[:30]}`. Expected format: EF-YYMM-XXXX."

    sheet = GoogleSheetsClient()
    _, row = _row_by_listing_id(sheet, clean)
    if not row:
        return f"Property `{clean}` not found in Housing_Listings."

    product_id = str(row.get("meta_catalog_id") or "").strip()
    if not product_id:
        return f"`{clean}` has no WhatsApp product ID. Run `/efps catalogue start` first."

    bhk = str(row.get("BHK") or "").strip()

    if not response_url:
        # Fallback for local/test — run synchronously
        return _assign_do_work(clean, product_id, bhk)

    # Invoke this Lambda asynchronously so the WhAPI work happens outside
    # the 3-second Slack deadline window.
    self_arn = os.environ.get("AWS_LAMBDA_FUNCTION_NAME", "")
    if not self_arn:
        # No ARN available (local dev) — fall back to synchronous
        return _assign_do_work(clean, product_id, bhk)

    async_payload = json.dumps({
        "_efps_async": "assign",
        "listing_id": clean,
        "product_id": product_id,
        "bhk": bhk,
        "response_url": response_url,
    })
    try:
        boto3.client("lambda").invoke(
            FunctionName=self_arn,
            InvocationType="Event",  # fire-and-forget, returns immediately
            Payload=async_payload.encode("utf-8"),
        )
    except Exception as e:  # noqa: BLE001
        print(f"⚠️  async self-invoke failed: {e!r} — falling back to sync")
        return _assign_do_work(clean, product_id, bhk)

    return f"⏳ Assigning `{clean}` to BHK collection — result will follow shortly..."


def _assign_do_work(clean: str, product_id: str, bhk: str) -> str:
    """Run the actual WhAPI assignment call. Used by both sync and async paths."""
    _generator_path = str(__file__).rsplit("/", 1)[0] + "/modules/efps_meta_catalogue_mgmnt/src"
    if _generator_path not in sys.path:
        sys.path.insert(0, _generator_path)
    from generator import assign_to_collection  # noqa: PLC0415

    success, msg = assign_to_collection(product_id, bhk)
    if success:
        return f"✅ `{clean}` assigned to BHK collection: {msg}"
    return f"❌ `{clean}` collection assignment failed: {msg}"


def _status() -> str:
    sheet = GoogleSheetsClient()
    all_rows = _rows(sheet)

    raw_count = sum(
        1 for _, r in all_rows
        if r.get("listing_id") and r.get("intake_status") == "Raw"
        and r.get("listing_state") != "Rented Out"
    )
    processed_no_photos = sum(
        1 for _, r in all_rows
        if r.get("listing_id") and r.get("intake_status") == "Processed"
        and not str(r.get("cloudinary_image_urls") or "").strip()
        and r.get("listing_state") != "Rented Out"
    )
    catalogue_ready = sum(
        1 for _, r in all_rows
        if r.get("listing_id") and r.get("intake_status") == "Catalogue Ready"
        and not str(r.get("meta_catalog_id") or "").strip()
        and r.get("listing_state") != "Rented Out"
    )
    published = sum(
        1 for _, r in all_rows
        if r.get("listing_id") and r.get("intake_status") == "Published"
        and r.get("listing_state") != "Rented Out"
    )
    rented_out = sum(
        1 for _, r in all_rows
        if r.get("listing_id") and r.get("listing_state") == "Rented Out"
    )
    total_active = sum(
        1 for _, r in all_rows
        if r.get("listing_id") and r.get("listing_state") != "Rented Out"
    )

    return "\n".join([
        "*EFPS Inventory Pipeline Status*\n",
        f"Total Active: {total_active}",
        f"  • Raw (needs processing): {raw_count}",
        f"  • Processed (needs photos): {processed_no_photos}",
        f"  • Catalogue Ready (needs catalogue): {catalogue_ready}",
        f"  • Published: {published}",
        f"\nRented Out: {rented_out}",
    ])


def _show(listing_id: str) -> str:
    clean = _validate_listing_id(listing_id)
    if not clean:
        return f"Invalid listing ID `{listing_id[:30]}`. Expected format: EF-YYMM-XXXX."

    sheet = GoogleSheetsClient()
    row_number, row = _row_by_listing_id(sheet, clean)
    if not row:
        return f"Property `{clean}` not found in Housing_Listings."

    sheet_link = _sheet_link(row_number)
    photos = "Yes" if str(row.get("cloudinary_image_urls") or "").strip() else "No"
    catalogue = str(row.get("meta_catalog_id") or "").strip()
    catalogue_display = f"Yes (ID: `{catalogue}`)" if catalogue else "No"

    return (
        f"*Property Details: `{clean}`*\n\n"
        f"BHK: {row.get('BHK') or '—'}\n"
        f"Society: {row.get('society_name') or '—'}\n"
        f"Locality: {row.get('locality') or '—'}\n"
        f"Rent: ₹{row.get('monthly_rent') or '—'}/mo\n"
        f"Deposit: ₹{row.get('security_deposit') or '—'}\n"
        f"Furnishing: {row.get('furnish_type') or '—'}\n"
        f"Floor: {row.get('floor_number') or '—'}\n\n"
        f"*Pipeline State*\n"
        f"Listing State: {row.get('listing_state') or '—'}\n"
        f"Intake Status: {row.get('intake_status') or '—'}\n"
        f"QA Status: {row.get('status') or '—'}\n"
        f"Photos: {photos}\n"
        f"Catalogue: {catalogue_display}\n\n"
        f"<{sheet_link}|Open in Google Sheets>"
    )


def _run_worker() -> str:
    """Invoke the lead ingestion worker Lambda."""
    import os
    worker_arn = os.environ.get("LEAD_WORKER_ARN", "")
    if not worker_arn:
        return "⚠️ LEAD_WORKER_ARN environment variable not set. Cannot invoke worker."
    try:
        boto3.client("lambda").invoke(
            FunctionName=worker_arn,
            InvocationType="Event",
            Payload=json.dumps({"source": "manual_slack_trigger"}),
        )
        return "✅ Lead ingestion worker triggered. Check CloudWatch logs for progress."
    except Exception as e:  # noqa: BLE001
        return f"❌ Failed to invoke worker: {str(e)[:300]}"
