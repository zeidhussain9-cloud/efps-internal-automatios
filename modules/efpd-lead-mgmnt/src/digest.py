"""Lead dashboard without the deferred sessions table."""
from __future__ import annotations
import db
import leads as L
from shared.slack import SlackClient
from shared.slack.routing import LEADS_CHANNEL

DASHBOARD_PREFIX = "Leads — "

def blocks(summary: dict) -> list[dict]:
    groups=(("🔴 Waiting on you",summary["our_reply"]),("🟠 Follow up today",summary["followup_due"]),("🟣 Visits",summary["visit_due"]),("🟡 Gone quiet (3+ days)",summary["quiet"]),("🔵 Waiting for stock",summary["no_match"]))
    lines=[]
    for title,items in groups:
        if items:
            lines.append(f"*{title}* ({len(items)})")
            lines.extend(f"• {L.label(x)} — {x.get('stage',L.NEW)} · {L.age_label(x.get('last_message_at',''))}" for x in items[:8])
            if len(items)>8: lines.append(f"_…and {len(items)-8} more_")
            lines.append("")
    if not lines: lines=["Nothing needs you right now."]
    return [{"type":"section","text":{"type":"mrkdwn","text":"\n".join(lines).strip()[:2900]}},{"type":"context","elements":[{"type":"mrkdwn","text":f"{summary['live']} live · {len(summary['new'])} new · {len(summary['closed'])} closed · {len(summary['lost'])} lost"}]}]

def _existing_dashboard(slack: SlackClient) -> str:
    for message in slack.history(LEADS_CHANNEL, limit=100):
        text=str(message.get("text") or "")
        if text.startswith(DASHBOARD_PREFIX) and (message.get("subtype") == "bot_message" or message.get("bot_id")):
            return str(message.get("ts") or "")
    return ""

def run(*, client: SlackClient|None=None, _res=None) -> dict:
    slack=client or SlackClient(); L.refresh_actions(_res=_res)
    summary=L.summarise(db.all_leads(_res=_res)); text=DASHBOARD_PREFIX+f"{len(summary['our_reply'])} waiting on you"; b=blocks(summary); ts=_existing_dashboard(slack)
    if ts:
        slack.update_message(LEADS_CHANNEL,ts,text,blocks=b); return {"updated":True,"ts":ts}
    ts=slack.post_message(LEADS_CHANNEL,text,blocks=b)
    return {"updated":False,"ts":ts}
