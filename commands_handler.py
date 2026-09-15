"""Slack slash-command Lambda entry point."""
from __future__ import annotations
import base64,hashlib,hmac,json,time,urllib.parse,sys
from shared.credentials import get_secret
from shared.webhook.request import response,body_bytes
from shared.slack import security
from shared.slack import crash_report
sys.path.insert(0,"modules/efps-inventory-mgmnt/src")
sys.path.insert(0,"modules/efpd-lead-mgmnt/src")
import commands

def _signing_secret():
    try:
        raw=get_secret("efps-whapi-panel-slack")
        try:v=json.loads(raw)
        except json.JSONDecodeError:v={"value":raw}
        if isinstance(v,dict):return str(v.get("signing_secret") or v.get("SLACK_SIGNING_SECRET") or "")
        return ""
    except Exception:return ""

def lambda_handler(event,context):
    raw=body_bytes(event);headers={str(k).lower():str(v) for k,v in (event.get("headers") or {}).items()}
    if not security.verify_signature(raw,headers.get("x-slack-request-timestamp","") ,headers.get("x-slack-signature",""),signing_secret=_signing_secret()):return response("unauthorized",401,"text/plain")
    form={k:v[0] for k,v in urllib.parse.parse_qs(raw.decode()).items()};answer=commands.handle(form.get("text",""),user_id=form.get("user_id",""),channel_id=form.get("channel_id",""));return response({"response_type":"in_channel","text":answer})
