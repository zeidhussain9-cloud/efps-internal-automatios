"""Live WhAPI webhook boundary for inventory and leads."""
from __future__ import annotations
import json
import os
import sys
import traceback
from datetime import datetime, timezone
from urllib.request import Request, urlopen

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


def _phone_from_chat(message) -> str:
    raw = str(message.chat_id or message.sender or "")
    return "".join(ch for ch in raw.split("@")[0] if ch.isdigit())

def forward_to_crm(message) -> dict:
    url = os.getenv("CRM_WEBHOOK_URL", "").strip()
    token = os.getenv("CRM_WEBHOOK_TOKEN", "").strip()
    phone = _phone_from_chat(message)
    if not url or not token or not phone:
        return {"forwarded": False, "reason": "CRM webhook configuration incomplete"}
    try:
        ts = message.timestamp
        if isinstance(ts, (int, float)):
            message_at = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
        else:
            message_at = str(ts or "")
        payload = {
            "source_number": "919148338801",
            "phone_number": phone,
            "provider_message_id": message.message_id,
            "direction": "Outgoing" if message.from_me else "Incoming",
            "message_type": message.message_type,
            "body": message.body,
            "sender_name": message.sender_name or None,
            "media_urls": [message.media_reference] if message.media_reference else [],
            "message_at": message_at,
        }
        request = Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type":"application/json","x-crm-webhook-token":token}, method="POST")
        with urlopen(request, timeout=3) as response:
            data = json.loads(response.read().decode("utf-8") or "{}")
        return {"forwarded": True, **data}
    except Exception as exc:
        print(f"CRM webhook forwarding failed for {message.message_id}: {exc!r}")
        return {"forwarded": False, "reason": "CRM webhook request failed"}

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
                lead_result = handle_lead(message)
                crm_result = forward_to_crm(message)
                results.append({**lead_result, "crm": crm_result})
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
