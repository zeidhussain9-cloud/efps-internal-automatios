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

# The legacy webhook protected the public Function URL with a shared token in
# query parameter `t`. The secret value itself remains runtime-only.
WEBHOOK_TOKEN_ENV = "EFPS_WEBHOOK_TOKEN"
WEBHOOK_QUERY_PARAMETER = "t"

# Verified legacy source numbers retained as integration hints. They are not
# two WhAPI credentials and must not be interpreted as two channels.
INVENTORY_LISTENER_NUMBERS = (
    "917975102130",
    "919902024973",
)


def live_enabled() -> bool:
    return os.environ.get(LIVE_FLAG, "") == "1"


def normalise_phone(value: str) -> str:
    """Return a WhatsApp phone number as bare digits with country code 91 when inferable."""
    digits = re.sub(r"\D", "", str(value).split("@")[0])
    if len(digits) == 10:
        return "91" + digits
    if len(digits) == 11 and digits.startswith("0"):
        return "91" + digits[1:]
    return digits


def is_inventory_listener(value: str) -> bool:
    """Whether the sender matches one of the retained inventory-listener numbers."""
    return normalise_phone(value) in set(INVENTORY_LISTENER_NUMBERS)


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
