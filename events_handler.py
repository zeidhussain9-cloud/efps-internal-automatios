"""Slack Events API endpoint for migrated photo/verification workflows."""
from __future__ import annotations
import json,sys
from shared.credentials import get_secret
from shared.webhook.request import body_bytes,response
from shared.slack import security
from shared.slack.client import SlackClient
sys.path.insert(0,"modules/efps-inventory-mgmnt")
sys.path.insert(0,"shared/slack")
from src.slack_ops import save_photos,verify_answer,verify_submit,load,clear,photo_move,verify_start
import bugs
THREAD_WORDS={"done":"done","save":"done","saved":"done","submit":"submit","ok":"done","skip":"skip","next":"next","exit":"exit","stop":"exit","cancel":"exit"}
def _secret():
 try:
  raw=get_secret("efps-whapi-panel-slack");v=json.loads(raw) if raw.startswith("{") else {"value":raw};return str(v.get("signing_secret") or v.get("SLACK_SIGNING_SECRET") or "")
 except Exception:return ""
def _verified(event,raw):
 h={str(k).lower():str(v) for k,v in (event.get("headers") or {}).items()};return security.verify_signature(raw,h.get("x-slack-request-timestamp",""),h.get("x-slack-signature",""),signing_secret=_secret())
def lambda_handler(event,context):
 if isinstance(event,dict) and event.get("internal")=="save_photos":return {"ok":True,"detail":save_photos(event.get("user_id",""),event.get("channel_id",""))[:200]}
 raw=body_bytes(event)
 try:payload=json.loads(raw.decode())
 except (ValueError,UnicodeDecodeError):return response("")
 if isinstance(payload,dict) and payload.get("type")=="url_verification":return response(str(payload.get("challenge","")),200,"text/plain")
 if not _verified(event,raw):return response("unauthorized",401,"text/plain")
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
