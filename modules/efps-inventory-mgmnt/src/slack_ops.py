"""Slack operator workflows for Inventory verification and photo operations."""
from __future__ import annotations
import json,os,urllib.request
from dataclasses import dataclass,field
from datetime import datetime,timezone
from shared.google_sheets import schema
from shared.google_sheets.client import GoogleSheetsClient
from shared.cloudinary.client import CloudinaryClient
from shared.slack.client import SlackClient
import pipeline
SESSION_PREFIX="inventory-slack:"
VERIFY_FIELDS=("society_name","locality","pincode","BHK","bathrooms","total_floors","monthly_rent","security_deposit","built_up_area","floor_number","property_subtype","society_amenities","internal_property_type","landmark","furnish_type","preferred_tenant_type","bachelor_preference")
PROTECTED={"listing_id","raw_message_text","intake_status","source_group","inventory_locked","listing_state","posted_url","posted_at","error_notes","meta_catalog_id","meta_catalog_status","city","google_maps_url"}
@dataclass
class Session:
 user_id:str;listing_id:str="";thread_ts:str="";skipped:list[str]=field(default_factory=list);answers:dict[str,str]=field(default_factory=dict);kind:str=""
def _table():
 import boto3;return boto3.resource("dynamodb",region_name=os.getenv("AWS_REGION","us-east-1")).Table(os.getenv("EFPS_DDB_PREFIX","efps")+"-sessions")
def _key(user,kind):return SESSION_PREFIX+kind+":"+user
def load(user,kind):
 item=_table().get_item(Key={"user_id":_key(user,kind)}).get("Item")
 if not item:return None
 return Session(user, str(item.get("listing_id") or ""),str(item.get("thread_ts") or ""),json.loads(item.get("skipped_json") or "[]"),json.loads(item.get("answers_json") or "{}"),kind)
def save(s):_table().put_item(Item={"user_id":_key(s.user_id,s.kind),"listing_id":s.listing_id,"thread_ts":s.thread_ts,"skipped_json":json.dumps(s.skipped),"answers_json":json.dumps(s.answers),"expires_at":int(datetime.now(timezone.utc).timestamp())+86400})
def clear(user,kind):_table().delete_item(Key={"user_id":_key(user,kind)})
def _rows():
 c=GoogleSheetsClient();raw=c.read_range(schema.SHEET_ID,schema.WORKSHEET_NAME,f"A2:{schema.EXPECTED_LAST_COLUMN}");return [(i+2,schema.row_to_mapping(r)) for i,r in enumerate(raw) if r]
def _candidates(kind,skipped):
 skip=set(skipped)
 if kind=="photos":return [(n,r) for n,r in _rows() if r.get("intake_status")=="Processed" and not str(r.get("cloudinary_image_urls") or "").strip() and r.get("listing_id") not in skip]
 return [(n,r) for n,r in _rows() if str(r.get("status") or "").lower()=="needs review" and r.get("listing_id") not in skip]
def photo_start(user):
 s=load(user,"photos") or Session(user,kind="photos");c=_candidates("photos",s.skipped)
 if not c:return s,"No processed property is currently waiting for photos."
 s.listing_id=c[0][1]["listing_id"];save(s);return s,f"Photo upload session: `{s.listing_id}`. Reply in this thread with photos, then `done`."
def photo_move(user,verb):
 s=load(user,"photos") or Session(user,kind="photos")
 if s.listing_id:s.skipped.append(s.listing_id)
 c=_candidates("photos",s.skipped)
 if not c:clear(user,"photos");return s,"No more processed properties need photos."
 s.listing_id=c[0][1]["listing_id"];save(s);return s,f"Showing `{s.listing_id}`. Reply with photos, then `done`."
def download_slack_file(file_obj):
 url=file_obj.get("url_private_download") or file_obj.get("url_private");size=int(file_obj.get("size") or 0)
 if not url or size>15*1024*1024:return None
 token=SlackClient().config.bot_token;req=urllib.request.Request(url,headers={"Authorization":f"Bearer {token}"})
 try:
  with urllib.request.urlopen(req,timeout=30) as resp:return resp.read()
 except Exception:return None
def save_photos(user,channel):
 s=load(user,"photos")
 if not s or not s.listing_id:return "No photo session is open."
 messages=SlackClient().replies(channel,s.thread_ts) if s.thread_ts else [];files=[f for m in messages for f in (m.get("files") or []) if str(f.get("mimetype","")).startswith("image/")][:30];blobs=[b for f in files if (b:=download_slack_file(f))]
 if not blobs:return "No readable image attachments were found. Nothing was changed."
 found=next(((n,r) for n,r in _rows() if r.get("listing_id")==s.listing_id),None)
 if not found:return f"Property `{s.listing_id}` is not present."
 n,row=found;existing=[x.strip() for x in str(row.get("cloudinary_image_urls") or "").split(",") if x.strip()];cu=CloudinaryClient();new=[]
 for i,b in enumerate(blobs,start=len(existing)+1):new.append(str(cu.upload_bytes(b,public_id=f"properties/{s.listing_id}/photo_{i}",overwrite=False)["secure_url"]))
 GoogleSheetsClient().write_range(schema.SHEET_ID,schema.WORKSHEET_NAME,schema.range_for("cloudinary_image_urls","cloudinary_image_urls",n)) if False else None
 GoogleSheetsClient().write_range(schema.SHEET_ID,schema.WORKSHEET_NAME,schema.range_for("cloudinary_image_urls","cloudinary_image_urls",n),[[", ".join((existing+new)[:10])]])
 clear(user,"photos");return f"Saved {len(new)} photo(s) for `{s.listing_id}`."
def verify_start(user):
 s=load(user,"verify") or Session(user,kind="verify");c=_candidates("verify",s.skipped)
 if not c:return s,"No properties are currently in Needs Review."
 s.listing_id=c[0][1]["listing_id"];s.answers={};save(s);missing=[f for f in VERIFY_FIELDS if not str(c[0][1].get(f) or "").strip()];return s,f"Verification for `{s.listing_id}`. Fields needing input: {', '.join(missing) if missing else 'review existing values'}"
def verify_answer(user,text):
 s=load(user,"verify")
 if not s or not s.listing_id:return "No verification session is open."
 for line in str(text).splitlines():
  if "=" not in line:continue
  f,v=line.split("=",1);f=f.strip();v=v.strip()
  if f in schema.BY_NAME and f not in PROTECTED:s.answers[f]=v
 save(s);return "Answer recorded. Reply `submit` when the values are complete."
def verify_submit(user):
 s=load(user,"verify")
 if not s or not s.listing_id:return "No verification session is open."
 found=next(((n,r) for n,r in _rows() if r.get("listing_id")==s.listing_id),None)
 if not found:return "The canonical row could not be found."
 n,row=found;candidate=pipeline.deterministic(str(row.get("raw_message_text") or ""),row)
 candidate.update(s.answers);errors=pipeline.validate.validate(candidate)
 if errors:return "Validation still fails: "+"; ".join(errors)
 candidate["status"]="Pending";candidate["intake_status"]="Processed";pipeline.write_phase1_update(GoogleSheetsClient(),n,candidate);clear(user,"verify");return f"Verified `{s.listing_id}` and saved the corrected canonical row."
