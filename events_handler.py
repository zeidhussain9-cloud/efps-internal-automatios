"""Slack Events API boundary for manual inventory photo/verification threads."""
from __future__ import annotations
import json
import re
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

def _get_session(channel_id):
    dynamo = boto3.resource("dynamodb")
    table = dynamo.Table("efps-sessions")
    try:
        item = table.get_item(Key={"user_id": f"slack_photo_session#{channel_id}"}).get("Item")
        return item
    except Exception as e:
        print(f"DynamoDB get_item failed: {e!r}")
        return None

def _delete_session(channel_id):
    dynamo = boto3.resource("dynamodb")
    table = dynamo.Table("efps-sessions")
    table.delete_item(Key={"user_id": f"slack_photo_session#{channel_id}"})

def _get_sheet_link(row_number):
    return f"https://docs.google.com/spreadsheets/d/{schema.SHEET_ID}/edit#gid=0&range=A{row_number}"


LID_RE=re.compile(r"`(EF-[A-Z0-9-]+|BLR-[A-Z0-9-]+)`")

def _row(client,lid):
    values=client.read_range(schema.SHEET_ID,schema.WORKSHEET_NAME,"A2:AT")
    width=schema.GRID_WIDTH-len(schema.RESERVED_COLUMNS)
    for n,r in enumerate(values,start=2):
        values_row=list(r)+[""]*len(schema.RESERVED_COLUMNS) if len(r)==width else r
        if len(values_row)==schema.GRID_WIDTH and str(values_row[0]).strip().upper()==lid.upper():
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
    replies=slack.replies(channel,thread_ts); lid=_thread_listing(replies[0].get("text","") if replies else "")
    if not lid: return "Could not identify the property from this photo thread."
    urls=_photo_files(replies)
    if not urls: return f"No photos found for `{lid}`. Nothing was changed."
    blobs=[slack.download_file(u) for u in urls]
    sheet=GoogleSheetsClient(); row_number,row=_row(sheet,lid)
    if not row: return f"Listing `{lid}` was not found in Housing_Listings."
    existing=[x.strip() for x in str(row.get("cloudinary_image_urls") or "").split(",") if x.strip()]
    uploads=upload_property_images(CloudinaryClient(),lid,blobs,start_index=len(existing)+1)
    combined=existing+[u.url for u in uploads]
    sheet.write_range(schema.SHEET_ID,schema.WORKSHEET_NAME,schema.range_for("cloudinary_image_urls","cloudinary_image_urls",row_number),[[", ".join(combined)]])
    return f"Saved {len(uploads)} photo(s) for `{lid}`. URLs written to the same row."

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

def lambda_handler(event,context):
    body=event.get("body") or "{}"; raw=body.encode()
    if event.get("isBase64Encoded"):
        import base64; raw=base64.b64decode(body); body=raw.decode()
    payload=json.loads(body)
    if payload.get("type")=="url_verification":
        return {"statusCode":200,"headers":{"Content-Type":"application/json"},"body":json.dumps({"challenge":payload.get("challenge","")})}
    headers={str(k).lower():str(v) for k,v in (event.get("headers") or {}).items()}
    if not verify_signature(raw,headers.get("x-slack-request-timestamp",""),headers.get("x-slack-signature","")): return {"statusCode":401,"body":"invalid signature"}
    ev=payload.get("event") or {}
    if ev.get("type")!="message" or ev.get("bot_id") or ev.get("subtype"): return {"statusCode":200,"body":""}
    text=str(ev.get("text") or "").strip().casefold(); thread_ts=str(ev.get("thread_ts") or "")
    if not thread_ts:return {"statusCode":200,"body":""}
    slack=SlackClient(); channel=str(ev.get("channel") or "")
    text = str(ev.get("text") or "").strip().casefold()
    thread_ts = str(ev.get("thread_ts") or ev.get("ts", ""))

    session = _get_session(channel)

    # --- Photo Flow Commands ---
    if channel == INVENTORY_CHANNEL and text in ["done", "next", "skip", "exit"]:
        try:
            if not session:
                slack.post_message(channel, "No active photo session. Start one with `/efps photos start`.", thread_ts=thread_ts)
                return {"statusCode": 200, "body": ""}

            if text == "exit":
                _delete_session(channel)
                slack.post_message(channel, "Stopped. Come back any time with `/efps photos start`.", thread_ts=session["thread_ts"])

            elif text == "done":
                slack.post_message(channel, f"Saving photos for `{session['listing_id']}`...\\n• Reading what you attached in the thread.\\n• Uploading to Cloudinary and writing the URLs to the sheet.\\n• I will confirm here in a moment.", thread_ts=session["thread_ts"])
                reply = _save_photos(slack, session["thread_ts"], channel)
                row_number, _ = _row(GoogleSheetsClient(), session['listing_id'])
                sheet_link = _get_sheet_link(row_number)
                
                confirmation = f"Saved — `{session['listing_id']}`\\n• {len((reply.split('photo(s)')[0]).split())} photos uploaded to Cloudinary.\\n• URLs written to the sheet. <{sheet_link}|Open this row>"
                slack.post_message(channel, confirmation, thread_ts=session["thread_ts"])

                # Follow-up with next step
                new_queue = [r for _,r in _rows(GoogleSheetsClient()) if r.get("listing_id") and r.get("intake_status")=="Processed" and not str(r.get("cloudinary_image_urls") or "").strip() and r.get("listing_state")!="Rented Out"]
                remaining_count = len(new_queue)
                if remaining_count == 0:
                    follow_up_text = "All caught up — no more properties need photos right now."
                    _delete_session(channel)
                else:
                    follow_up_text = f"{remaining_count} properties still need photos.\\n• `next` — show me the next one\\n• `exit` — stop here, come back any time\\n\\n_Just type the word on its own — no slash. Here or in the thread, both work._"
                slack.post_message(channel, follow_up_text, thread_ts=session["thread_ts"])


            elif text in ["next", "skip"]:
                new_queue_tuples = _rows(GoogleSheetsClient())
                full_queue = [r for _, r in new_queue_tuples if r.get("listing_id") and r.get("intake_status")=="Processed" and not str(r.get("cloudinary_image_urls") or "").strip() and r.get("listing_state")!="Rented Out"]
                
                current_lid = session.get('listing_id')
                
                # Find the index of the current item in the original session queue
                try:
                    current_index_in_session = session["queue"].index(current_lid)
                    next_item_index = current_index_in_session + 1
                except (ValueError, KeyError):
                    next_item_index = 0

                if next_item_index >= len(session.get("queue", [])):
                     slack.post_message(channel, "All caught up — no more properties need photos right now.", thread_ts=session["thread_ts"])
                     _delete_session(channel)
                     return {"statusCode": 200, "body": ""}

                next_lid = session["queue"][next_item_index]
                next_prop = next((r for _,r in new_queue_tuples if r.get("listing_id") == next_lid), None)

                if not next_prop:
                    slack.post_message(channel, "Could not find the next property. It might have been updated. Please start again with `/efps photos start`.", thread_ts=session["thread_ts"])
                    _delete_session(channel)
                    return {"statusCode": 200, "body": ""}

                position = session.get('queue_position', 0) + 1
                
                message_text = (f"*Photos needed — {position} of {session['total_in_queue']}*\\n"
                                f"`{next_lid}`\\n"
                                f"• Society: {next_prop.get('society_name') or '—'}\\n"
                                f"• BHK: {next_prop.get('BHK') or '—'}\\n"
                                f"• Rent: {next_prop.get('monthly_rent') or '—'}\\n"
                                f"• Floor: {next_prop.get('floor_number') or '—'}\\n"
                                f"• Locality: {next_prop.get('locality') or '—'}\\n"
                                f"• Furnishing: {next_prop.get('furnish_type') or '—'}\\n\\n"
                                f"*Original message:*\\n"
                                f"```{str(next_prop.get('raw_message_text',''))[:1200]}```\\n\\n"
                                f"*Reply to this message with the photos* — attach them right here in the thread.\\n"
                                f"Then reply `done` in this thread to save them.\\n"
                                f"(`skip` to pass, `exit` to stop.)\\n\\n"
                                f"_Just type the word on its own — no slash._")
                new_ts = slack.post_message(INVENTORY_CHANNEL, message_text)
                slack.post_message(channel, f"Showing `{next_lid}` above — reply to it with the photos.", thread_ts=session.get("thread_ts"))

                session["listing_id"] = next_lid
                session["thread_ts"] = new_ts
                session["queue_position"] = position
                boto3.resource("dynamodb").Table("efps-sessions").put_item(Item=session)

        except Exception as e:
            print(f"Photo flow command failed: {e!r}")
            slack.post_message(channel, "An error occurred in the photo workflow. Please contact support.", thread_ts=thread_ts)

    # --- Verification Flow (unchanged) ---
    elif channel==PROPERTY_VERIFICATION_CHANNEL and text=="submit":
        try:
            reply=_save_verification(slack,thread_ts,channel)
            slack.post_message(channel,reply,thread_ts=thread_ts)
        except Exception as verify_exc:
            print(f"Verification submission failed: {verify_exc!r}")
            slack.post_message(channel,"Something went wrong saving your verification — please check your values and try again, or contact support.",thread_ts=thread_ts)
    return {"statusCode":200,"body":""}
