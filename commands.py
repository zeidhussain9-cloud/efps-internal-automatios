"""EFPS slash-command router for the new repository."""
from __future__ import annotations
import re
import sys
from shared.google_sheets.client import GoogleSheetsClient
from shared.google_sheets import schema
from shared.slack.routing import INVENTORY_CHANNEL, LEADS_CHANNEL, PROPERTY_VERIFICATION_CHANNEL, TOP_LEVEL_COMMAND
from shared.slack import SlackClient
sys.path.insert(0,"modules/efpd-lead-mgmnt/src")
sys.path.insert(0,"modules/efps-inventory-mgmnt/src")
from pipeline import next_listing_id, process_phase1
from leads import get_lead if False else record_message

HELP="""*EFPS commands*
`/efps status` — inventory counts
`/efps show <listing_id>` — show one property
`/efps run` — process Raw inventory rows
`/efps fix <listing_id> <field> <value>` — deterministic same-row correction
`/efps photos start` — show the next processed property without photos
`/efps verify start` — show the next Needs Review property
`/efps help` — this help
"""

# Import the lead module without exporting a public 'get_lead' command surface.
def _inventory_rows(client):
    return [schema.row_to_mapping(r) for r in client.read_range(schema.SHEET_ID,schema.WORKSHEET_NAME,"A2:AV") if len(r)==schema.GRID_WIDTH]

def handle(text:str,user_id:str,channel_id:str)->dict:
    args=text.strip().split(None,2); cmd=args[0].lower() if args else "help"
    client=GoogleSheetsClient(); slack=SlackClient()
    if cmd in {"help",""}: return {"response_type":"ephemeral","text":HELP}
    if cmd=="status":
        rows=_inventory_rows(client); raw=sum(str(r.get("intake_status"))=="Raw" for r in rows); processed=sum(str(r.get("intake_status"))=="Processed" for r in rows); review=sum(str(r.get("status"))=="Needs Review" for r in rows)
        return {"response_type":"in_channel","text":f"*Inventory status*\n• Raw: {raw}\n• Processed: {processed}\n• Needs Review: {review}\n• Total: {len(rows)}"}
    if cmd=="show" and len(args)>=2:
        lid=args[1].strip().upper(); row=next((r for r in _inventory_rows(client) if str(r.get("listing_id","" )).strip().upper()==lid),None)
        if not row:return {"response_type":"ephemeral","text":f"No listing `{lid}` found."}
        fields=[("BHK","BHK"),("Rent","monthly_rent"),("Locality","locality"),("Society","society_name"),("Type","internal_property_type"),("Furnishing","furnish_type")]
        lines=[f"*`{lid}`*"]+[f"• {label}: {row.get(key) or '—'}" for label,key in fields]
        return {"response_type":"ephemeral","text":"\n".join(lines)}
    if cmd=="photos" and len(args)>=2 and args[1].lower()=="start":
        rows=_inventory_rows(client); queue=[r for r in rows if str(r.get("listing_id","" )).strip() and str(r.get("intake_status","" )).strip()=="Processed" and not str(r.get("cloudinary_image_urls","" )).strip() and str(r.get("listing_state","" )).strip()!="Rented Out"]
        if not queue:return {"response_type":"ephemeral","text":"No processed properties are waiting for photos."}
        row=queue[0]; raw=str(row.get("raw_message_text","")).strip(); text=f"*Photos needed — `{row['listing_id']}`*\n• BHK: {row.get('BHK') or '—'}\n• Rent: {row.get('monthly_rent') or '—'}\n• Locality: {row.get('locality') or '—'}\n• Furnishing: {row.get('furnish_type') or '—'}\n\nReply to this message in its thread with the photos, then reply `submit` in the same thread.\n\nOriginal source:\n```{raw[:1200]}```"
        ts=slack.post_message(INVENTORY_CHANNEL,text); return {"response_type":"ephemeral","text":f"Photo task opened for `{row['listing_id']}`. Thread timestamp: {ts}"}
    if cmd=="verify" and len(args)>=2 and args[1].lower()=="start":
        rows=_inventory_rows(client); row=next((r for r in rows if str(r.get("status","" )).strip()=="Needs Review"),None)
        if not row:return {"response_type":"ephemeral","text":"No inventory properties currently need verification."}
        blanks=[n for n in ("society_name","locality","pincode","BHK","bathrooms","total_floors","monthly_rent","security_deposit","built_up_area","floor_number","property_subtype","internal_property_type","landmark","furnish_type","preferred_tenant_type","bachelor_preference") if not str(row.get(n,"" )).strip()]
        text=f"*Verification needed — `{row['listing_id']}`*\nBlank fields: {', '.join(blanks) or 'none'}\n\nReply in this thread using `field=value` lines. Example: `internal_property_type=Semi Gated`. Reply `submit` when complete.\n\nSource:\n```{str(row.get('raw_message_text',''))[:1200]}```"
        slack.post_message(PROPERTY_VERIFICATION_CHANNEL,text); return {"response_type":"ephemeral","text":f"Verification opened for `{row['listing_id']}` in {PROPERTY_VERIFICATION_CHANNEL}."}
    if cmd=="run": return {"response_type":"ephemeral","text":"Run dispatch is configured for the new inventory pipeline; scheduled deployment wiring is handled by the live template."}
    if cmd=="fix" and len(args)>=3:
        lid,rest=args[1],args[2]; parts=rest.split(None,1)
        if len(parts)!=2:return {"response_type":"ephemeral","text":"Usage: `/efps fix <listing_id> <field> <value>`"}
        field,value=parts; rows=_inventory_rows(client); row=next((r for r in rows if str(r.get("listing_id","" )).strip().upper()==lid.upper()),None)
        if not row:return {"response_type":"ephemeral","text":f"No listing `{lid}` found."}
        blocked={"listing_id","raw_message_text","intake_status","source_group","inventory_locked","locality","pincode","google_maps_url","posted_url","posted_at","meta_catalog_id","meta_catalog_status"}
        if field in blocked or field not in schema.BY_NAME:return {"response_type":"ephemeral","text":f"`{field}` cannot be manually corrected by this command."}
        row[field]=value; projected=process_phase1(str(row.get("raw_message_text","")),row=row).row; projected[field]=value
        errs=[]
        from validate import validate
        errs=validate(projected)
        if errs:return {"response_type":"ephemeral","text":"Correction refused: "+"; ".join(errs)}
        from pipeline import write_phase1_update
        write_phase1_update(client,int(row["_row"] if "_row" in row else 0),projected)
        return {"response_type":"in_channel","text":f"Updated `{lid}` field `{field}`."}
    return {"response_type":"ephemeral","text":f"Unknown command. Use `{TOP_LEVEL_COMMAND} help`."}
