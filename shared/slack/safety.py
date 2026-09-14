"""Reusable Slack text safety helpers.

These helpers prevent customer/property text from accidentally becoming Slack
mentions. They do not decide business content.
"""
from __future__ import annotations

import re


MENTION_RE = re.compile(r"<(?:(?:@|!)[^>]+|#[^>]+)>")


def safe_text(value: object) -> str:
    """Neutralize Slack mention markup in externally supplied text."""
    text = str(value if value is not None else "")
    return MENTION_RE.sub(lambda match: match.group(0).replace("<", "&lt;").replace(">", "&gt;"), text)


def normalize_thread_control(text: object) -> str | None:
    """Recognize only an explicit bare session control word."""
    value = str(text or "").strip().lower()
    if value in {"done", "submit", "next", "skip", "exit"}:
        return value
    return None
