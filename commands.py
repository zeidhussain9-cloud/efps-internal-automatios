"""Slack /efps entrypoint adapter for the migrated live operational surface."""
from __future__ import annotations
import json,os,sys
from shared.google_sheets import schema
from shared.google_sheets.client import GoogleSheetsClient
sys.path.insert(0,"modules/efps-inventory-mgmnt")
sys.path.insert(0,"modules/efpd-lead-mgmnt/src")
sys.path.insert(0,"shared/slack")
from src import pipeline
from src.slack_ops import photo_start,photo_move,verify_start
import bugs
HELP="*EFPS panel — commands*\n• `/efps status` — inventory status\n• `/efps run` — process Raw inventory rows\n• `/efps show EF-XXXX` — show one property\n• `/efps fix EF-XXXX <field> <value>` — same-row validated correction\n• `/efps verify start` — property verification queue\n• `/efps photos start` — photo collection queue\n• `/efps bug report` / `/efps bugs` — runtime bug tracking\n• `/efps pause` / `/efps resume` — scheduled batches"
RULES=tuple(x for x in os.getenv("EFPS_SCHEDULE_RULES","efps-internal-automatios-morning,efps-internal-automatios-midday,efps-internal-automatios-evening").split(",") if x)
PROTECTED={"listing_state","posted_url","posted_at","error_notes","meta_catalog_id","meta_catalog_status","inventory_locked"}
def _rows():
 c=GoogleSheetsClient();raw=c.read_range(schema.SHEET_ID,schema.WORKSHEET_NAME,f"A2:{schema.EXPECTED_LAST_COLUMN}");return [(i+2,schema.row_to_mapping(r)) for i,r in enumerate(raw) if r]
def _find(lid):
 w=lid.strip().upper()
 for n,r in _rows():
  if str(r.get("listing_id","")).strip().upper()==w:return n,r
 raise ValueError(f"No property with ID `{lid}`.")
def status(_args=""):
 rows=[r for _,r in _rows()];return f"*EFPS panel — status*\n• Waiting to process: *{sum(r.get('intake_status')=='Raw' for r in rows)}*\n• Processed: *{sum(r.get('intake_status')=='Processed' for r in rows)}*\n• Needs Review: *{sum(str(r.get('status','')).lower()=='needs review' for r in rows)}*\n• Rows in sheet: {len(rows)}"
def show(args):
 _,r=_find(args);fields=("society_name","BHK","property_subtype","monthly_rent","security_deposit","furnish_type","floor_number","locality","internal_property_type");return "\n".join([f"*{r.get('listing_id')}* — {r.get('status') or 'no status'}"]+[f"• {f}: {str(r.get(f,'')).strip() or '_blank_'}" for f in fields])
def fix(args):
 p=args.strip().split(None,2)
 if len(p)<3:raise ValueError("Use `/efps fix <listing_id> <field> <value>`." )
 lid,field,value=p
 if field not in schema.BY_NAME:raise ValueError(f"Unknown field: `{field}`")
 if field in PROTECTED:raise ValueError(f"`{field}` is protected by the current ownership contract.")
 n,row=_find(lid);candidate=pipeline.deterministic(str(row.get("raw_message_text") or ""),row);candidate[field]=value;candidate["status"]="Pending";errors=pipeline.validate.validate(candidate)
 if errors:raise ValueError("Correction failed validation: "+"; ".join(errors))
 candidate["intake_status"]="Processed";pipeline.write_phase1_update(GoogleSheetsClient(),n,candidate);return f"*Corrected `{candidate['listing_id']}`*\n• {field}: `{row.get(field,'')}` → `{candidate.get(field,'')}`"
def run(_args=""):
 import boto3
 boto3.client("lambda",region_name=os.getenv("AWS_REGION","us-east-1")).invoke(FunctionName=os.getenv("EFPS_BATCH_FUNCTION","efps-internal-automatios-batch"),InvocationType="Event",Payload=json.dumps({"command":"process","commit":True}).encode());return "*Batch started.*"
def _set_schedules(enabled):
 import boto3;c=boto3.client("events",region_name=os.getenv("AWS_REGION","us-east-1"))
 for name in RULES:(c.enable_rule if enabled else c.disable_rule)(Name=name)
def handle(text,user_id="",channel_id=""):
 raw=" ".join(str(text or "").split());verb,_,args=raw.partition(" ");v=verb.lower()
 try:
  if not v or v=="help":return HELP
  if v=="status":return status(args)
  if v=="show":return show(args)
  if v=="fix":return fix(args)
  if v=="run":return run(args)
  if v=="pause":_set_schedules(False);return "*Scheduled batches paused.*"
  if v=="resume":_set_schedules(True);return "*Scheduled batches resumed.*"
  if v=="photos":
   if not user_id:raise ValueError("I could not tell who you are.")
   a=(args.strip().split(None,1)+[""])[0].lower() or "start";s,msg=photo_start(user_id) if a=="start" else photo_move(user_id,a) if a in {"next","skip"} else (None,"Photo commands: start, next, skip, done, exit.");return msg
  if v=="verify":
   if not user_id:raise ValueError("I could not tell who you are.")
   if args.strip().lower().startswith("start") or not args.strip():_,msg=verify_start(user_id);return msg
   return "Verification commands: start, submit, next, skip, exit."
  if v=="bugs":return bugs.format_list(bugs.open_bugs())
  if v=="bug":return bugs.start(user_id)
  return HELP
 except Exception as exc:return f":warning: {exc}"
