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
sys.path.insert(0,"modules/efps-inventory-mgmnt/src")
from pipeline import write_phase1_update, process_phase1

LID_RE=re.compile(r"`(EF-[A-Z0-9-]+|BLR-[A-Z0-9-]+)`")

def _row(client,lid):
    values=client.read_range(schema.SHEET_ID,schema.WORKSHEET_NAME,"A2:AV")
    for n,r in enumerate(values,start=2):
        if len(r)==schema.GRID_WIDTH and str(r[0]).strip().upper()==lid.upper(): return n,schema.row_to_mapping(r)
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
            if k in schema.BY_NAME: out[k]=v
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
    headers={str(k).lower():str(v) for k,v in (event.get("headers") or {}).items()}
    if not verify_signature(raw,headers.get("x-slack-request-timestamp",""),headers.get("x-slack-signature","")): return {"statusCode":401,"body":"invalid signature"}
    payload=json.loads(body)
    if payload.get("type")=="url_verification": return {"statusCode":200,"body":payload.get("challenge","")}
    ev=payload.get("event") or {}
    if ev.get("type")!="message" or ev.get("bot_id") or ev.get("subtype"): return {"statusCode":200,"body":""}
    text=str(ev.get("text") or "").strip().casefold(); thread_ts=str(ev.get("thread_ts") or "")
    if not thread_ts:return {"statusCode":200,"body":""}
    slack=SlackClient(); channel=str(ev.get("channel") or "")
    try:
        if channel==INVENTORY_CHANNEL and text=="submit": reply=_save_photos(slack,thread_ts,channel); slack.post_message(channel,reply,thread_ts=thread_ts)
        elif channel==PROPERTY_VERIFICATION_CHANNEL and text=="submit": reply=_save_verification(slack,thread_ts,channel); slack.post_message(channel,reply,thread_ts=thread_ts)
    except Exception as exc:
        print(f"Slack event failed: {exc!r}")
    return {"statusCode":200,"body":""}
