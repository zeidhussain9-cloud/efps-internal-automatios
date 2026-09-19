"""EFPS slash-command router for migrated inventory and lead surfaces."""
from __future__ import annotations
import sys
from shared.google_sheets.client import GoogleSheetsClient
from shared.google_sheets import schema
from shared.slack.routing import INVENTORY_CHANNEL, PROPERTY_VERIFICATION_CHANNEL, TOP_LEVEL_COMMAND
from shared.slack import SlackClient
sys.path.insert(0,"modules/efpd-lead-mgmnt/src")
sys.path.insert(0,"modules/efps-inventory-mgmnt/src")
from pipeline import process_phase1, write_phase1_update

HELP="""*EFPS commands*
`/efps status` — inventory counts
`/efps show <listing_id>` — show one property
`/efps add-property` — add new property with details + images in one session
`/efps photos start` — show next Processed property without photos
`/efps catalogue start` — create Meta catalogues for ready properties
`/efps verify start` — show next Needs Review property
`/efps help` — this help
"""

def _rows(client):
    raw=client.read_range(schema.SHEET_ID,schema.WORKSHEET_NAME,"A2:AT")
    width=schema.GRID_WIDTH-len(schema.RESERVED_COLUMNS)
    results=[]
    for i,r in enumerate(raw,start=2):
        if len(r) <= width:
            padded=list(r)+[""]*(width-len(r))+[""]*len(schema.RESERVED_COLUMNS)
            results.append((i, schema.row_to_mapping(padded)))
    return results

def handle(text:str,user_id:str,channel_id:str)->dict:
    args=text.strip().split(None,2); cmd=args[0].lower() if args else "help"
    client=GoogleSheetsClient(); slack=SlackClient()
    if cmd in {"help",""}: return {"response_type":"ephemeral","text":HELP}
    rows=_rows(client)
    if cmd=="status":
        raw=sum(r.get("intake_status")=="Raw" for _,r in rows); processed=sum(r.get("intake_status")=="Processed" for _,r in rows); review=sum(r.get("status")=="Needs Review" for _,r in rows)
        return {"response_type":"in_channel","text":f"*Inventory status*\n• Raw: {raw}\n• Processed: {processed}\n• Needs Review: {review}\n• Total: {len(rows)}"}
    if cmd=="show" and len(args)>=2:
        lid=args[1].strip().upper(); row=next((r for _,r in rows if str(r.get("listing_id","" )).strip().upper()==lid),None)
        if not row:return {"response_type":"ephemeral","text":f"No listing `{lid}` found."}
        fields=[("BHK","BHK"),("Rent","monthly_rent"),("Locality","locality"),("Society","society_name"),("Type","internal_property_type"),("Furnishing","furnish_type")]
        return {"response_type":"ephemeral","text":"\n".join([f"*`{lid}`*"]+[f"• {k}: {row.get(v) or '—'}" for k,v in fields])}
    if cmd=="photos" and len(args)>=2 and args[1].lower()=="start":
        import boto3
        dynamo = boto3.resource("dynamodb")
        table = dynamo.Table("efps-sessions")

        queue=[r for _,r in rows if r.get("listing_id") and r.get("intake_status")=="Processed" and not str(r.get("cloudinary_image_urls") or "").strip() and r.get("listing_state")!="Rented Out"]
        if not queue:
            table.delete_item(Key={"user_id": f"slack_photo_session#{channel_id}"})
            return {"response_type":"ephemeral","text":"All caught up — no more properties need photos right now."}

        total_count = len(queue)
        current_prop = queue[0]
        listing_id = current_prop['listing_id']

        message_text = (
            f"*Photos needed — 1 of {total_count}*\n"
            f"`{listing_id}`\n"
            f"• Society: {current_prop.get('society_name') or '—'}\n"
            f"• BHK: {current_prop.get('BHK') or '—'}\n"
            f"• Rent: {current_prop.get('monthly_rent') or '—'}\n"
            f"• Floor: {current_prop.get('floor_number') or '—'}\n"
            f"• Locality: {current_prop.get('locality') or '—'}\n"
            f"• Furnishing: {current_prop.get('furnish_type') or '—'}\n\n"
            f"*Original message:*\n```\n{str(current_prop.get('raw_message_text',''))[:1200]}\n```\n\n"
            f"*Reply to this message with the photos* — attach them right here in the thread, as many as you like, across as many replies as you like.\n"
            f"Then reply `done` in this thread to save them — just the word, no slash.\n"
            f"(`skip` to pass, `exit` to stop.)\n\n"
            f"_Just type the word on its own — no slash. Here or in the thread, both work._"
        )

        ts = slack.post_message(INVENTORY_CHANNEL, message_text)

        session_data = {
            "user_id": f"slack_photo_session#{channel_id}",
            "listing_id": listing_id,
            "thread_ts": ts,
            "queue_position": 1,
            "total_in_queue": total_count,
            "queue": [r['listing_id'] for r in queue]
        }
        table.put_item(Item=session_data)

        return {"response_type":"ephemeral","text":f"Photo task opened for `{listing_id}` in channel. Thread: {ts}"}
    if cmd=="catalogue" and len(args)>=2 and args[1].lower()=="start":
        import boto3
        dynamo = boto3.resource("dynamodb")
        table = dynamo.Table("efps-sessions")

        queue = [r for _, r in rows if (
            r.get("listing_id") and
            r.get("intake_status") == "Catalogue Ready" and
            r.get("status") == "Pending" and
            r.get("listing_state") != "Rented Out" and
            not str(r.get("meta_catalog_id") or "").strip() and
            str(r.get("cloudinary_image_urls") or "").strip()
        )]
        if not queue:
            table.delete_item(Key={"user_id": f"slack_catalogue_session#{channel_id}"})
            return {"response_type":"ephemeral","text":"All caught up — no properties ready for catalogue creation."}

        total = len(queue)
        lines = [f"*Meta Catalogue — {total} {'property' if total == 1 else 'properties'} ready*\n"]
        for i, prop in enumerate(queue[:10], 1):
            society = str(prop.get('society_name') or '').strip()
            bhk = str(prop.get('BHK') or '').strip()
            furnish = str(prop.get('furnish_type') or '').strip()
            rent_raw = prop.get('monthly_rent')
            try:
                rent_str = f"₹{int(rent_raw):,}" if rent_raw else "—"
            except (ValueError, TypeError):
                rent_str = f"₹{rent_raw}" if rent_raw else "—"
            loc = society if society else str(prop.get('locality') or '').strip()
            lines.append(f"{i}. `{prop['listing_id']}` · {loc} · {furnish} {bhk} · {rent_str}")
        if total > 10:
            lines.append(f"...and {total - 10} more")
        lines.append(f"\nReply `go` in this thread to start creating catalogues.")

        ts = slack.post_message(INVENTORY_CHANNEL, "\n".join(lines))

        session = {
            "user_id": f"slack_catalogue_session#{channel_id}",
            "thread_ts": ts,
            "queue": [r['listing_id'] for r in queue],
            "position": 0,
            "total": total,
        }
        table.put_item(Item=session)

        return {"response_type":"ephemeral","text":f"Catalogue session opened. Thread: {ts}"}
    if cmd=="verify" and len(args)>=2 and args[1].lower()=="start":
        row=next((r for _,r in rows if r.get("status")=="Needs Review" and r.get("listing_state")!="Rented Out"),None)
        if not row:return {"response_type":"ephemeral","text":"No inventory properties currently need verification."}
        blanks=[n for n in ("society_name","locality","pincode","BHK","bathrooms","total_floors","monthly_rent","security_deposit","built_up_area","floor_number","property_subtype","internal_property_type","landmark","furnish_type","preferred_tenant_type","bachelor_preference") if not str(row.get(n,"" )).strip()]
        ts=slack.post_message(PROPERTY_VERIFICATION_CHANNEL,f"*Verification needed — `{row['listing_id']}`*\nBlank fields: {', '.join(blanks) or 'none'}\n\nReply in this thread with `field=value` lines, then `submit`.\n\n```{str(row.get('raw_message_text',''))[:1200]}```")
        return {"response_type":"ephemeral","text":f"Verification opened for `{row['listing_id']}`. Thread: {ts}"}
    if cmd=="run": return {"response_type":"ephemeral","text":"Manual batch dispatch is wired through the new inventory pipeline deployment."}
    if cmd=="fix" and len(args)>=3:
        lid,rest=args[1].upper(),args[2]; parts=rest.split(None,1)
        if len(parts)!=2:return {"response_type":"ephemeral","text":"Usage: `/efps fix <listing_id> <field> <value>`"}
        field,value=parts; found=next(((n,r) for n,r in rows if str(r.get("listing_id","" )).strip().upper()==lid),None)
        if not found:return {"response_type":"ephemeral","text":f"No listing `{lid}` found."}
        row_number,row=found
        blocked={"listing_id","raw_message_text","intake_status","locality","pincode","google_maps_url","posted_url","posted_at","meta_catalog_id","meta_catalog_status",*schema.RESERVED_COLUMNS}
        if field in blocked or field not in schema.BY_NAME:return {"response_type":"ephemeral","text":f"`{field}` cannot be corrected by `/efps fix`."}
        candidate=dict(row); candidate[field]=value
        projected=process_phase1(str(candidate.get("raw_message_text","")),row=candidate).row
        projected[field]=value
        from validate import validate
        errors=validate(projected)
        if errors:return {"response_type":"ephemeral","text":"Correction refused: "+"; ".join(errors)}
        write_phase1_update(client,row_number,projected)
        return {"response_type":"in_channel","text":f"Updated `{lid}` field `{field}`."}
    if cmd=="add-property":
        import boto3, time
        dynamo=boto3.resource("dynamodb")
        table=dynamo.Table("efps-sessions")
        session_key=f"slack_add_property_session#{channel_id}"
        session_data={
            "user_id":session_key,
            "thread_ts":"",
            "raw_text":"",
            "image_count":0,
            "expires_at":int(time.time())+86400,
        }
        table.put_item(Item=session_data)
        ts=slack.post_message(INVENTORY_CHANNEL,
            "📝 Property Entry Session Started\n\n"
            "Share property details in THIS THREAD:\n\n"
            "1️⃣ Reply with property text (like WhatsApp message):\n"
            "   Example:\n"
            "   _3 BHK, Semi Furnished\n"
            "   Rent: 45K\n"
            "   Maintenance: 3K\n"
            "   Deposit: 1.5L\n"
            "   Location: Sarjapur Road\n"
            "   Pets: Allowed_\n\n"
            "2️⃣ Attach ALL images in next replies\n\n"
            "3️⃣ When done, reply: `done`\n"
            "   To cancel: `cancel`"
        )
        session_data["thread_ts"]=ts
        table.put_item(Item=session_data)
        return {"response_type":"ephemeral","text":f"Property entry session opened in {INVENTORY_CHANNEL}. Thread: {ts}"}
    return {"response_type":"ephemeral","text":f"Unknown command. Use `{TOP_LEVEL_COMMAND} help`."}
