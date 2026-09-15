"""Lead mutation audit trail. Hooked automatically by db.put_lead()."""
from __future__ import annotations
import contextlib
import contextvars
import uuid
from datetime import datetime, timezone

from . import db

AUTO = "auto"
MANUAL = "manual"
TRACKED = ["stage", "action", "next_followup_date", "customer_name", "looking_requirement",
           "budget_min", "budget_max", "preferred_localities", "interested_listings", "lost_reason"]
MAX_VALUE = 700
_actor: contextvars.ContextVar[tuple[str, str, str]] = contextvars.ContextVar("efps_lead_actor", default=("system", AUTO, ""))

@contextlib.contextmanager
def actor(who: str, *, source: str = MANUAL, reason: str = ""):
    token = _actor.set((who or "system", source, reason))
    try:
        yield
    finally:
        _actor.reset(token)

def current() -> tuple[str, str, str]:
    return _actor.get()

def _clip(value: str) -> str:
    text = str(value or "")
    return text if len(text) <= MAX_VALUE else text[:MAX_VALUE] + "…"

def diff(before: dict | None, after: dict) -> list[dict]:
    if not before:
        return [{"field": "lead", "old": "", "new": "created"}]
    changes = []
    for field in TRACKED:
        old, new = str(before.get(field, "") or ""), str(after.get(field, "") or "")
        if old != new:
            changes.append({"field": field, "old": _clip(old), "new": _clip(new)})
    return changes

def record(phone: str, changes: list[dict], *, _res=None) -> list[dict]:
    if not changes:
        return []
    who, source, reason = current()
    stamp = datetime.now(timezone.utc).isoformat()
    written = []
    for change in changes:
        item = {"phone_number": str(phone), "changed_at": f"{stamp}#{uuid.uuid4().hex[:6]}",
                "field": change["field"], "old_value": change["old"], "new_value": change["new"],
                "source": source, "actor": who}
        if reason:
            item["reason"] = reason
        try:
            db._table(db.DDB_AUDIT, _res).put_item(Item=item)
            written.append(item)
        except Exception as exc:  # noqa: BLE001
            print(f"lead audit write failed for {phone}: {exc!r}")
    return written

def history(phone: str, limit: int = 20, *, _res=None) -> list[dict]:
    try:
        return db._table(db.DDB_AUDIT, _res).query(
            KeyConditionExpression="phone_number = :p",
            ExpressionAttributeValues={":p": str(phone)},
            ScanIndexForward=False, Limit=limit).get("Items", [])
    except Exception as exc:  # noqa: BLE001
        print(f"lead audit read failed: {exc!r}")
        return []

def describe(entry: dict) -> str:
    when = str(entry.get("changed_at", "")).split("#")[0]
    try:
        dt = datetime.fromisoformat(when).astimezone(timezone.utc)
        when = dt.strftime("%-d %b %-I:%M %p")
    except (TypeError, ValueError):
        pass
    field = str(entry.get("field", ""))
    new = str(entry.get("new_value", "")) or "cleared"
    by = "you" if entry.get("source") == MANUAL else "system"
    return f"{when} — {'lead created' if field == 'lead' else field.replace('_', ' ') + ' → ' + new} ({by})"
