"""Slack lead card rendering and delivery."""
from __future__ import annotations
import json
import re
from typing import Any
from . import db, leads as L
from shared.slack import SlackClient


def safe_text(text: str) -> str:
    out = str(text or "")
    out = out.replace("<!channel>", "@channel").replace("<!here>", "@here").replace("<!everyone>", "@everyone")
    return re.sub(r"<@([A-Z0-9]+)(\|[^>]*)?>", r"@\1", out)

def _requirement(lead: dict) -> str:
    bits=[]
    if lead.get("looking_requirement"): bits.append(str(lead["looking_requirement"]))
    lo,hi=lead.get("budget_min"),lead.get("budget_max")
    if lo and hi: bits.append(f"₹{int(lo):,}–₹{int(hi):,}")
    elif hi: bits.append(f"under ₹{int(hi):,}")
    elif lo: bits.append(f"above ₹{int(lo):,}")
    if lead.get("preferred_localities"): bits.append(str(lead["preferred_localities"]))
    return " · ".join(bits) or "_not captured yet_"

def headline(lead: dict) -> str:
    stage=lead.get("stage") or L.NEW; action=lead.get("action") or L.NOTHING
    return f"{L.ACTION_EMOJI.get(action,'')} {safe_text(L.label(lead))} — {L.STAGE_EMOJI.get(stage,'')} {stage} · {action}"

def chat_url(lead: dict) -> str:
    phone=L.normalise_phone(lead.get("phone_number", "")); return f"https://wa.me/{phone}" if phone else ""

def buttons(lead: dict) -> list[dict]:
    phone=lead.get("phone_number",""); stage=lead.get("stage"); action=lead.get("action")
    stage_buttons=[]
    for label in L.CARD_BUTTONS:
        if label == stage: continue
        item={"type":"button","text":{"type":"plain_text","text":label},"action_id":f"stage::{label}","value":phone}
        if label==L.LOST: item["style"]="danger"
        elif label==L.CLOSED: item["style"]="primary"
        stage_buttons.append(item)
    extras=[
        {"type":"button","text":{"type":"plain_text","text":"Un-match" if action==L.NO_MATCH else "No match"},"action_id":"action::nomatch","value":phone},
        {"type":"button","text":{"type":"plain_text","text":"Follow up"},"action_id":"followup::open","value":phone},
        {"type":"button","text":{"type":"plain_text","text":"Edit"},"action_id":"edit::open","value":phone},
        {"type":"button","text":{"type":"plain_text","text":"History"},"action_id":"history::open","value":phone},
    ]
    chunks=[stage_buttons[:5], stage_buttons[5:]+extras[:2], extras[2:3]]
    return [{"type":"actions","elements":c} for c in chunks if c]

def blocks(lead: dict) -> list[dict]:
    name=safe_text(L.label(lead)); shown=L.display_phone(lead.get("phone_number", "")); stage=lead.get("stage") or L.NEW; action=lead.get("action") or L.NOTHING
    title=name if name==shown else f"{name} · {shown}"
    unread=int(lead.get("unread_count") or 0)
    if unread: title += f" ({unread} unread)"
    out=[
        {"type":"header","text":{"type":"plain_text","text":title[:150]}},
        {"type":"section","fields":[{"type":"mrkdwn","text":f"*Stage*\n{L.STAGE_EMOJI.get(stage,'')} {stage}"},{"type":"mrkdwn","text":f"*Action*\n{L.ACTION_EMOJI.get(action,'')} {action}"},],"accessory":{"type":"button","text":{"type":"plain_text","text":"💬 Open chat"},"url":chat_url(lead),"action_id":"chat::open"}},
        {"type":"section","text":{"type":"mrkdwn","text":f"*Looking for*\n{_requirement(lead)}"}},
    ]
    last=str(lead.get("last_message") or "").strip()
    if last:
        who="They said" if lead.get("last_direction")=="in" else "We said"
        out.append({"type":"section","text":{"type":"mrkdwn","text":f"*{who}* · _{L.age_label(lead.get('last_message_at',''))}_\n>{safe_text(last[:297]+'…' if len(last)>300 else last)}"}})
    meta=[]
    if lead.get("next_followup_date"): meta.append(f"follow up {lead['next_followup_date']}")
    if lead.get("interested_listings"): meta.append(f"shared: {lead['interested_listings']}")
    if lead.get("lost_reason") and stage==L.LOST: meta.append(f"lost: {lead['lost_reason']}")
    if meta: out.append({"type":"context","elements":[{"type":"mrkdwn","text":safe_text(' · '.join(meta))}]})
    out.extend(buttons(lead)); return out

def history_line(interaction: dict) -> str:
    arrow="⬅️" if interaction.get("direction")=="in" else "➡️"; who="them" if interaction.get("direction")=="in" else "us"; body=safe_text(str(interaction.get("message_body") or "").strip() or "_(no text)_")
    if interaction.get("has_media"): body="📷 "+body
    return f"{arrow} *{who}* · _{L.ist_label(interaction.get('timestamp',''))}_\n{body}"

def post_or_update(lead: dict, *, channel: str = "C0BTM6PH55L", client: SlackClient | None = None, _res=None) -> str:
    slack=client or SlackClient(); payload={"channel":channel,"text":headline(lead),"blocks":blocks(lead)}; existing=str(lead.get("card_ts") or "")
    if existing:
        try: slack.update_message(channel=channel, ts=existing, text=payload["text"], blocks=payload["blocks"]); return existing
        except Exception: pass
    data=slack.post_message(channel=channel,text=payload["text"],blocks=payload["blocks"]); ts=str(data.get("ts") or "")
    if ts: db.set_card_ts(lead["phone_number"],ts,_res=_res)
    return ts

def post_history(lead: dict, text: str, *, channel: str = "C0BTM6PH55L", client: SlackClient | None = None) -> None:
    ts=str(lead.get("card_ts") or "")
    if ts: (client or SlackClient()).post_message(channel=channel,text=text,thread_ts=ts)
