"""Lead-domain DynamoDB access. Inventory does not use these tables."""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from typing import Any

AWS_REGION = "us-east-1"
DDB_LEADS = "efps-leads"
DDB_INTERACTIONS = "efps-interactions"
DDB_AUDIT = "efps-lead-audit"

TABLES: dict[str, dict[str, Any]] = {
    DDB_LEADS: {
        "hash_key": ("phone_number", "S"),
        "fields": [
            "phone_number", "customer_name", "stage", "action", "lost_reason",
            "last_message", "last_message_at", "last_direction", "unread_count",
            "looking_requirement", "budget_min", "budget_max", "preferred_localities",
            "interested_listings", "next_followup_date", "source_group", "card_ts",
            "created_at", "updated_at",
        ],
    },
    DDB_INTERACTIONS: {
        "hash_key": ("phone_number", "S"), "range_key": ("timestamp", "S"),
        "fields": ["phone_number", "timestamp", "message_id", "direction", "message_body",
                   "group_name", "has_media", "media_urls", "is_from_group"],
    },
    DDB_AUDIT: {
        "hash_key": ("phone_number", "S"), "range_key": ("changed_at", "S"),
        "fields": ["phone_number", "changed_at", "field", "old_value", "new_value",
                   "source", "actor", "reason"],
    },
}

class LeadDbError(RuntimeError):
    pass


def _resource(_res=None):
    if _res is not None:
        return _res
    import boto3
    return boto3.resource("dynamodb", region_name=AWS_REGION)


def _table(name: str, _res=None):
    if _res is None and "pytest" in sys.modules:
        raise RuntimeError(f"refusing live DynamoDB table from tests: {name}")
    return _resource(_res).Table(name)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def table_spec(name: str) -> dict[str, Any]:
    spec = TABLES[name]
    keys = [{"AttributeName": spec["hash_key"][0], "KeyType": "HASH"}]
    attrs = [{"AttributeName": spec["hash_key"][0], "AttributeType": spec["hash_key"][1]}]
    if "range_key" in spec:
        keys.append({"AttributeName": spec["range_key"][0], "KeyType": "RANGE"})
        attrs.append({"AttributeName": spec["range_key"][0], "AttributeType": spec["range_key"][1]})
    return {"TableName": name, "KeySchema": keys, "AttributeDefinitions": attrs, "BillingMode": "PAY_PER_REQUEST"}


def create_tables(dry_run: bool = True, *, _client=None) -> dict[str, str]:
    if _client is None:
        import boto3
        _client = boto3.client("dynamodb", region_name=AWS_REGION)
    existing = set(_client.list_tables().get("TableNames", []))
    out: dict[str, str] = {}
    for name in TABLES:
        if name in existing:
            out[name] = "exists"
        elif dry_run:
            out[name] = "would create"
        else:
            _client.create_table(**table_spec(name))
            out[name] = "created"
    return out


def get_lead(phone: str, *, _res=None) -> dict | None:
    key = str(phone or "").strip()
    if not key:
        return None
    return _table(DDB_LEADS, _res).get_item(Key={"phone_number": key}).get("Item")


def all_leads(*, _res=None) -> list[dict]:
    table = _table(DDB_LEADS, _res)
    items: list[dict] = []
    kwargs: dict[str, Any] = {}
    while True:
        page = table.scan(**kwargs)
        items.extend(page.get("Items", []))
        if not page.get("LastEvaluatedKey"):
            return items
        kwargs["ExclusiveStartKey"] = page["LastEvaluatedKey"]


def interaction_exists(phone: str, message_id: str, *, _res=None) -> bool:
    if not message_id:
        return False
    got = _table(DDB_INTERACTIONS, _res).query(
        KeyConditionExpression="phone_number = :p",
        FilterExpression="message_id = :m",
        ExpressionAttributeValues={":p": str(phone).strip(), ":m": str(message_id)},
        ScanIndexForward=False,
        Limit=100,
    )
    return bool(got.get("Items"))


def lead_history(phone: str, limit: int = 50, *, _res=None) -> list[dict]:
    if not str(phone or "").strip():
        return []
    return _table(DDB_INTERACTIONS, _res).query(
        KeyConditionExpression="phone_number = :p",
        ExpressionAttributeValues={":p": str(phone).strip()},
        ScanIndexForward=True,
        Limit=limit,
    ).get("Items", [])


def log_interaction(phone: str, direction: str, body: str, *, message_id: str = "",
                    group_name: str = "", has_media: bool = False, media_urls: str = "",
                    is_from_group: bool = False, _res=None) -> dict:
    if direction not in ("in", "out"):
        raise LeadDbError("direction must be 'in' or 'out'")
    item = {"phone_number": str(phone).strip(), "timestamp": _now(), "message_id": str(message_id),
            "direction": direction, "message_body": str(body or ""), "group_name": str(group_name or ""),
            "has_media": bool(has_media), "media_urls": str(media_urls or ""),
            "is_from_group": bool(is_from_group)}
    _table(DDB_INTERACTIONS, _res).put_item(Item=item)
    return item


def put_lead(lead: dict, *, _res=None) -> dict:
    phone = str(lead.get("phone_number") or "").strip()
    if not phone or not any(c.isdigit() for c in phone):
        raise LeadDbError(f"phone_number is required: {lead.get('phone_number')!r}")
    item = {k: v for k, v in lead.items() if str(v).strip() != ""}
    item["phone_number"] = phone
    item.setdefault("created_at", _now())
    item["updated_at"] = _now()
    old = _table(DDB_LEADS, _res).put_item(Item=item, ReturnValues="ALL_OLD").get("Attributes")
    try:
        from . import audit
        audit.record(phone, audit.diff(old, item), _res=_res)
    except Exception as exc:  # noqa: BLE001
        print(f"lead audit write skipped: {exc!r}")
    return item


def set_card_ts(phone: str, card_ts: str, *, _res=None) -> None:
    _table(DDB_LEADS, _res).update_item(
        Key={"phone_number": str(phone).strip()},
        UpdateExpression="SET card_ts = :t",
        ExpressionAttributeValues={":t": str(card_ts)},
    )


def create_tables_cli(argv=None) -> int:
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--commit", action="store_true")
    args = p.parse_args(argv)
    for name, state in create_tables(dry_run=not args.commit).items():
        print(f"{name:24} {state}")
    return 0
