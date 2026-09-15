"""Slack Events API endpoint for migrated photo/verification workflows."""
from __future__ import annotations
import json,sys
from shared.webhook.request import body_bytes,response
from shared.slack import security,crash_report
from shared.slack.client import SlackClient
sys.path.insert(0,"modules/efps-inventory-mgmnt")
sys.path.insert(0,"shared/slack")
sys.path.insert(0,"modules/efpd-lead-mgmnt/src")
from src.slack_ops import save_photos,verify_answer,verify_submit,load,clear,photo_move,verify_start
import bugs,db
THREAD_WORDS={"done":"done","save":"done","saved":"done","submit":"submit","ok":"done","skip":"skip","next":"next","exit":"exit","stop":"exit","cancel":"exit"}
def lambda_handler(event,context):
 raw=body_bytes(event)
 try:payload=json.loads(raw.decode())
 except (ValueError,UnicodeDecodeError):return response("")
 if isinstance(payload,dict) and payload.get("type")=="url_verification":return response(str(payload.get("challenge","")),200,"text/plain")
 headers={str(k).lower():str(v) for k,v in (event.get("headers") or {}).items()}
 if not security.verify_signature(raw,headers.get("x-slack-request-timestamp",""),headers.get("x-slack-signature","")):
  return response("unauthorized",401,"text/plain")
 event_id=str(payload.get("event_id") or "") if isinstance(payload,dict) else ""
 try:
  if event_id and not db.claim_event(event_id):return response("")
  inner=payload.get("event") or {}
  if inner.get("type")=="message" and not inner.get("bot_id") and not inner.get("subtype"):
   user=str(inner.get("user") or "");channel=str(inner.get("channel") or "");thread=str(inner.get("thread_ts") or "");text=str(inner.get("text") or "").strip();word=THREAD_WORDS.get(text.strip(".!").lower(),"")
   if user and bugs.in_progress(user):
    reply=bugs.answer(user,text)
    if reply:SlackClient().post_message(channel,reply,thread_ts=thread or None)
    return response("")
   vs=load(user,"verify") if user else None;ps=load(user,"photos") if user else None;session=vs or ps
   if session and (not thread or session.thread_ts==thread) and word:
    if session.kind=="photos":
     if word=="done":reply=save_photos(user,channel)
     elif word in {"next","skip"}:_,reply=photo_move(user,word)
     else:clear(user,"photos");reply="Photo session closed."
    else:
     if word=="submit":reply=verify_submit(user)
     elif word in {"next","skip"}:_,reply=verify_start(user)
     else:clear(user,"verify");reply="Verification session closed."
    if reply:SlackClient().post_message(channel,reply,thread_ts=thread or None)
    return response("")
   if vs and vs.thread_ts and thread==vs.thread_ts and text:
    reply=verify_answer(user,text);SlackClient().post_message(channel,reply,thread_ts=thread);return response("")
  return response("")
 except Exception as exc:
  crash_report.report("slack_events",exc,reference=event_id)
  return response("")
