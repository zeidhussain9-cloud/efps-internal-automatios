"""Slack interactive handler for the migrated lead-management surface."""
from __future__ import annotations
import json,urllib.parse,sys
from shared.credentials import get_secret
from shared.webhook.request import body_bytes,response
from shared.slack import security
from shared.slack.client import SlackClient
sys.path.insert(0,"modules/efpd-lead-mgmnt/src")
from audit import actor,MANUAL
import db,leads as L,lead_card

def _secret():
 try:
  raw=get_secret("efps-whapi-panel-slack");v=json.loads(raw) if raw.startswith("{") else {"value":raw};return str(v.get("signing_secret") or v.get("SLACK_SIGNING_SECRET") or "")
 except Exception:return ""
def _modal(callback,phone,title,blocks):return {"type":"modal","callback_id":callback,"private_metadata":phone,"title":{"type":"plain_text","text":title},"submit":{"type":"plain_text","text":"Save"},"blocks":blocks}
def _input(block_id,label,value,placeholder,optional=True):
 e={"type":"plain_text_input","action_id":"value","placeholder":{"type":"plain_text","text":placeholder}}
 if str(value or ""):e["initial_value"]=str(value)
 return {"type":"input","block_id":block_id,"optional":optional,"label":{"type":"plain_text","text":label},"element":e}
def _open(trigger,view):return SlackClient().call("views.open",{"trigger_id":trigger,"view":view})
def _values(view):
 out={}
 for block_id,block in (view.get("state") or {}).get("values",{}).items():
  for el in block.values():out[block_id]=str(el.get("value") or "").strip()
 return out

def _action(payload):
 action=str((payload.get("actions") or [{}])[0].get("action_id") or "");phone=L.normalise_phone(str((payload.get("actions") or [{}])[0].get("value") or ""));trigger=str(payload.get("trigger_id") or "")
 if not phone:return {"ignored":"no phone"}
 if action=="chat::open":return {"ignored":"chat link"}
 if action=="stage::Lost":return _open(trigger,_modal("lead_lost",phone,"Mark as lost",[_input("reason","Why was this lead lost?","","budget too low / went elsewhere",False)]))
 if action=="followup::open":return _open(trigger,_modal("lead_followup",phone,"Set a follow-up",[_input("when","When?","","tomorrow · 3d · 1w · 5 oct · 2026-10-05",False)]))
 if action=="edit::open":
  lead=db.get_lead(phone) or {};blocks=[_input("customer_name","Name",lead.get("customer_name"),"Ramesh"),_input("looking_requirement","Looking for",lead.get("looking_requirement"),"2BHK semi-furnished"),_input("budget_min","Budget from",lead.get("budget_min"),"30000"),_input("budget_max","Budget up to",lead.get("budget_max"),"45000"),_input("preferred_localities","Preferred areas",lead.get("preferred_localities"),"Whitefield, Marathahalli"),_input("interested_listings","Properties shared",lead.get("interested_listings"),"EF-2608-K7QX")];return _open(trigger,_modal("lead_edit",phone,"Edit lead",blocks))
 if action=="history::open":
  rows=__import__("audit").history(phone,limit=20);text="\n".join(f"• {__import__('audit').describe(r)}" for r in rows) or "_No changes recorded yet._";return _open(trigger,_modal("lead_history",phone,"Lead history",[{"type":"section","text":{"type":"mrkdwn","text":text[:2900]}}]))
 user=str((payload.get("user") or {}).get("id") or "unknown")
 with actor(user,source=MANUAL):
  if action.startswith("stage::"):lead=L.set_stage(phone,action.split("::",1)[1])
  elif action=="action::nomatch":
   current=db.get_lead(phone) or {};lead=L.set_action(phone,L.NOTHING if current.get("action")==L.NO_MATCH else L.NO_MATCH)
  else:return {"ignored":action}
 ts=str((payload.get("container") or {}).get("message_ts") or lead.get("card_ts") or "");channel=str((payload.get("channel") or {}).get("id") or "C0BTM6PH55L")
 SlackClient().update_message(channel,ts,lead_card.headline(lead),blocks=lead_card.blocks(lead)) if ts else lead_card.post_or_update(lead,channel=channel)
 return {"ok":True}

def _submission(payload):
 view=payload.get("view") or {};cb=str(view.get("callback_id") or "");phone=L.normalise_phone(str(view.get("private_metadata") or ""));vals=_values(view);user=str((payload.get("user") or {}).get("id") or "unknown")
 with actor(user,source=MANUAL):
  if cb=="lead_lost":lead=L.set_stage(phone,L.LOST,reason=vals.get("reason",""))
  elif cb=="lead_followup":
   try:lead=L.set_followup(phone,vals.get("when",""))
   except L.LeadError as exc:return {"response_action":"errors","errors":{"when":str(exc)[:150]}}
  elif cb=="lead_edit":
   updates={k:v for k,v in vals.items() if v};
   for money in ("budget_min","budget_max"):
    if money in updates:
     digits="".join(c for c in updates[money] if c.isdigit())
     if not digits:return {"response_action":"errors","errors":{money:"numbers only, e.g. 45000"}}
     updates[money]=int(digits)
   lead=L.set_fields(phone,updates) if updates else (db.get_lead(phone) or {})
  else:return {}
 lead_card.post_or_update(lead);return {}

def lambda_handler(event,context):
 raw=body_bytes(event);headers={str(k).lower():str(v) for k,v in (event.get("headers") or {}).items()}
 if not security.verify_signature(raw,headers.get("x-slack-request-timestamp",""),headers.get("x-slack-signature",""),signing_secret=_secret()):return response("unauthorized",401,"text/plain")
 form={k:v[0] for k,v in urllib.parse.parse_qs(raw.decode()).items()};payload=json.loads(form.get("payload","{}"));kind=payload.get("type")
 if kind=="block_actions":_action(payload)
 elif kind=="view_submission":
  result=_submission(payload)
  if result:return response(result)
 return response("")
