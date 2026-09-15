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
`/efps run` — process Raw inventory rows
`/efps fix <listing_id> <field> <value>` — deterministic correction
`/efps photos start` — show next Processed property without photos
`/efps verify start` — show next Needs Review property
`/efps help` — this help
"""

def _rows(client):
    raw=client.read_range(schema.SHEET_ID,schema.WORKSHEET_NAME,"A2:AV")
    return [(i,schema.row_to_mapping(r)) for i,r in enumerate(raw,start=2) if len(r)==schema.GRID_WIDTH]

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
        queue=[r for _,r in rows if r.get("listing_id") and r.get("intake_status")=="Processed" and not str(r.get("cloudinary_image_urls") or "").strip() and r.get("listing_state")!="Rented Out"]
        if not queue:return {"response_type":"ephemeral","text":"No processed properties are waiting for photos."}
        row=queue[0]; raw=str(row.get("raw_message_text","")).strip(); ts=slack.post_message(INVENTORY_CHANNEL,f"*Photos needed — `{row['listing_id']}`*\n• BHK: {row.get('BHK') or '—'}\n• Rent: {row.get('monthly_rent') or '—'}\n• Locality: {row.get('locality') or '—'}\n• Furnishing: {row.get('furnish_type') or '—'}\n\nAttach photos as replies in this thread, then reply `submit`.\n\n```{raw[:1200]}```")
        return {"response_type":"ephemeral","text":f"Photo task opened for `{row['listing_id']}`. Thread: {ts}"}
    if cmd=="verify" and len(args)>=2 and args[1].lower()=="start":
        row=next((r for _,r in rows if r.get("status")=="Needs Review"),None)
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
        blocked={"listing_id","raw_message_text","intake_status","source_group","inventory_locked","locality","pincode","google_maps_url","posted_url","posted_at","meta_catalog_id","meta_catalog_status"}
        if field in blocked or field not in schema.BY_NAME:return {"response_type":"ephemeral","text":f"`{field}` cannot be corrected by `/efps fix`."}
        candidate=dict(row); candidate[field]=value
        projected=process_phase1(str(candidate.get("raw_message_text","")),row=candidate).row
        projected[field]=value
        from validate import validate
        errors=validate(projected)
        if errors:return {"response_type":"ephemeral","text":"Correction refused: "+"; ".join(errors)}
        write_phase1_update(client,row_number,projected)
        return {"response_type":"in_channel","text":f"Updated `{lid}` field `{field}`."}
    return {"response_type":"ephemeral","text":f"Unknown command. Use `{TOP_LEVEL_COMMAND} help`."}
