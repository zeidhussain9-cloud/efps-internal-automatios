"""Slack slash-command Lambda entry point."""
from __future__ import annotations
import urllib.parse,sys
from shared.webhook.request import response,body_bytes
from shared.slack import security,crash_report
sys.path.insert(0,"modules/efps-inventory-mgmnt/src")
sys.path.insert(0,"modules/efpd-lead-mgmnt/src")
import commands

def lambda_handler(event,context):
    raw=body_bytes(event);headers={str(k).lower():str(v) for k,v in (event.get("headers") or {}).items()}
    if not security.verify_signature(raw,headers.get("x-slack-request-timestamp",""),headers.get("x-slack-signature","")):
        return response("unauthorized",401,"text/plain")
    try:
        form={k:v[0] for k,v in urllib.parse.parse_qs(raw.decode()).items()}
        answer=commands.handle(form.get("text",""),user_id=form.get("user_id",""),channel_id=form.get("channel_id",""))
        return response({"response_type":"in_channel","text":answer})
    except Exception as exc:
        crash_report.report("slack_command",exc,reference=form.get("command","") if 'form' in locals() else "")
        return response({"response_type":"ephemeral","text":"EFPS could not process that command. The error was logged for review."})
