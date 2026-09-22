"""Slack slash-command HTTP/Lambda boundary."""
from __future__ import annotations
import json
from urllib.parse import parse_qs
from shared.slack.security import verify_signature
import commands

def lambda_handler(event, context):
    # Async self-invocation: EFPSCommands invokes itself with InvocationType=Event
    # to do slow work outside the 3-second Slack deadline.  The async payload is
    # sent as the raw Lambda event dict (not wrapped in API Gateway body).
    if isinstance(event, dict) and "_efps_async" in event:
        commands.handle_async(event)
        return {"statusCode": 200, "body": ""}

    # Normal Slack slash-command path (API Gateway wraps the body as a string)
    body=event.get("body") or ""; raw=body.encode()
    if event.get("isBase64Encoded"):
        import base64; raw=base64.b64decode(body); body=raw.decode()
    headers={str(k).lower():str(v) for k,v in (event.get("headers") or {}).items()}
    if not verify_signature(raw,headers.get("x-slack-request-timestamp", ""),headers.get("x-slack-signature", "")):
        return {"statusCode":401,"body":"invalid signature"}
    form={k:v[0] for k,v in parse_qs(body).items() if v}
    if form.get("command") != "/efps": return {"statusCode":200,"body":json.dumps({"response_type":"ephemeral","text":"Unknown Slack command."})}
    response_url = form.get("response_url", "")
    try: response=commands.handle(form.get("text",""),form.get("user_id",""),form.get("channel_id",""),response_url=response_url)
    except Exception as exc:
        print(f"command failed: {exc!r}"); response={"response_type":"ephemeral","text":"Command failed safely; check runtime logs."}
    # Normalise: commands.handle() returns a plain string; wrap it in the
    # Slack payload envelope before JSON-serialising so Slack renders it
    # correctly.  Dict responses (e.g. error fallback above) pass through as-is.
    if isinstance(response, str):
        response = {"response_type": "ephemeral", "text": response}
    return {"statusCode":200,"headers":{"Content-Type":"application/json"},"body":json.dumps(response, ensure_ascii=False)}
