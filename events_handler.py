"""Slack Events API boundary for manual inventory photo/verification threads."""
from __future__ import annotations
import json
import re
import os
from decimal import Decimal
from shared.slack import SlackClient
from shared.slack.security import verify_signature
from shared.slack.routing import INVENTORY_CHANNEL, PROPERTY_VERIFICATION_CHANNEL
from shared.google_sheets.client import GoogleSheetsClient
from shared.google_sheets import schema
from shared.cloudinary.client import CloudinaryClient
from shared.cloudinary.media import upload_property_images
import sys
sys.path.insert(0, str(__file__).rsplit("/",1)[0] + "/modules/efps-inventory-mgmnt/src")
from pipeline import write_phase1_update, process_phase1
import boto3

def _get_session(channel_id, session_type="photo"):
    dynamo = boto3.resource("dynamodb")
    table = dynamo.Table("efps-sessions")
    try:
        key = f"slack_{session_type}_session#{channel_id}"
        item = table.get_item(Key={"user_id": key}).get("Item")
        return item
    except Exception as e:
        print(f"DynamoDB get_item failed: {e!r}")
        return None

def _delete_session(channel_id, session_type="photo"):
    dynamo = boto3.resource("dynamodb")
    table = dynamo.Table("efps-sessions")
    key = f"slack_{session_type}_session#{channel_id}"
    table.delete_item(Key={"user_id": key})

def _get_sheet_link(row_number):
    return f"https://docs.google.com/spreadsheets/d/{schema.SHEET_ID}/edit#gid=0&range=A{row_number}"


LID_RE=re.compile(r"`(EF-[A-Z0-9-]+|BLR-[A-Z0-9-]+)`")

def _row(client,lid):
    values=client.read_range(schema.SHEET_ID,schema.WORKSHEET_NAME,"A2:AT")
    for n,r in enumerate(values,start=2):
        if str(r[0] if r else "").strip().upper()!=lid.upper():
            continue
        values_row=list(r)+[""]*(schema.GRID_WIDTH-len(r)) if len(r)<schema.GRID_WIDTH else list(r)[:schema.GRID_WIDTH]
        return n,schema.row_to_mapping(values_row)
    return None,None

def _thread_listing(root_text):
    m=LID_RE.search(str(root_text or "")); return m.group(1) if m else ""

def _photo_files(replies):
    files=[]; seen=set()
    for message in replies:
        for item in message.get("files") or []:
            fid=str(item.get("id") or "")
            url=str(item.get("url_private_download") or item.get("url_private") or "")
            if fid and fid not in seen and url: seen.add(fid); files.append(url)
    return files

def _save_photos(slack,thread_ts,channel):
    print(f"DIAG[save_photos] START thread_ts={thread_ts} channel={channel}")
    replies=slack.replies(channel,thread_ts)
    print(f"DIAG[save_photos] replies_count={len(replies)}")
    lid=_thread_listing(replies[0].get("text","") if replies else "")
    print(f"DIAG[save_photos] resolved_listing_id={lid!r}")
    if not lid:
        print("DIAG[save_photos] ABORT: no listing_id found in root message")
        return 0, "Could not identify the property from this photo thread."
    urls=_photo_files(replies)
    print(f"DIAG[save_photos] photo_urls_found={len(urls)} urls={urls}")
    if not urls:
        print("DIAG[save_photos] ABORT: no photo urls extracted from replies")
        return 0, f"No photos found for `{lid}`. Nothing was changed."
    blobs=[]
    for i, u in enumerate(urls):
        try:
            b = slack.download_file(u)
            blobs.append(b)
            print(f"DIAG[save_photos] downloaded photo {i+1}/{len(urls)} size_bytes={len(b)}")
        except Exception as dl_exc:
            print(f"DIAG[save_photos] DOWNLOAD FAILED for photo {i+1}/{len(urls)} url={u}: {dl_exc!r}")
    print(f"DIAG[save_photos] total_blobs_downloaded={len(blobs)} of {len(urls)} urls")
    sheet=GoogleSheetsClient()
    row_number,row=_row(sheet,lid)
    print(f"DIAG[save_photos] sheet_row_lookup row_number={row_number} row_found={row is not None}")
    if not row:
        print(f"DIAG[save_photos] ABORT: listing {lid} not found in sheet")
        return 0, f"Listing `{lid}` was not found in Housing_Listings."
    existing=[x.strip() for x in str(row.get("cloudinary_image_urls") or "").split(",") if x.strip()]
    print(f"DIAG[save_photos] existing_urls_in_sheet={len(existing)}")
    try:
        uploads=upload_property_images(CloudinaryClient(),lid,blobs,start_index=len(existing)+1)
        print(f"DIAG[save_photos] cloudinary_uploads_succeeded={len(uploads)} of {len(blobs)} blobs")
    except Exception as up_exc:
        print(f"DIAG[save_photos] CLOUDINARY UPLOAD FAILED partway: {up_exc!r}")
        raise
    combined=existing+[u.url for u in uploads]
    print(f"DIAG[save_photos] combined_url_count={len(combined)} about_to_write_range")
    try:
        write_result = sheet.write_range(schema.SHEET_ID,schema.WORKSHEET_NAME,schema.range_for("cloudinary_image_urls","cloudinary_image_urls",row_number),[[", ".join(combined)]])
        print(f"DIAG[save_photos] write_range SUCCEEDED result={write_result!r}")
    except Exception as write_exc:
        print(f"DIAG[save_photos] WRITE_RANGE FAILED: {write_exc!r}")
        raise
    print(f"DIAG[save_photos] DONE lid={lid} uploaded={len(uploads)}")
    return len(uploads), f"Saved {len(uploads)} photo(s) for `{lid}`. URLs written to the same row."

def _verification_fields(text):
    out={}
    for line in str(text or "").splitlines():
        if "=" in line:
            k,v=line.split("=",1); k=k.strip(); v=v.strip()
            if k in schema.BY_NAME and k not in schema.RESERVED_COLUMNS: out[k]=v
    return out

def _save_verification(slack,thread_ts,channel):
    replies=slack.replies(channel,thread_ts); lid=_thread_listing(replies[0].get("text","") if replies else "")
    if not lid:return "Could not identify the property from this verification thread."
    changes={}
    for msg in replies[1:]: changes.update(_verification_fields(msg.get("text","")))
    row_number,row=_row(GoogleSheetsClient(),lid)
    if not row:return f"Listing `{lid}` was not found."
    candidate=dict(row); candidate.update(changes)
    candidate=process_phase1(str(candidate.get("raw_message_text","")),row=candidate).row
    from validate import validate
    errors=validate(candidate)
    if errors:return "Verification refused: " + "; ".join(errors)
    candidate["status"]="Pending"; candidate["intake_status"]="Processed"
    write_phase1_update(GoogleSheetsClient(),row_number,candidate)
    return f"Verified `{lid}`. Deterministic validation passed and the same row was updated."


def _claim_event(event_id):
    """Atomically claim an event_id using a Decimal timestamp (DynamoDB requires Decimal, not float).
    Returns True if this is the first time we've seen this event_id (caller should proceed),
    False if it was already claimed (caller should no-op — this is a Slack retry)."""
    if not event_id:
        return True
    dynamo = boto3.resource("dynamodb")
    table = dynamo.Table("efps-sessions")
    try:
        table.update_item(
            Key={"user_id": f"slack_event_lock#{event_id}"},
            UpdateExpression="SET locked_at = :now",
            ConditionExpression="attribute_not_exists(locked_at)",
            ExpressionAttributeValues={":now": Decimal(str(__import__("time").time()))},
        )
        return True
    except Exception as e:
        if "ConditionalCheckFailedException" in repr(e):
            print(f"Event {event_id} already claimed (genuine Slack retry, ignoring).")
        else:
            print(f"_claim_event FAILED for {event_id} due to a real error (NOT a duplicate) - will proceed anyway to avoid silent drops: {e!r}")
        return True


def _process_event(event, context):
    """The actual slow work: parses the Slack payload and runs the photo/verification flow.
    This is invoked asynchronously so it can take as long as it needs without Slack waiting on it."""
    payload = event["_slack_payload"]
    ev = payload.get("event") or {}
    if ev.get("type") != "message" or ev.get("bot_id") or ev.get("subtype"):
        return
    text = str(ev.get("text") or "").strip().casefold()
    thread_ts = str(ev.get("thread_ts") or ev.get("ts", ""))
    if not thread_ts:
        return
    slack = SlackClient(); channel = str(ev.get("channel") or "")

    photo_session = _get_session(channel, "photo")
    catalogue_session = _get_session(channel, "catalogue")
    print(f"DIAG[process_event] text={text!r} channel={channel} photo={photo_session is not None} catalogue={catalogue_session is not None}")

    if channel == INVENTORY_CHANNEL and text in ["go", "skip", "exit"] and catalogue_session:
        try:
            if text == "exit":
                _delete_session(channel, "catalogue")
                slack.post_message(channel, "Catalogue session stopped.", thread_ts=catalogue_session["thread_ts"])
                return

            pos = int(catalogue_session.get("position", 0))
            queue = catalogue_session.get("queue", [])

            if text == "skip":
                pos += 1

            if pos >= len(queue):
                _delete_session(channel, "catalogue")
                slack.post_message(channel, "All catalogues created. Session closed.", thread_ts=catalogue_session["thread_ts"])
                return

            listing_id = queue[pos]
            sheet = GoogleSheetsClient()
            row_number, row = _row(sheet, listing_id)

            if not row:
                slack.post_message(channel, f"Could not find `{listing_id}` in sheet. Skipping.", thread_ts=catalogue_session["thread_ts"])
                catalogue_session["position"] = pos + 1
                boto3.resource("dynamodb").Table("efps-sessions").put_item(Item=catalogue_session)
                return

            slack.post_message(channel, f"Creating catalogue for `{listing_id}`...", thread_ts=catalogue_session["thread_ts"])

            try:
                sys.path.insert(0, str(__file__).rsplit("/",1)[0] + "/modules/efps_meta_catalogue_mgmnt/src")
                from generator import publish_product
                result = publish_product(row_number, row)
                product_id = result.get("product_id", "")
                slack.post_message(channel, f"✅ `{listing_id}` → Product ID: {product_id}", thread_ts=catalogue_session["thread_ts"])
            except Exception as pub_exc:
                error_msg = str(pub_exc)
                slack.post_message(channel, f"❌ `{listing_id}` failed: {error_msg[:200]}", thread_ts=catalogue_session["thread_ts"])
                sheet.write_range(
                    schema.SHEET_ID, schema.WORKSHEET_NAME,
                    schema.range_for("error_notes", "error_notes", row_number),
                    [[f"Catalogue creation failed: {error_msg}"]]
                )

            catalogue_session["position"] = pos + 1
            boto3.resource("dynamodb").Table("efps-sessions").put_item(Item=catalogue_session)

            remaining = len(queue) - (pos + 1)
            if remaining > 0:
                slack.post_message(channel, f"{remaining} more to go. Processing next...", thread_ts=catalogue_session["thread_ts"])
            else:
                _delete_session(channel, "catalogue")
                slack.post_message(channel, "All catalogues created. Session closed.", thread_ts=catalogue_session["thread_ts"])

        except Exception as e:
            print(f"Catalogue flow failed: {e!r}")
            slack.post_message(channel, "An error occurred. Please contact support.", thread_ts=thread_ts)

    elif channel == INVENTORY_CHANNEL and text in ["done", "next", "skip", "exit"] and photo_session:
        try:
            if text == "exit":
                _delete_session(channel, "photo")
                slack.post_message(channel, "Stopped. Come back any time with `/efps photos start`.", thread_ts=photo_session["thread_ts"])

            elif text == "done":
                slack.post_message(
                    channel,
                    f"Saving photos for `{photo_session['listing_id']}`...\n"
                    f"• Reading what you attached in the thread.\n"
                    f"• Uploading to Cloudinary and writing the URLs to the sheet.\n"
                    f"• I will confirm here in a moment.",
                    thread_ts=photo_session["thread_ts"]
                )
                uploaded_count, reply = _save_photos(slack, photo_session["thread_ts"], channel)
                print(f"DIAG[process_event] _save_photos returned: uploaded_count={uploaded_count} reply={reply!r}")
                sheet = GoogleSheetsClient()
                row_number, row = _row(sheet, photo_session['listing_id'])
                sheet_link = _get_sheet_link(row_number)

                # Auto-flip to "Catalogue Ready" if qualifies
                if (row and
                    row.get("intake_status") == "Processed" and
                    row.get("status") == "Pending" and
                    row.get("listing_state") != "Rented Out" and
                    not str(row.get("meta_catalog_id") or "").strip() and
                    str(row.get("cloudinary_image_urls") or "").strip()):
                    sheet.write_range(
                        schema.SHEET_ID, schema.WORKSHEET_NAME,
                        schema.range_for("intake_status", "intake_status", row_number),
                        [["Catalogue Ready"]]
                    )
                    print(f"DIAG[process_event] flipped {photo_session['listing_id']} → Catalogue Ready")

                confirmation = (
                    f"Saved — `{photo_session['listing_id']}`\n"
                    f"• {uploaded_count} photo(s) uploaded to Cloudinary.\n"
                    f"• URLs written to the sheet. <{sheet_link}|Open this row>"
                )
                slack.post_message(channel, confirmation, thread_ts=photo_session["thread_ts"])

                new_queue = [r for _,r in _rows_local(GoogleSheetsClient()) if r.get("listing_id") and r.get("intake_status")=="Processed" and not str(r.get("cloudinary_image_urls") or "").strip() and r.get("listing_state")!="Rented Out"]
                remaining_count = len(new_queue)
                if remaining_count == 0:
                    follow_up_text = "All caught up — no more properties need photos right now."
                    _delete_session(channel, "photo")
                else:
                    follow_up_text = (
                        f"{remaining_count} properties still need photos.\n"
                        f"• `next` — show me the next one\n"
                        f"• `exit` — stop here, come back any time\n\n"
                        f"_Just type the word on its own — no slash. Here or in the thread, both work._"
                    )
                slack.post_message(channel, follow_up_text, thread_ts=photo_session["thread_ts"])

            elif text in ["next", "skip"]:
                new_queue_tuples = _rows_local(GoogleSheetsClient())
                current_lid = photo_session.get('listing_id')

                try:
                    current_index_in_session = photo_session["queue"].index(current_lid)
                    next_item_index = current_index_in_session + 1
                except (ValueError, KeyError):
                    next_item_index = 0

                if next_item_index >= len(photo_session.get("queue", [])):
                    slack.post_message(channel, "All caught up — no more properties need photos right now.", thread_ts=photo_session["thread_ts"])
                    _delete_session(channel, "photo")
                    return

                next_lid = photo_session["queue"][next_item_index]
                next_prop = next((r for _,r in new_queue_tuples if r.get("listing_id") == next_lid), None)

                if not next_prop:
                    slack.post_message(channel, "Could not find the next property. It might have been updated. Please start again with `/efps photos start`.", thread_ts=photo_session["thread_ts"])
                    _delete_session(channel, "photo")
                    return

                position = photo_session.get('queue_position', 0) + 1

                message_text = (
                    f"*Photos needed — {position} of {photo_session['total_in_queue']}*\n"
                    f"`{next_lid}`\n"
                    f"• Society: {next_prop.get('society_name') or '—'}\n"
                    f"• BHK: {next_prop.get('BHK') or '—'}\n"
                    f"• Rent: {next_prop.get('monthly_rent') or '—'}\n"
                    f"• Floor: {next_prop.get('floor_number') or '—'}\n"
                    f"• Locality: {next_prop.get('locality') or '—'}\n"
                    f"• Furnishing: {next_prop.get('furnish_type') or '—'}\n\n"
                    f"*Original message:*\n```\n{str(next_prop.get('raw_message_text',''))[:1200]}\n```\n\n"
                    f"*Reply to this message with the photos* — attach them right here in the thread.\n"
                    f"Then reply `done` in this thread to save them.\n"
                    f"(`skip` to pass, `exit` to stop.)\n\n"
                    f"_Just type the word on its own — no slash._"
                )
                new_ts = slack.post_message(INVENTORY_CHANNEL, message_text)
                slack.post_message(channel, f"Showing `{next_lid}` above — reply to it with the photos.", thread_ts=photo_session.get("thread_ts"))

                photo_session["listing_id"] = next_lid
                photo_session["thread_ts"] = new_ts
                photo_session["queue_position"] = position
                boto3.resource("dynamodb").Table("efps-sessions").put_item(Item=photo_session)

        except Exception as e:
            print(f"Photo flow command failed: {e!r}")
            slack.post_message(channel, "An error occurred in the photo workflow. Please contact support.", thread_ts=thread_ts)

    elif channel == PROPERTY_VERIFICATION_CHANNEL and text == "submit":
        try:
            reply = _save_verification(slack, thread_ts, channel)
            slack.post_message(channel, reply, thread_ts=thread_ts)
        except Exception as verify_exc:
            print(f"Verification submission failed: {verify_exc!r}")
            slack.post_message(channel, "Something went wrong saving your verification — please check your values and try again, or contact support.", thread_ts=thread_ts)


def lambda_handler(event, context):
    # --- Async self-invocation path: this is the SLOW worker run, triggered by ourselves, not by Slack/API Gateway.
    if isinstance(event, dict) and event.get("_async_worker"):
        _process_event(event, context)
        return {"statusCode": 200, "body": ""}

    # --- Fast path: this is the real Slack/API Gateway webhook call. Must return within 3 seconds.
    headers = {str(k).lower(): str(v) for k, v in (event.get("headers") or {}).items()}
    body = event.get("body") or "{}"; raw = body.encode()
    if event.get("isBase64Encoded"):
        import base64; raw = base64.b64decode(body); body = raw.decode()
    payload = json.loads(body)
    print(f"DIAG event_id={payload.get('event_id')} retry_num={headers.get('x-slack-retry-num')} retry_reason={headers.get('x-slack-retry-reason')} type={payload.get('type')} event_type={(payload.get('event') or {}).get('type')} ts={(payload.get('event') or {}).get('ts')} thread_ts={(payload.get('event') or {}).get('thread_ts')}")
    if payload.get("type") == "url_verification":
        return {"statusCode": 200, "headers": {"Content-Type": "application/json"}, "body": json.dumps({"challenge": payload.get("challenge", "")})}
    if not verify_signature(raw, headers.get("x-slack-request-timestamp", ""), headers.get("x-slack-signature", "")):
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


def _rows_local(client):
    """Local copy of commands.py's _rows(), duplicated here to avoid cross-module import."""
    raw=client.read_range(schema.SHEET_ID,schema.WORKSHEET_NAME,"A2:AT")
    width=schema.GRID_WIDTH-len(schema.RESERVED_COLUMNS)
    results=[]
    for i,r in enumerate(raw,start=2):
        if len(r) <= width:
            padded=list(r)+[""]*(width-len(r))+[""]*len(schema.RESERVED_COLUMNS)
            results.append((i, schema.row_to_mapping(padded)))
    return results
