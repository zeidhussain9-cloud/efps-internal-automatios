"""Canonical WhAPI webhook entry point for the new runtime.

WhAPI parsing and authentication are shared technical capabilities. Inventory
and Lead behavior stay in their owning modules.
"""
from __future__ import annotations
import json,os,sys
from shared.webhook.request import json_body,response
from shared.whatsapp_whapi import webhook as whapi_webhook
from shared.whatsapp_whapi import config as whapi_config
from shared.credentials import get_secret
from shared.slack import crash_report
sys.path.insert(0,"modules/efps-inventory-mgmnt/src")
sys.path.insert(0,"modules/efpd-lead-mgmnt/src")
from inventory_runtime import handle as handle_inventory
from leads import normalise_phone,record_message
from lead_card import post_or_update,post_history,history_line

def _webhook_token()->str:
    try:
        raw=get_secret("efps-whapi-panel-webhook")
        try:value=json.loads(raw)
        except json.JSONDecodeError:value={"value":raw}
        if isinstance(value,dict):
            return str(value.get("token") or value.get("api_token") or value.get("EFPS_WEBHOOK_TOKEN") or value.get("value") or "")
        return str(value)
    except Exception:return os.getenv("EFPS_WEBHOOK_TOKEN","")

def _process(payload:dict)->dict:
    results=[]
    for message in whapi_webhook.parse_delivery(payload):
        try:
            if message.is_inventory_listener:
                results.append(handle_inventory(message));continue
            if message.is_group:
                results.append({"skipped":"untracked group"});continue
            phone=normalise_phone(message.chat_id or message.sender)
            if not phone:results.append({"skipped":"no usable phone number"});continue
            direction="out" if message.from_me else "in"
            lead=record_message(phone,direction,message.body,message_id=message.message_id,sender_name="" if message.from_me else message.sender_name)
            if lead.get("_duplicate"):results.append({"phone":phone,"duplicate":True});continue
            ts=post_or_update(lead)
            if ts and not lead.get("card_ts"):lead["card_ts"]=ts
            post_history(lead,history_line({"direction":direction,"message_body":message.body,"timestamp":lead.get("last_message_at", ""),"has_media":message.has_media}))
            results.append({"phone":phone,"created":bool(lead.get("_created")),"direction":direction})
        except Exception as exc:
            crash_report.report("webhook",exc,reference=message.message_id);results.append({"error":str(exc)})
    return {"handled":len(results),"results":results}

def lambda_handler(event,context):
    if not whapi_config.live_enabled():return response({"ok":True,"live":False})
    if not whapi_webhook.authorize_query_token(event.get("queryStringParameters") or {},_webhook_token()):return response("unauthorized",401,"text/plain")
    payload=event.get("__efps_async__") if isinstance(event.get("__efps_async__"),dict) else json_body(event)
    if payload is None:return response({"ok":True,"ignored":"unparseable body"})
    return response(_process(payload))
