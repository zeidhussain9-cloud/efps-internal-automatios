"""Live WhAPI webhook boundary for inventory and leads."""
from __future__ import annotations
import json
import os
import sys
import traceback

sys.path.insert(0, str(__file__).rsplit("/",1)[0] + "/modules/efpd-lead-mgmnt/src")
sys.path.insert(0, str(__file__).rsplit("/",1)[0] + "/modules/efps-inventory-mgmnt/src")

from shared.whatsapp_whapi.webhook import authorize_query_token, parse_delivery
from shared.whatsapp_whapi import config as whapi_config
from shared.google_sheets.client import GoogleSheetsClient
from leads import record_message
from lead_card import post_or_update, post_history, history_line
from shared.slack.routing import LEADS_CHANNEL


def _ok(body: dict | None = None) -> dict:
    return {"statusCode": 200, "headers": {"Content-Type": "application/json"}, "body": json.dumps(body or {"ok": True})}

def _authorised(event: dict) -> bool:
    return authorize_query_token(event.get("queryStringParameters"), os.getenv("EFPS_WEBHOOK_TOKEN", ""))

def handle_lead(message) -> dict:
    if message.is_group:
        return {"skipped":"untracked group"}
    counterparty = message.chat_id if not message.is_group else message.sender
    phone = record_message(counterparty, "out" if message.from_me else "in", message.body,
                           message_id=message.message_id, sender_name="" if message.from_me else message.sender_name,
                           group_name="" if not message.is_group else message.chat_id)
    if phone.get("_duplicate"):
        return {"phone": phone.get("phone_number"), "duplicate": True}
    try:
        post_or_update(phone, channel=LEADS_CHANNEL)
        post_history(phone, history_line({"direction":"out" if message.from_me else "in",
                                          "message_body":message.body,"timestamp":phone.get("last_message_at",""),
                                          "has_media":message.has_media}), channel=LEADS_CHANNEL)
    except Exception as exc:  # noqa: BLE001
        print(f"lead Slack card failed: {exc!r}")
    return {"phone": phone.get("phone_number"), "direction": "out" if message.from_me else "in"}

def process(payload: dict) -> dict:
    messages=parse_delivery(payload); results=[]; sheets_client=GoogleSheetsClient()
    for message in messages:
        try:
            if message.is_inventory_listener and not message.is_group and not message.from_me:
                from inventory_runtime import handle as inventory_handle
                results.append(inventory_handle(message, client=sheets_client))
            else:
                results.append(handle_lead(message))
        except Exception as exc:  # noqa: BLE001
            traceback.print_exc()
            print(f"webhook message {message.message_id} failed: {exc!r}")
            results.append({"message_id":message.message_id,"error":str(exc)})
    return {"handled":len(results),"results":results}

def lambda_handler(event, context):
    if not _authorised(event): return {"statusCode":401,"body":"unauthorized"}
    if not whapi_config.live_enabled(): return _ok({"ok":True,"live":False})
    body=event.get("body") or "{}"
    if event.get("isBase64Encoded"):
        import base64; body=base64.b64decode(body).decode()
    try: payload=json.loads(body)
    except (json.JSONDecodeError,TypeError): return _ok({"ok":True,"ignored":"unparseable body"})
    if not isinstance(payload,dict): return _ok({"ok":True,"ignored":"payload is not an object"})
    return _ok(process(payload))
