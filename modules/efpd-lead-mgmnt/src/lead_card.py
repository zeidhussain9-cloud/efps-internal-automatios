"""Slack lead card view and delivery."""
from __future__ import annotations
import re
import config,db,leads as L
from shared.slack.client import SlackClient
class CardError(RuntimeError):pass
def safe_text(text):
 out=str(text or "")
 for a,b in (("<!channel>","@channel"),("<!here>","@here"),("<!everyone>","@everyone")):out=out.replace(a,b)
 return re.sub(r"<@([A-Z0-9]+)(\|[^>]*)?>",r"@\1",out)
def chat_url(lead):
 p=L.normalise_phone(lead.get("phone_number",""));return f"https://wa.me/{p}" if p else ""
def _requirement_line(lead):
 bits=[]
 if lead.get("looking_requirement"):bits.append(str(lead["looking_requirement"]))
 lo,hi=lead.get("budget_min"),lead.get("budget_max")
 if lo and hi:bits.append(f"₹{int(lo):,}–₹{int(hi):,}")
 elif hi:bits.append(f"under ₹{int(hi):,}")
 elif lo:bits.append(f"above ₹{int(lo):,}")
 if lead.get("preferred_localities"):bits.append(str(lead["preferred_localities"]))
 return " · ".join(bits) or "_not captured yet_"
def headline(lead):
 s=lead.get("stage") or L.NEW;a=lead.get("action") or L.NOTHING;return f"{L.ACTION_EMOJI.get(a,'')} {safe_text(L.label(lead))} — {L.STAGE_EMOJI.get(s,'')} {s} · {a}"
def blocks(lead):
 phone=lead.get("phone_number","");name=safe_text(L.label(lead));stage=lead.get("stage") or L.NEW;action=lead.get("action") or L.NOTHING
 title=f"{name} · {L.display_phone(phone)}" if name!=L.display_phone(phone) else name
 out=[{"type":"header","text":{"type":"plain_text","text":title[:150]}},{"type":"section","fields":[{"type":"mrkdwn","text":f"*Stage*\n{L.STAGE_EMOJI.get(stage,'')} {stage}"},{"type":"mrkdwn","text":f"*Action*\n{L.ACTION_EMOJI.get(action,'')} {action}"}]},{"type":"section","text":{"type":"mrkdwn","text":f"*Looking for*\n{_requirement_line(lead)}"}}]
 link=chat_url(lead)
 if link:out[1]["accessory"]={"type":"button","text":{"type":"plain_text","text":"Open chat"},"url":link,"action_id":"chat::open"}
 last=str(lead.get("last_message") or "").strip()
 if last:
  who="They said" if lead.get("last_direction")=="in" else "We said";out.append({"type":"section","text":{"type":"mrkdwn","text":f"*{who}* · _{L.age_label(lead.get('last_message_at',''))}_\n>{safe_text(last[:300])}"}})
 rows=[];stage_buttons=[]
 for label in L.CARD_BUTTONS:
  if label==stage:continue
  b={"type":"button","text":{"type":"plain_text","text":label},"action_id":f"stage::{label}","value":phone}
  if label==L.LOST:b["style"]="danger"
  elif label==L.CLOSED:b["style"]="primary"
  stage_buttons.append(b)
 extra=[{"type":"button","text":{"type":"plain_text","text":"Un-match" if action==L.NO_MATCH else "No match"},"action_id":"action::nomatch","value":phone},{"type":"button","text":{"type":"plain_text","text":"Follow up"},"action_id":"followup::open","value":phone},{"type":"button","text":{"type":"plain_text","text":"Edit"},"action_id":"edit::open","value":phone}]
 for chunk in (stage_buttons[:5],stage_buttons[5:]+extra,[{"type":"button","text":{"type":"plain_text","text":"History"},"action_id":"history::open","value":phone}]):
  if chunk:
   if len(chunk)>5:raise CardError("Slack action row exceeds five buttons")
   rows.append({"type":"actions","elements":chunk})
 out.extend(rows);return out
def post_or_update(lead,*,channel=None,_post=None,_save_ts=None,_res=None):
 c=channel or config.LEADS_CHANNEL;payload={"channel":c,"text":headline(lead),"blocks":blocks(lead)};existing=str(lead.get("card_ts") or "")
 try:
  client=SlackClient()
  if existing:client.update_message(c,existing,payload["text"],blocks=payload["blocks"]);return existing
  ts=client.post_message(c,payload["text"],blocks=payload["blocks"])
 except Exception as exc:
  if _post:
   if existing:
    _post("chat.update",dict(payload,ts=existing));return existing
   ts=str((_post("chat.postMessage",payload) or {}).get("ts") or "")
  else:raise CardError(str(exc)) from exc
 if ts:
  if _save_ts:_save_ts(lead.get("phone_number",""),ts)
  else:db.set_card_ts(lead.get("phone_number",""),ts,_res=_res)
 return ts
def post_history(lead,text,*,channel=None,_post=None):
 ts=str(lead.get("card_ts") or "");
 if not ts:return
 c=channel or config.LEADS_CHANNEL
 if _post:_post("chat.postMessage",{"channel":c,"thread_ts":ts,"text":text})
 else:SlackClient().post_message(c,text,thread_ts=ts)
def history_line(interaction):
 who="them" if interaction.get("direction")=="in" else "us";body=str(interaction.get("message_body") or "").strip() or "_(no text)_";return f"*{who}* · _{L.ist_label(interaction.get('timestamp',''))}_\n{body}"
def _call(method,payload,*,_post=None):return _post(method,payload) if _post else SlackClient().call(method,payload)
