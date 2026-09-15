"""Lead dashboard derived view."""
from __future__ import annotations
from datetime import datetime,timezone
import config,db,leads as L,lead_card
KEY="__dashboard__"
def _table():
 import boto3;return boto3.resource("dynamodb",region_name=config.AWS_REGION).Table(config.DDB_SESSIONS)
def _load_ts():
 try:return str((_table().get_item(Key={"user_id":KEY}).get("Item") or {}).get("thread_ts") or "")
 except Exception:return ""
def _save_ts(ts):_table().put_item(Item={"user_id":KEY,"thread_ts":ts,"expires_at":int(datetime.now(timezone.utc).timestamp())+10*365*24*3600,"started_at":L.now_iso()})
def _line(lead):return f"• *{lead_card.safe_text(L.label(lead))}* — {lead.get('stage') or L.NEW} · _{L.age_label(lead.get('last_message_at',''))}_"
def _group(title,items):
 if not items:return []
 lines=[f"*{title}* ({len(items)})"]+[_line(x) for x in items[:8]]
 if len(items)>8:lines.append(f"_…and {len(items)-8} more_")
 return lines+[""]
def blocks(summary,*,_now=None):
 now=_now or datetime.now(L.IST);body=_group("Waiting on you",summary["our_reply"])+_group("Follow up today",summary["followup_due"])+_group("Visits",summary["visit_due"])+_group("Gone quiet (3+ days)",summary["quiet"])+_group("Waiting for stock",summary["no_match"])
 if not body:body=["Nothing needs you right now.",""]
 return [{"type":"header","text":{"type":"plain_text","text":f"Leads — {now.strftime('%a %-d %b')}"}},{"type":"section","text":{"type":"mrkdwn","text":"\n".join(body).strip()[:2900]}},{"type":"context","elements":[{"type":"mrkdwn","text":f"{summary['live']} live · {len(summary['new'])} new · {len(summary['closed'])} closed · {len(summary['lost'])} lost"}]}]
def refresh_board(*, _res=None,_post=None,_now=None):
 summary=L.summarise(db.all_leads(_res=_res));ts=_load_ts()
 if not ts:return {"updated":False,"reason":"no dashboard yet"}
 payload={"channel":config.LEADS_CHANNEL,"text":f"Leads — {len(summary['our_reply'])} waiting on you","blocks":blocks(summary,_now=_now)}
 lead_card._call("chat.update",dict(payload,ts=ts),_post=_post);return {"updated":True,"ts":ts,"waiting":len(summary["our_reply"])}
def run(*, _res=None,_post=None,_now=None):
 changed=L.refresh_actions(_res=_res);summary=L.summarise(db.all_leads(_res=_res));payload={"channel":config.LEADS_CHANNEL,"text":f"Leads — {len(summary['our_reply'])} waiting on you","blocks":blocks(summary,_now=_now)};ts=_load_ts()
 if ts:
  try:lead_card._call("chat.update",dict(payload,ts=ts),_post=_post);return {"updated":True,"ts":ts,"refreshed":len(changed),"waiting":len(summary["our_reply"])}
  except Exception:pass
 data=lead_card._call("chat.postMessage",payload,_post=_post);new_ts=str(data.get("ts") or "")
 if new_ts:
  _save_ts(new_ts)
  try:lead_card._call("pins.add",{"channel":config.LEADS_CHANNEL,"timestamp":new_ts},_post=_post)
  except Exception:pass
 return {"updated":False,"ts":new_ts,"refreshed":len(changed),"waiting":len(summary["our_reply"])}
