"""Lead CRM rules copied from legacy behavior, without inventory coupling."""
from __future__ import annotations
import re
from datetime import date, datetime, timedelta, timezone
import db

IST = timezone(timedelta(hours=5, minutes=30))
NEW, CONTACTED, SHARED, VISITING, NEGOTIATING, BOOKED, CLOSED, LOST, ON_HOLD = ("New", "Contacted", "Shared", "Visiting", "Negotiating", "Booked", "Closed", "Lost", "On hold")
STAGES = [NEW, CONTACTED, SHARED, VISITING, NEGOTIATING, BOOKED, CLOSED, LOST, ON_HOLD]
TERMINAL = {CLOSED, LOST}
OUR_REPLY, THEIR_REPLY, NO_MATCH, VISIT_DUE, FOLLOWUP_DUE, NOTHING = ("Our reply", "Their reply", "No match", "Visit due", "Follow-up due", "None")
ACTIONS = [OUR_REPLY, THEIR_REPLY, NO_MATCH, VISIT_DUE, FOLLOWUP_DUE, NOTHING]
STICKY_ACTIONS = {NO_MATCH, VISIT_DUE}
CARD_BUTTONS = [SHARED, VISITING, NEGOTIATING, BOOKED, CLOSED, ON_HOLD, LOST]
STAGE_EMOJI = {NEW:"🆕", CONTACTED:"💬", SHARED:"📤", VISITING:"🏠", NEGOTIATING:"🤝", BOOKED:"📝", CLOSED:"✅", LOST:"❌", ON_HOLD:"⏸️"}
ACTION_EMOJI = {OUR_REPLY:"🔴", THEIR_REPLY:"🟡", NO_MATCH:"🔵", VISIT_DUE:"🟣", FOLLOWUP_DUE:"🟠", NOTHING:"⚪"}
class LeadError(Exception): pass

def clean_sender_name(raw: str) -> str:
    name = " ".join(str(raw or "").split()).strip()
    return name[:60] if name and re.search(r"[A-Za-z]", name) else ""
def normalise_phone(raw: str) -> str:
    text = str(raw or "").split("@")[0]; digits = re.sub(r"\D", "", text)
    if len(digits)==10:return "91"+digits
    if len(digits)==11 and digits.startswith("0"):return "91"+digits[1:]
    if len(digits)==13 and digits.startswith("091"):return digits[1:]
    return digits
def display_phone(phone: str) -> str:
    p=normalise_phone(phone)
    return f"+91 {p[2:7]} {p[7:]}" if len(p)==12 and p.startswith("91") else ("+"+p if p else "unknown")
def label(lead: dict) -> str:return str(lead.get("customer_name") or "").strip() or display_phone(lead.get("phone_number", ""))
def now_iso() -> str:return datetime.now(timezone.utc).isoformat(timespec="seconds")
def _parse(ts: str):
    try:return datetime.fromisoformat(str(ts).replace("Z","+00:00"))
    except (ValueError,TypeError):return None
def ist_label(ts: str) -> str:
    dt=_parse(ts); return dt.astimezone(IST).strftime("%-d %b, %-I:%M %p").lower() if dt else "—"
def age_label(ts: str, *, _now=None) -> str:
    dt=_parse(ts)
    if not dt:return "—"
    seconds=int(((_now or datetime.now(timezone.utc))-dt).total_seconds())
    if seconds<60:return "just now"
    if seconds<3600:return f"{seconds//60}m ago"
    if seconds<86400:return f"{seconds//3600}h ago"
    return f"{seconds//86400}d ago"
def quiet_days(lead: dict, *, _now=None) -> int:
    dt=_parse(lead.get("last_message_at", "")); return max(0,(((_now or datetime.now(timezone.utc))-dt).days)) if dt else 0
def parse_followup(text: str, *, _today: date|None=None) -> str:
    raw=str(text or "").strip().lower(); today=_today or datetime.now(IST).date()
    if raw=="today":return today.isoformat()
    if raw in {"tomorrow","tmrw"}:return (today+timedelta(days=1)).isoformat()
    m=re.fullmatch(r"(\d+)\s*d(?:ays?)?",raw)
    if m:return (today+timedelta(days=int(m.group(1)))).isoformat()
    m=re.fullmatch(r"(\d+)\s*w(?:eeks?)?",raw)
    if m:return (today+timedelta(weeks=int(m.group(1)))).isoformat()
    m=re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})",raw)
    if m:
        try:return datetime.strptime(raw,"%Y-%m-%d").date().isoformat()
        except ValueError:raise LeadError(f"no such date: {text}") from None
    m=re.fullmatch(r"(\d{1,2})\s*([a-z]{3,})\.?\s*(\d{4})?",raw)
    if m:
        months=["jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec"]; month=m.group(2)[:3]
        if month in months:
            y=int(m.group(3)) if m.group(3) else today.year
            try:d=datetime(y,months.index(month)+1,int(m.group(1))).date()
            except ValueError:raise LeadError(f"no such date: {text}") from None
            if not m.group(3) and d<today:d=d.replace(year=y+1)
            return d.isoformat()
    raise LeadError(f"could not read a date from {text!r}")
def next_action(lead: dict, *, _today: date|None=None) -> str:
    if lead.get("stage") in TERMINAL:return NOTHING
    current=lead.get("action","")
    if current in STICKY_ACTIONS:return current
    today=(_today or datetime.now(IST).date()).isoformat(); due=str(lead.get("next_followup_date") or "")
    if due and due<=today:return FOLLOWUP_DUE
    if lead.get("last_direction")=="in":return OUR_REPLY
    if lead.get("last_direction")=="out":return THEIR_REPLY
    return NOTHING
def next_stage(lead:dict,direction:str)->str:
    stage=lead.get("stage") or NEW; return CONTACTED if direction=="out" and stage==NEW else stage
def validate_stage(value:str)->str:
    wanted=str(value or "").strip().lower()
    for stage in STAGES:
        if stage.lower()==wanted:return stage
    raise LeadError(f"unknown stage {value!r}")
def validate_action(value:str)->str:
    wanted=str(value or "").strip().lower().replace("_"," ").replace("-"," ")
    for action in ACTIONS:
        if action.lower().replace("-"," ")==wanted:return action
    raise LeadError(f"unknown action {value!r}")
def record_message(phone:str,direction:str,body:str,*,message_id:str="",sender_name:str="",group_name:str="",_res=None)->dict:
    if direction not in {"in","out"}:raise LeadError("direction must be 'in' or 'out'")
    key=normalise_phone(phone)
    if not key:raise LeadError(f"unusable phone number: {phone!r}")
    existing=db.get_lead(key,_res=_res) or {}; created=not existing
    if message_id and db.interaction_exists(key,message_id,_res=_res):existing.update({"_created":False,"_duplicate":True});return existing
    db.log_interaction(key,direction,body,message_id=message_id,group_name=group_name,_res=_res)
    lead=dict(existing); lead.update({"phone_number":key,"last_message":str(body or "")[:400],"last_message_at":now_iso(),"last_direction":direction})
    name=clean_sender_name(sender_name)
    if name and not lead.get("customer_name"):lead["customer_name"]=name
    if group_name and not lead.get("source_group"):lead["source_group"]=group_name
    if created:lead.update({"stage":NEW,"unread_count":0})
    lead["stage"]=next_stage(lead,direction)
    if direction=="in":lead["unread_count"]=int(lead.get("unread_count") or 0)+1
    else:
        lead["unread_count"]=0
        if lead.get("action")!=NO_MATCH:lead["next_followup_date"]=""
    lead["action"]=next_action(lead); stored=db.put_lead(lead,_res=_res); stored.update({"_created":created,"_duplicate":False}); return stored
def set_stage(phone:str,stage:str,*,reason:str="",_res=None)->dict:
    key=normalise_phone(phone);lead=db.get_lead(key,_res=_res)
    if not lead:raise LeadError(f"no lead for {display_phone(key)}")
    lead["stage"]=validate_stage(stage)
    if lead["stage"]==LOST:lead["lost_reason"]=reason or lead.get("lost_reason") or "not given"
    if lead["stage"]==VISITING and lead.get("action") not in STICKY_ACTIONS:lead["action"]=VISIT_DUE
    if lead["stage"] in TERMINAL:lead["action"]=NOTHING;lead["next_followup_date"]=""
    else:
        if lead["stage"] in {SHARED,NEGOTIATING,BOOKED} and lead.get("action")==NO_MATCH:lead["action"]=NOTHING
        lead["action"]=next_action(lead)
    return db.put_lead(lead,_res=_res)
def set_action(phone:str,action:str,*,_res=None)->dict:
    lead=db.get_lead(normalise_phone(phone),_res=_res)
    if not lead:raise LeadError("lead not found")
    lead["action"]=validate_action(action);return db.put_lead(lead,_res=_res)
def set_followup(phone:str,when:str,*,_res=None)->dict:
    lead=db.get_lead(normalise_phone(phone),_res=_res)
    if not lead:raise LeadError("lead not found")
    lead["next_followup_date"]=parse_followup(when);lead["action"]=next_action(lead);return db.put_lead(lead,_res=_res)
def set_fields(phone:str,updates:dict,*,_res=None)->dict:
    allowed={"customer_name","looking_requirement","budget_min","budget_max","preferred_localities","interested_listings","lost_reason"};lead=db.get_lead(normalise_phone(phone),_res=_res)
    if not lead:raise LeadError("lead not found")
    bad=set(updates)-allowed
    if bad:raise LeadError(f"not editable: {', '.join(sorted(bad))}")
    lead.update(updates);return db.put_lead(lead,_res=_res)
def mark_read(phone:str,*,_res=None)->dict:
    lead=db.get_lead(normalise_phone(phone),_res=_res)
    if not lead:raise LeadError("lead not found")
    lead["unread_count"]=0;return db.put_lead(lead,_res=_res)
def refresh_actions(*, _res=None,_today=None)->list[dict]:
    changed=[]
    for lead in db.all_leads(_res=_res):
        wanted=next_action(lead,_today=_today)
        if wanted!=lead.get("action"):lead["action"]=wanted;changed.append(db.put_lead(lead,_res=_res))
    return changed
def queue(rows:list[dict],*,_now=None)->list[dict]:
    priority={OUR_REPLY:0,FOLLOWUP_DUE:1,VISIT_DUE:2,NO_MATCH:3,THEIR_REPLY:4,NOTHING:5};return sorted([r for r in rows if r.get("stage") not in TERMINAL],key=lambda r:(priority.get(r.get("action"),9),str(r.get("last_message_at") or "")))
def summarise(rows:list[dict],*,_now=None)->dict:
    live=[r for r in rows if r.get("stage") not in TERMINAL]
    return {"total":len(rows),"live":len(live),"our_reply":[r for r in live if r.get("action")==OUR_REPLY],"followup_due":[r for r in live if r.get("action")==FOLLOWUP_DUE],"visit_due":[r for r in live if r.get("action")==VISIT_DUE],"no_match":[r for r in live if r.get("action")==NO_MATCH],"new":[r for r in live if r.get("stage")==NEW],"quiet":[r for r in live if quiet_days(r,_now=_now)>=3 and r.get("action")==THEIR_REPLY],"closed":[r for r in rows if r.get("stage")==CLOSED],"lost":[r for r in rows if r.get("stage")==LOST]}
