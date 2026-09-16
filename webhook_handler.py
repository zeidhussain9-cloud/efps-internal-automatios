"""Live WhAPI webhook boundary for Inventory Stage-1 and Leads."""
from __future__ import annotations
import json
import os
import sys

sys.path.insert(0, str(__file__).rsplit("/", 1)[0] + "/modules/efpd-lead-mgmnt/src")
sys.path.insert(0, str(__file__).rsplit("/", 1)[0] + "/modules/efps-inventory-mgmnt/src")

from shared.whatsapp_whapi.webhook import authorize_query_token, parse_delivery
from shared.whatsapp_whapi import config as whapi_config
from shared.google_sheets.client import GoogleSheetsClient
from inventory_runtime import handle as handle_inventory
from leads import normalise_phone, record_message
from lead_card import post_or_update, post_history, history_line
from shared.slack.routing import LEADS_CHANNEL


def _ok(body: dict | None = None) -> dict:
    return {"statusCode": 200, "headers": {"Content-Type": "application/json"}, "body": json.dumps(body or {"ok": True})}


def _webhook_token() -> str:
    try:
        from shared.credentials import get_secret
        raw = get_secret("efps-whapi-panel-webhook")
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            value = {"value": raw}
        if isinstance(value, dict):
            return str(value.get("token") or value.get("api_token") or value.get("EFPS_WEBHOOK_TOKEN") or value.get("value") or "")
        return str(value)
    except Exception:
        return os.getenv("EFPS_WEBHOOK_TOKEN", "")


def _authorised(event: dict) -> bool:
    return authorize_query_token(event.get("queryStringParameters") or {}, _webhook_token())


def process(payload: dict) -> dict:
    results = []
    sheets_client = GoogleSheetsClient()
    for message in parse_delivery(payload):
        try:
            if message.is_inventory_listener and not message.is_group and not message.from_me:
                results.append(handle_inventory(message, client=sheets_client))
                continue
            if message.is_group:
                results.append({"skipped": "untracked group"})
                continue
            phone = normalise_phone(message.chat_id or message.sender)
            if not phone:
                results.append({"skipped": "no usable phone number"})
                continue
            direction = "out" if message.from_me else "in"
            lead = record_message(
                phone,
                direction,
                message.body,
                message_id=message.message_id,
                sender_name="" if message.from_me else message.sender_name,
                media_reference=message.media_reference,
            )
            if lead.get("_duplicate"):
                results.append({"phone": phone, "duplicate": True})
                continue
            ts = post_or_update(lead, channel=LEADS_CHANNEL)
            if ts and not lead.get("card_ts"):
                lead["card_ts"] = ts
            post_history(lead, history_line({
                "direction": direction,
                "message_body": message.body,
                "timestamp": lead.get("last_message_at", ""),
                "has_media": message.has_media,
            }), channel=LEADS_CHANNEL)
            results.append({"phone": phone, "direction": direction, "has_media": message.has_media})
        except Exception as exc:
            results.append({"message_id": message.message_id, "error": str(exc)})
    return {"handled": len(results), "results": results}


def lambda_handler(event, context):
    if not _authorised(event):
        return {"statusCode": 401, "body": "unauthorized"}
    if not whapi_config.live_enabled():
        return _ok({"ok": True, "live": False})
    body = event.get("body") or "{}"
    if event.get("isBase64Encoded"):
        import base64
        body = base64.b64decode(body).decode()
    try:
        payload = json.loads(body)
    except (json.JSONDecodeError, TypeError):
        return _ok({"ok": True, "ignored": "unparseable body"})
    if not isinstance(payload, dict):
        return _ok({"ok": True, "ignored": "payload is not an object"})
    return _ok(process(payload))
