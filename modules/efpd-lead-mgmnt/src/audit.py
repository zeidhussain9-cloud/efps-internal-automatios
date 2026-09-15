"""Lead audit trail."""
from __future__ import annotations
import contextlib,contextvars,uuid
from datetime import datetime,timezone
import config
AUTO="auto";MANUAL="manual"
TRACKED=["stage","action","next_followup_date","customer_name","looking_requirement","budget_min","budget_max","preferred_localities","interested_listings","lost_reason"]
_actor=contextvars.ContextVar("efps_audit_actor",default=("system",AUTO,""));MAX_VALUE=700
@contextlib.contextmanager
def actor(who:str,*,source:str=MANUAL,reason:str=""):
 t=_actor.set((who or "system",source,reason))
 try:yield
 finally:_actor.reset(t)
def current():return _actor.get()
def _clip(v):
 t=str(v or "");return t if len(t)<=MAX_VALUE else t[:MAX_VALUE]+"…"
def diff(before,after):
 if not before:return [{"field":"lead","old":"","new":"created"}]
 out=[]
 for f in TRACKED:
  old=str(before.get(f,"") or "");new=str(after.get(f,"") or "")
  if old!=new:out.append({"field":f,"old":_clip(old),"new":_clip(new)})
 return out
def record(phone,changes,*,_res=None):
 if not changes:return []
 import db
 who,source,reason=current();stamp=datetime.now(timezone.utc).isoformat();written=[]
 for ch in changes:
  item={"phone_number":str(phone),"changed_at":f"{stamp}#{uuid.uuid4().hex[:6]}","field":ch["field"],"old_value":ch["old"],"new_value":ch["new"],"source":source,"actor":who}
  if reason:item["reason"]=reason
  try:db._table(config.DDB_AUDIT,_res).put_item(Item=item);written.append(item)
  except Exception as exc:print(f"audit write failed: {exc!r}")
 return written
def history(phone,limit=20,*,_res=None):
 import db
 try:return db._table(config.DDB_AUDIT,_res).query(KeyConditionExpression="phone_number = :p",ExpressionAttributeValues={":p":str(phone)},ScanIndexForward=False,Limit=limit).get("Items",[])
 except Exception as exc:print(f"audit read failed: {exc!r}");return []
def describe(entry):
 import leads as L
 when=str(entry.get("changed_at","")).split("#")[0]
 try:when=datetime.fromisoformat(when).astimezone(L.IST).strftime("%-d %b %-I:%M %p")
 except (ValueError,TypeError):pass
 field=str(entry.get("field",""));new=str(entry.get("new_value","")) or "cleared";by="you" if entry.get("source")==MANUAL else "system"
 return f"{when} — lead created ({by})" if field=="lead" else f"{when} — {field.replace('_',' ')} → {new} ({by})"
