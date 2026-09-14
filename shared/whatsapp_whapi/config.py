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

WEBHOOK_TOKEN_ENV = "EFPS_WEBHOOK_TOKEN"
WEBHOOK_QUERY_PARAMETER = "t"

# Verified legacy source numbers. These are source-routing facts, not two
# WhAPI credentials/channels.
INVENTORY_LISTENER_NUMBERS = (
    "917975102130",
    "919902024973",
)
# Backward-compatible alias for existing inventory tests/callers.
INVENTORY_SENDER_NUMBERS = INVENTORY_LISTENER_NUMBERS

INVENTORY_LISTENER_NAME = "inventory"
LEAD_LISTENER_NAME = "lead"

LEAD_LISTENER_EXCLUDED_PATHS = (
    "inventory",
    "groups",
    "promotions",
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
    """Whether the sender matches one of the two dedicated inventory numbers."""
    return normalise_phone(value) in set(INVENTORY_LISTENER_NUMBERS)


def classify_listener_source(*, sender: str, chat_id: str, from_me: bool = False, path: str | None = None) -> str:
    """Return the neutral listener name: ``inventory`` or ``lead``.

    Inventory is restricted to the two dedicated direct-message sender
    numbers. Group traffic, promotion traffic, and all other direct senders
    remain on the lead listener path. This function performs no business
    action, persistence, matching, deduplication, or lead creation.
    """
    normalized_path = (path or "").strip().lower()
    is_group = chat_id.endswith("@g.us")
    if (
        not from_me
        and not is_group
        and normalized_path not in {"groups", "promotions"}
        and is_inventory_listener(sender or chat_id)
    ):
        return INVENTORY_LISTENER_NAME
    return LEAD_LISTENER_NAME


def listener_configuration() -> dict[str, object]:
    """Return the repository-level two-listener routing configuration."""
    return {
        "inventory": {
            "name": INVENTORY_LISTENER_NAME,
            "source_numbers": list(INVENTORY_LISTENER_NUMBERS),
            "direct_messages_only": True,
        },
        "lead": {
            "name": LEAD_LISTENER_NAME,
            "default_for_other_inbound_traffic": True,
            "excluded_paths": list(LEAD_LISTENER_EXCLUDED_PATHS),
        },
    }


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
