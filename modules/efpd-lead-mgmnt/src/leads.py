"""Lead business rules migrated from the verified live implementation."""
from __future__ import annotations
import logging,re
from datetime import datetime,timedelta,timezone
import db,media
log=logging.getLogger(__name__)
IST=timezone(timedelta(hours=5,minutes=30))
NEW="New";CONTACTED="Contacted";SHARED="Shared";VISITING="Visiting";NEGOTIATING="Negotiating";BOOKED="Booked";CLOSED="Closed";LOST="Lost";ON_HOLD="On hold";STAGES=[NEW,CONTACTED,SHARED,VISITING,NEGOTIATING,BOOKED,CLOSED,LOST,ON_HOLD];TERMINAL={CLOSED,LOST}
OUR_REPLY="Our reply";THEIR_REPLY="Their reply";NO_MATCH="No match";VISIT_DUE="Visit due";FOLLOWUP_DUE="Follow-up due";NOTHING="None";ACTIONS=[OUR_REPLY,THEIR_REPLY,NO_MATCH,VISIT_DUE,FOLLOWUP_DUE,NOTHING];STICKY_ACTIONS={NO_MATCH,VISIT_DUE}
STAGE_EMOJI={NEW:"🆕",CONTACTED:"💬",SHARED:"📤",VISITING:"🏠",NEGOTIATING:"🤝",BOOKED:"📝",CLOSED:"✅",LOST:"❌",ON_HOLD:"⏸️"};ACTION_EMOJI={OUR_REPLY:"🔴",THEIR_REPLY:"🟡",NO_MATCH:"🔵",VISIT_DUE:"🟣",FOLLOWUP_DUE:"🟠",NOTHING:"⚪"};CARD_BUTTONS=[SHARED,VISITING,NEGOTIATING,BOOKED,CLOSED,ON_HOLD,LOST]
class LeadError(Exception):pass
def clean_sender_name(raw):
 name=" ".join(str(raw or "").split()).strip()
 if not name or not re.search(r"[A-Za-z]",name):return ""
 return name[:60]
def normalise_phone(raw):
 digits=re.sub(r"\D","",str(raw or "").split("@")[0])
 if len(digits)==10:return "91"+digits
 if len(digits)==11 and digits.startswith("0"):return "91"+digits[1:]
 if len(digits)==13 and digits.startswith("091"):return digits[1:]
 return digits
def display_phone(phone):
 p=normalise_phone(phone);return f"+91 {p[2:7]} {p[7:]}" if len(p)==12 and p.startswith("91") else ("+"+p if p else "unknown")
def label(lead):return str(lead.get("customer_name") or "").strip() or display_phone(lead.get("phone_number",""))
def now_iso():return datetime.now(timezone.utc).isoformat(timespec="seconds")
def _parse(ts):
 try:return datetime.fromisoformat(str(ts).replace("Z","+00:00"))
 except (ValueError,TypeError):return None
def ist_label(ts):
 dt=_parse(ts);return dt.astimezone(IST).strftime("%-d %b, %-I:%M %p").lower() if dt else "—"
def age_label(ts,*,_now=None):
 dt=_parse(ts)
 if not dt:return "—"
 s=int(((_now or datetime.now(timezone.utc))-dt).total_seconds())
 return "just now" if s<60 else (f"{s//60}m ago" if s<3600 else (f"{s//3600}h ago" if s<86400 else f"{s//86400}d ago"))
def quiet_days(lead,*,_now=None):
 dt=_parse(lead.get("last_message_at",""));return max(0,(((_now or datetime.now(timezone.utc))-dt).days)) if dt else 0
def parse_followup(text,*,_today=None):
 raw=str(text or "").strip().lower();today=_today or datetime.now(IST).date()
 if not raw:raise LeadError("no date given")
 if raw=="today":return today.isoformat()
 if raw in ("tomorrow","tmrw"):return (today+timedelta(days=1)).isoformat()
 m=re.fullmatch(r"([0-9]+)\s*d(ays?)?",raw)
 if m:return (today+timedelta(days=int(m.group(1)))).isoformat()
 m=re.fullmatch(r"([0-9]+)\s*w(eeks?)?",raw)
 if m:return (today+timedelta(weeks=int(m.group(1)))).isoformat()
 m=re.fullmatch(r"([0-9]{4})-([0-9]{2})-([0-9]{2})",raw)
 if m:
  try:return datetime.strptime(raw,"%Y-%m-%d").date().isoformat()
  except ValueError:raise LeadError(f"no such date: {text}") from None
 m=re.fullmatch(r"([0-9]{1,2})\s*([a-z]{3,})\.?\s*([0-9]{4})?",raw)
 if m:
  months=["jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec"];mn=m.group(2)[:3]
  if mn in months:
   y=int(m.group(3)) if m.group(3) else today.year
   try:d=datetime(y,months.index(mn)+1,int(m.group(1))).date()
   except ValueError:raise LeadError(f"no such date: {text}") from None
   if not m.group(3) and d<today:d=d.replace(year=y+1)
   return d.isoformat()
 raise LeadError(f"could not read a date from {text!r}")
def next_action(lead,*,_today=None):
 if lead.get("stage") in TERMINAL:return NOTHING
 if lead.get("action") in STICKY_ACTIONS:return lead["action"]
 due=str(lead.get("next_followup_date") or "")
 if due and due<=(_today or datetime.now(IST).date()).isoformat():return FOLLOWUP_DUE
 if lead.get("last_direction")=="in":return OUR_REPLY
 if lead.get("last_direction")=="out":return THEIR_REPLY
 return NOTHING
def next_stage(lead,direction):return CONTACTED if direction=="out" and (lead.get("stage") or NEW)==NEW else (lead.get("stage") or NEW)
def validate_stage(value):
 for x in STAGES:
  if x.lower()==str(value or "").strip().lower():return x
 raise LeadError(f"unknown stage {value!r} — use one of: "+", ".join(STAGES))
def validate_action(value):
 wanted=str(value or "").strip().lower().replace("_"," ").replace("-"," ")
 for x in ACTIONS:
  if x.lower().replace("-"," ")==wanted:return x
 raise LeadError(f"unknown action {value!r} — use one of: "+", ".join(ACTIONS))
def record_message(phone,direction,body,*,message_id="",sender_name="",group_name="",media_reference="",media_blobs=None,_uploader=None,_res=None):
 if direction not in ("in","out"):raise LeadError("direction must be 'in' or 'out'")
 key=normalise_phone(phone)
 if not key:raise LeadError(f"unusable phone number: {phone!r}")
 existing=db.get_lead(key,_res=_res) or {};created=not existing
 if message_id and db.interaction_exists(key,message_id,_res=_res):existing["_created"]=False;existing["_duplicate"]=True;return existing
 media_urls=str(media_reference or "").strip()
 if media_blobs:
  try:
   uploaded=media.upload_lead_images(key,message_id,list(media_blobs),_uploader=_uploader)
   uploaded_urls=", ".join(x.url for x in uploaded)
   media_urls=", ".join(x for x in (media_urls,uploaded_urls) if x)
  except Exception as exc:log.warning("lead image upload failed: %s",exc)
 has_media=bool(media_reference or media_blobs)
 db.log_interaction(key,direction,body,message_id=message_id,group_name=group_name,has_media=has_media,media_urls=media_urls,_res=_res)
 lead=dict(existing);lead.update({"phone_number":key,"last_message":(body or "")[:400],"last_message_at":now_iso(),"last_direction":direction});name=clean_sender_name(sender_name)
 if name and not lead.get("customer_name"):lead["customer_name"]=name
 if group_name and not lead.get("source_group"):lead["source_group"]=group_name
 if created:lead["stage"]=NEW;lead["unread_count"]=0
 lead["stage"]=next_stage(lead,direction)
 if direction=="in":lead["unread_count"]=int(lead.get("unread_count") or 0)+1
 else:
  lead["unread_count"]=0
  if lead.get("action")!=NO_MATCH:lead["next_followup_date"]=""
 lead["action"]=next_action(lead);stored=db.put_lead(lead,_res=_res);stored["_created"]=created;stored["_duplicate"]=False;return stored
def set_stage(phone,stage,*,reason="",_res=None):
 key=normalise_phone(phone);lead=db.get_lead(key,_res=_res)
 if not lead:raise LeadError(f"no lead for {display_phone(key)}")
 lead["stage"]=validate_stage(stage)
 if lead["stage"]==LOST:lead["lost_reason"]=reason or lead.get("lost_reason") or "not given"
 if lead["stage"]==VISITING and lead.get("action") not in STICKY_ACTIONS:lead["action"]=VISIT_DUE
 if lead["stage"] in TERMINAL:lead["action"]=NOTHING;lead["next_followup_date"]=""
 else:
  if lead["stage"] in (SHARED,NEGOTIATING,BOOKED) and lead.get("action")==NO_MATCH:lead["action"]=NOTHING
  lead["action"]=next_action(lead)
 return db.put_lead(lead,_res=_res)
def set_action(phone,action,*,_res=None):
 key=normalise_phone(phone);lead=db.get_lead(key,_res=_res)
 if not lead:raise LeadError(f"no lead for {display_phone(key)}")
 lead["action"]=validate_action(action);return db.put_lead(lead,_res=_res)
def set_followup(phone,when,*,_res=None):
 key=normalise_phone(phone);lead=db.get_lead(key,_res=_res)
 if not lead:raise LeadError(f"no lead for {display_phone(key)}")
 lead["next_followup_date"]=parse_followup(when);lead["action"]=next_action(lead);return db.put_lead(lead,_res=_res)
def set_fields(phone,updates,*,_res=None):
 allowed={"customer_name","looking_requirement","budget_min","budget_max","preferred_localities","interested_listings","lost_reason"};key=normalise_phone(phone);lead=db.get_lead(key,_res=_res)
 if not lead:raise LeadError(f"no lead for {display_phone(key)}")
 for f,v in updates.items():
  if f not in allowed:raise LeadError(f"{f} is not an editable field")
  lead[f]=v
 return db.put_lead(lead,_res=_res)
def mark_read(phone,*,_res=None):
 key=normalise_phone(phone);lead=db.get_lead(key,_res=_res)
 if not lead:raise LeadError(f"no lead for {display_phone(key)}")
 lead["unread_count"]=0;return db.put_lead(lead,_res=_res)
def refresh_actions(*, _res=None,_today=None):
 changed=[]
 for lead in db.all_leads(_res=_res):
  wanted=next_action(lead,_today=_today)
  if wanted!=lead.get("action"):lead["action"]=wanted;changed.append(db.put_lead(lead,_res=_res))
 return changed
def queue(leads,*,_now=None):
 priority={OUR_REPLY:0,FOLLOWUP_DUE:1,VISIT_DUE:2,NO_MATCH:3,THEIR_REPLY:4,NOTHING:5};live=[l for l in leads if l.get("stage") not in TERMINAL];return sorted(live,key=lambda l:(priority.get(l.get("action"),9),str(l.get("last_message_at") or "")))
def summarise(leads,*,_now=None):
 live=[l for l in leads if l.get("stage") not in TERMINAL];return {"total":len(leads),"live":len(live),"our_reply":[l for l in live if l.get("action")==OUR_REPLY],"followup_due":[l for l in live if l.get("action")==FOLLOWUP_DUE],"visit_due":[l for l in live if l.get("action")==VISIT_DUE],"no_match":[l for l in live if l.get("action")==NO_MATCH],"new":[l for l in live if l.get("stage")==NEW],"quiet":[l for l in live if quiet_days(l,_now=_now)>=3 and l.get("action")==THEIR_REPLY],"closed":[l for l in leads if l.get("stage")==CLOSED],"lost":[l for l in leads if l.get("stage")==LOST]}
