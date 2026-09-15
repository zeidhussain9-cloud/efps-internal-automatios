"""Slack slash-command HTTP/Lambda boundary."""
from __future__ import annotations
import json
from urllib.parse import parse_qs
from shared.slack.security import verify_signature
import commands

def lambda_handler(event, context):
    body=event.get("body") or ""; raw=body.encode()
    if event.get("isBase64Encoded"):
        import base64; raw=base64.b64decode(body); body=raw.decode()
    headers={str(k).lower():str(v) for k,v in (event.get("headers") or {}).items()}
    if not verify_signature(raw,headers.get("x-slack-request-timestamp", ""),headers.get("x-slack-signature", "")):
        return {"statusCode":401,"body":"invalid signature"}
    form={k:v[0] for k,v in parse_qs(body).items() if v}
    if form.get("command") != "/efps": return {"statusCode":200,"body":json.dumps({"response_type":"ephemeral","text":"Unknown Slack command."})}
    try: response=commands.handle(form.get("text",""),form.get("user_id",""),form.get("channel_id",""))
    except Exception as exc:
        print(f"command failed: {exc!r}"); response={"response_type":"ephemeral","text":"Command failed safely; check runtime logs."}
    return {"statusCode":200,"headers":{"Content-Type":"application/json"},"body":json.dumps(response)}
