"""Canonical EFPS WhAPI integration configuration.

This file contains integration facts, not inventory/lead business rules.
Secret values are never stored here.
"""

from __future__ import annotations

import os
import re
from collections.abc import Iterable, Mapping

SECRET_NAME = "efps-whapi-panel-token"
TOKEN_ENV = "WHAPI_API_TOKEN"
BASE_URL = "https://gate.whapi.cloud"
LIVE_FLAG = "EFPS_WHAPI_LIVE"
API_ENABLED_FLAG = "EFPS_WHAPI_API_ENABLED"
CATALOG_WRITE_FLAG = "EFPS_WHAPI_CATALOG_WRITE_ENABLED"
WEBHOOK_ENABLED_FLAG = "EFPS_WHAPI_WEBHOOK_ENABLED"

WEBHOOK_TOKEN_ENV = "EFPS_WEBHOOK_TOKEN"
WEBHOOK_QUERY_PARAMETER = "t"

# Fallback inventory source allowlist. The deployed SAM template may override it
# with INVENTORY_SENDERS; message parsing itself remains transport-only.
INVENTORY_SOURCE_NUMBERS = (
    "917975102130",
    "919902024973",
)


def flag_enabled(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}

def live_enabled() -> bool:
    return flag_enabled(LIVE_FLAG, False)

def api_enabled() -> bool:
    return flag_enabled(API_ENABLED_FLAG, False)

def catalog_write_enabled() -> bool:
    return api_enabled() and flag_enabled(CATALOG_WRITE_FLAG, False)

def webhook_enabled() -> bool:
    return flag_enabled(WEBHOOK_ENABLED_FLAG, True)


def normalise_phone(value: str) -> str:
    """Return a WhatsApp phone number as bare digits with country code 91 when inferable."""
    digits = re.sub(r"\D", "", str(value).split("@")[0])
    if len(digits) == 10:
        return "91" + digits
    if len(digits) == 11 and digits.startswith("0"):
        return "91" + digits[1:]
    return digits

def inventory_source_numbers() -> tuple[str, ...]:
    """Return normalized inventory sender allowlist, honoring the Lambda env override."""
    configured = os.environ.get("INVENTORY_SENDERS", "").strip()
    values = configured.split(",") if configured else INVENTORY_SOURCE_NUMBERS
    return tuple(normalise_phone(value.strip()) for value in values if value.strip())


def is_inventory_source(value: str) -> bool:
    """Whether a direct-message sender belongs to the configured inventory source allowlist."""
    return normalise_phone(value) in set(inventory_source_numbers())


def webhook_registration_payload(url: str, events: Iterable[Mapping[str, str] | str]) -> dict:
    """Build a WhAPI `/settings` webhook payload from explicitly verified events.

    The caller must obtain the allowed event names from `GET /settings/events`
    before a live configuration change. This prevents the shared layer from
    guessing that legacy event names remain valid.
    """
    normalized: list[dict[str, str]] = []
    for event in events:
        if isinstance(event, str):
            event_type = event.strip()
            method = "post"
        else:
            event_type = str(event.get("type") or "").strip()
            method = str(event.get("method") or "post").strip().lower()
        if not event_type:
            raise ValueError("webhook event type must not be empty")
        if not method:
            raise ValueError("webhook event method must not be empty")
        normalized.append({"type": event_type, "method": method})

    if not url.strip():
        raise ValueError("webhook URL must not be empty")
    if not normalized:
        raise ValueError("at least one verified webhook event is required")

    return {
        "webhooks": [
            {
                "mode": "body",
                "events": normalized,
                "url": url.rstrip("/"),
            }
        ]
    }
