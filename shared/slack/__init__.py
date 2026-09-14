"""Shared Slack capability."""

from .client import SlackClient, SlackConfig, SlackError
from .routing import (
    BUGS_CHANNEL,
    INVENTORY_CHANNEL,
    LEADS_CHANNEL,
    PROPERTY_VERIFICATION_CHANNEL,
    TOP_LEVEL_COMMAND,
)
from .safety import normalize_thread_control, safe_text
from .security import SlackSecurityError, require_valid_signature, verify_signature

__all__ = [
    "SlackClient",
    "SlackConfig",
    "SlackError",
    "SlackSecurityError",
    "INVENTORY_CHANNEL",
    "LEADS_CHANNEL",
    "PROPERTY_VERIFICATION_CHANNEL",
    "BUGS_CHANNEL",
    "TOP_LEVEL_COMMAND",
    "safe_text",
    "normalize_thread_control",
    "verify_signature",
    "require_valid_signature",
]
