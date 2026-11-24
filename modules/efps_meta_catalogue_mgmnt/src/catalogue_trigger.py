"""Trigger surface for the gated catalogue operations.

Two trigger paths, both fail-closed and both reuse the existing intake
mechanisms:

1. HMAC-signed HTTP route (/catalogue/run), the pattern from
   scripts/trigger-inventory-sync.mjs: X-EFPS-Inventory-Timestamp +
   X-EFPS-Inventory-Signature = HMAC-SHA256(timestamp) hex, 5-minute window.
   The HTTP handler only verifies and enqueues; the operation itself runs in
   the internal async invocation so long runs never hit API Gateway timeouts.

2. Notion webhook ticks: ticking Run on a Catalogue Control Panel row
   arrives through the existing intake webhook -> worker path, which enqueues
   the same internal invocation. (The Housing-row "Post to Catalogue" tick
   path was retired on 24 Nov 2026 with the column's removal.)

Nothing auto-fires: every run traces to an explicit tick or signed call, the
operation's own switch must be ON, and the two template.yaml masters gate
live traffic. The runner enforces all of that again at run time.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import time

OPERATIONS = ("create", "update", "delete", "assign", "reconcile")

SIGNATURE_HEADER = "x-efps-inventory-signature"
TIMESTAMP_HEADER = "x-efps-inventory-timestamp"
TIMESTAMP_TOLERANCE_SECONDS = 300

TRIGGER_SECRET_ENV = "CATALOGUE_TRIGGER_SECRET_ARN"


class CatalogueTriggerError(RuntimeError):
    pass


def verify_signature(headers: dict, *, secret: str, now: float | None = None) -> bool:
    """Constant-time check of the trigger HMAC headers. Fail-closed."""
    if not secret:
        return False
    lowered = {str(k).lower(): str(v) for k, v in (headers or {}).items()}
    timestamp = lowered.get(TIMESTAMP_HEADER, "").strip()
    supplied = lowered.get(SIGNATURE_HEADER, "").strip()
    if not timestamp or not supplied:
        return False
    try:
        stamp = int(timestamp)
    except ValueError:
        return False
    current = time.time() if now is None else now
    if abs(current - stamp) > TIMESTAMP_TOLERANCE_SECONDS:
        return False
    expected = hmac.new(secret.encode("utf-8"), timestamp.encode("utf-8"), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, supplied)


def parse_operation(body: str) -> str:
    try:
        payload = json.loads(body or "{}")
    except (json.JSONDecodeError, TypeError):
        raise CatalogueTriggerError("trigger body must be a JSON object")
    operation = str(payload.get("operation") or "").strip().lower()
    if operation not in OPERATIONS:
        raise CatalogueTriggerError(f"operation must be one of: {', '.join(OPERATIONS)}")
    return operation


def masters_from_environment() -> dict:
    return {
        "EFPS_WHAPI_LIVE": os.environ.get("EFPS_WHAPI_LIVE", "") == "1",
        "EFPS_WHAPI_API_ENABLED": os.environ.get("EFPS_WHAPI_API_ENABLED", "") == "1",
    }


def run_catalogue_operation(operation: str, *, notion_token: str, store=None, whapi=None, time_left=None) -> dict:
    """Execute one gated operation against live Notion + Whapi.

    store/whapi are injectable for tests; production builds them from the
    Lambda's own token and environment.
    """
    if operation not in OPERATIONS:
        raise CatalogueTriggerError(f"unsupported catalogue operation: {operation!r}")
    if store is None:
        from catalogue_notion_store import NotionCatalogueStore

        store = NotionCatalogueStore(notion_token)
    if whapi is None:
        import boto3
        from shared.whatsapp_whapi.client import WhApiClient, WhApiCredentials

        secret_arn = os.environ.get("WHAPI_SECRET_ARN", "").strip()
        if not secret_arn:
            raise CatalogueTriggerError("WHAPI_SECRET_ARN is not configured")
        secret = json.loads(boto3.client("secretsmanager").get_secret_value(SecretId=secret_arn)["SecretString"])
        token = ""
        for key in ("token", "api_token", "value"):
            if secret.get(key):
                token = str(secret[key]).strip()
                break
        if not token:
            raise CatalogueTriggerError("WhAPI secret has no token field")
        whapi = WhApiClient(credentials=WhApiCredentials(token=token))
    from catalogue_runner import run_operation

    return run_operation(operation, store=store, whapi=whapi, masters=masters_from_environment(), time_left=time_left)
