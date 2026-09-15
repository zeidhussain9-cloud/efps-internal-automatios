"""Slack interactive actions for the lead CRM card."""
from __future__ import annotations
import json
from urllib.parse import parse_qs
import sys
from shared.slack import SlackClient
from shared.slack.security import verify_signature
from shared.slack.routing import LEADS_CHANNEL
sys.path.insert(0,"modules/efpd-lead-mgmnt/src")
import audit, db, leads as L
from lead_card import post_or_update, history_line

def _value(action): return str(action.get("value") or "").strip()
def _respond(body:str): return {"statusCode":200,"headers":{"Content-Type":"application/json"},"body":body}
def _modal_view(kind:str, phone:str)->dict:
    if kind=="followup":
        return {"type":"modal","callback_id":"lead_followup","private_metadata":phone,"title":{"type":"plain_text","text":"Follow up"},"submit":{"type":"plain_text","text":"Save"},"close":{"type":"plain_text","text":"Cancel"},"blocks":[{"type":"input","block_id":"date","label":{"type":"plain_text","text":"Date"},"element":{"type":"plain_text_input","action_id":"value","placeholder":{"type":"plain_text","text":"today, tomorrow, 5 Oct, 2026-10-05"}}}]}
    return {"type":"modal","callback_id":"lead_edit","private_metadata":phone,"title":{"type":"plain_text","text":"Edit lead"},"submit":{"type":"plain_text","text":"Save"},"close":{"type":"plain_text","text":"Cancel"},"blocks":[{"type":"input","block_id":"customer_name","optional":True,"label":{"type":"plain_text","text":"Customer name"},"element":{"type":"plain_text_input","action_id":"value"}},{"type":"input","block_id":"looking_requirement","optional":True,"label":{"type":"plain_text","text":"Requirement"},"element":{"type":"plain_text_input","action_id":"value"}},{"type":"input","block_id":"budget_min","optional":True,"label":{"type":"plain_text","text":"Budget min"},"element":{"type":"plain_text_input","action_id":"value"}},{"type":"input","block_id":"budget_max","optional":True,"label":{"type":"plain_text","text":"Budget max"},"element":{"type":"plain_text_input","action_id":"value"}},{"type":"input","block_id":"preferred_localities","optional":True,"label":{"type":"plain_text","text":"Preferred localities"},"element":{"type":"plain_text_input","action_id":"value"}},{"type":"input","block_id":"interested_listings","optional":True,"label":{"type":"plain_text","text":"Interested listings"},"element":{"type":"plain_text_input","action_id":"value"}}]}

def lambda_handler(event,context):
    body=event.get("body") or "";raw=body.encode()
    if event.get("isBase64Encoded"):
        import base64;raw=base64.b64decode(body);body=raw.decode()
    headers={str(k).lower():str(v) for k,v in (event.get("headers") or {}).items()}
    if not verify_signature(raw,headers.get("x-slack-request-timestamp",""),headers.get("x-slack-signature","")):return _respond("invalid signature")
    form={k:v[0] for k,v in parse_qs(body).items() if v};payload=json.loads(form.get("payload","{}"));ptype=payload.get("type","");slack=SlackClient()
    if ptype=="block_actions":
        action=(payload.get("actions") or [{}])[0];aid=str(action.get("action_id") or "");phone=_value(action);user=str((payload.get("user") or {}).get("id") or "")
        try:
            if aid.startswith("stage::"):
                with audit.actor(user,source=audit.MANUAL):lead=L.set_stage(phone,aid.split("::",1)[1])
                post_or_update(lead,client=slack);return _respond("")
            if aid=="action::nomatch":
                current=db.get_lead(L.normalise_phone(phone)) or {}
                target=L.NOTHING if current.get("action")==L.NO_MATCH else L.NO_MATCH
                with audit.actor(user,source=audit.MANUAL):lead=L.set_action(phone,target)
                post_or_update(lead,client=slack);return _respond("")
            if aid=="followup::open":
                slack.call("views.open",{"trigger_id":payload.get("trigger_id"),"view":_modal_view("followup",phone)});return _respond("")
            if aid=="edit::open":
                slack.call("views.open",{"trigger_id":payload.get("trigger_id"),"view":_modal_view("edit",phone)});return _respond("")
            if aid=="history::open":
                lead=db.get_lead(L.normalise_phone(phone)) or {};items=db.lead_history(L.normalise_phone(phone),limit=50)
                post_or_update(lead,client=slack)
                for item in items:slack.post_message(LEADS_CHANNEL,history_line(item),thread_ts=lead.get("card_ts"))
                return _respond("")
            if aid=="chat::open":return _respond("")
        except Exception as exc:print(f"interactive action failed: {exc!r}")
        return _respond("")
    if ptype=="view_submission":
        view=payload.get("view") or {};cb=view.get("callback_id");phone=str(view.get("private_metadata") or "");values=view.get("state",{}).get("values",{});user=str((payload.get("user") or {}).get("id") or "")
        try:
            if cb=="lead_followup":
                value=str(values.get("date",{}).get("value",{}).get("value") or "");
                with audit.actor(user,source=audit.MANUAL):lead=L.set_followup(phone,value)
            elif cb=="lead_edit":
                updates={block:str(data.get("value") or "").strip() for block,data in ((bid,(next(iter(actions.values()))) if actions else {}) for bid,actions in values.items()) if block in {"customer_name","looking_requirement","budget_min","budget_max","preferred_localities","interested_listings"} and data.get("value") is not None};
                with audit.actor(user,source=audit.MANUAL):lead=L.set_fields(phone,updates)
            else:return _respond(json.dumps({"response_action":"clear"}))
            post_or_update(lead,client=slack);return _respond(json.dumps({"response_action":"clear"}))
        except Exception as exc:
            print(f"interactive submission failed: {exc!r}");return _respond(json.dumps({"response_action":"errors","errors":{"date":"Could not save. Check the format."}}) if cb=="lead_followup" else json.dumps({"response_action":"errors","errors":{"customer_name":"Could not save."}}))
    return _respond("")
