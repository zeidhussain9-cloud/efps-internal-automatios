"""Security primitives for Slack inbound requests."""
from __future__ import annotations

import hashlib
import hmac
import os
import time


class SlackSecurityError(ValueError):
    pass


def verify_signature(raw_body: bytes, timestamp: str, signature: str, *, now: int | None = None,
                     max_age_seconds: int = 300, signing_secret: str | None = None) -> bool:
    """Verify Slack's v0 HMAC signature and reject stale requests."""
    secret = (signing_secret or os.getenv("SLACK_SIGNING_SECRET", "")).encode("utf-8")
    if not secret or not timestamp or not signature:
        return False
    try:
        ts = int(timestamp)
    except ValueError:
        return False
    current = int(time.time()) if now is None else int(now)
    if abs(current - ts) > max_age_seconds:
        return False
    base = b"v0:" + timestamp.encode("utf-8") + b":" + raw_body
    expected = "v0=" + hmac.new(secret, base, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def require_valid_signature(raw_body: bytes, timestamp: str, signature: str, **kwargs: object) -> None:
    if not verify_signature(raw_body, timestamp, signature, **kwargs):
        raise SlackSecurityError("Invalid or expired Slack request signature")
