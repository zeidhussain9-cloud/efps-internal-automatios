"""DynamoDB-stream lead-card worker and scheduled dashboard worker."""
from __future__ import annotations
import sys
sys.path.insert(0,"modules/efpd-lead-mgmnt/src")
import config,db,digest,lead_card
COSMETIC={"card_ts","updated_at"}
def _plain(image):
 out={}
 for k,v in (image or {}).items():
  if not isinstance(v,dict):out[k]=v
  elif "S" in v:out[k]=v["S"]
  elif "N" in v:out[k]=int(v["N"]) if "." not in v["N"] else float(v["N"])
  elif "BOOL" in v:out[k]=v["BOOL"]
  elif "NULL" in v:out[k]=""
  else:out[k]=next(iter(v.values()))
 return out
def meaningful_change(old,new):
 if not old:return True
 return any(str(old.get(k,""))!=str(new.get(k,"")) for k in (set(old)|set(new))-COSMETIC)
def handle_stream(event,*,_post=None,_res=None):
 latest={};order=[]
 for rec in event.get("Records",[]):
  if rec.get("eventName")=="REMOVE":continue
  d=rec.get("dynamodb",{});new=_plain(d.get("NewImage"));old=_plain(d.get("OldImage"));phone=new.get("phone_number")
  if not phone:continue
  if phone in latest:latest[phone]={"old":latest[phone]["old"],"new":new}
  else:latest[phone]={"old":old,"new":new};order.append(phone)
 redrawn=skipped=0
 for phone in order:
  pair=latest[phone]
  if not meaningful_change(pair["old"],pair["new"]):skipped+=1;continue
  try:
   lead=dict(pair["new"]);lead["card_ts"]=(db.get_lead(phone,_res=_res) or {}).get("card_ts",lead.get("card_ts",""));lead_card.post_or_update(lead,_post=_post,_res=_res);redrawn+=1
  except Exception as exc:print(f"lead card redraw failed: {exc!r}")
 board=False
 if redrawn:
  try:board=bool(digest.run(_res=_res).get("updated"))
  except Exception as exc:print(f"board refresh failed: {exc!r}")
 return {"redrawn":redrawn,"skipped":skipped,"board":board}
def lambda_handler(event,context):
 if isinstance(event,dict) and event.get("Records"):return handle_stream(event)
 if isinstance(event,dict) and event.get("command")=="digest":return digest.run()
 return {"ok":True,"ignored":"nothing to do"}
