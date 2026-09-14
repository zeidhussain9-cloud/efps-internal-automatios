"""Canonical EFPS WhAPI integration configuration.

This file contains integration facts, not inventory/lead business rules.
Secret values are never stored here.
"""

from __future__ import annotations

import os
import re

SECRET_NAME = "efps-whapi-panel-token"
TOKEN_ENV = "WHAPI_API_TOKEN"
BASE_URL = "https://gate.whapi.cloud"
LIVE_FLAG = "EFPS_WHAPI_LIVE"

# The legacy webhook protected the public Function URL with a shared token in
# query parameter `t`. The secret value itself remains runtime-only.
WEBHOOK_TOKEN_ENV = "EFPS_WEBHOOK_TOKEN"
WEBHOOK_QUERY_PARAMETER = "t"

# These are the two verified inventory-listener source numbers from the legacy
# deployment. They are WhatsApp sender numbers used to distinguish inventory
# messages from ordinary direct enquiries. They are NOT two WhAPI channel
# credentials; the legacy WhAPI auth model is one token per connected channel.
INVENTORY_LISTENER_NUMBERS = (
    "917975102130",
    "919902024973",
)

# The legacy WhAPI skill/reference configured webhook subscriptions through
# PATCH /settings using this event family. Endpoint-specific registration must
# still be verified against the current WhAPI API before a live mutation.
WEBHOOK_EVENT_TYPES = (
    "messages",
    "statuses",
    "chats",
    "contacts",
    "groups",
    "calls",
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
    """Whether the sender matches one of the verified inventory-listener numbers."""
    return normalise_phone(value) in set(INVENTORY_LISTENER_NUMBERS)


def webhook_registration_payload(url: str) -> dict:
    """Build the legacy-compatible WhAPI webhook settings payload.

    This only constructs data. It does not perform the destructive/live
    `PATCH /settings` operation.
    """
    if not url.strip():
        raise ValueError("webhook URL must not be empty")
    return {
        "webhooks": [
            {
                "mode": "body",
                "events": [
                    {"type": event_type, "method": "post"}
                    for event_type in WEBHOOK_EVENT_TYPES
                ],
                "url": url.rstrip("/"),
            }
        ]
    }
