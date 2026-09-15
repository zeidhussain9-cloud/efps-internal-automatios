"""Canonical segmentation of concatenated WhatsApp inventory source messages.

This module contains no business rules. It identifies source-message boundaries
so every Inventory Stage-2 field extractor works against one source unit and
cannot consume a later message's value.
"""
from __future__ import annotations

import re

_MESSAGE_MARKER = re.compile(
    r"(?:^|(?<=[\n|]))\s*(?:"
    r"\[(?:\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4})[^\]]*\]"
    r"|(?:\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4})"
    r"[ T]\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AP]M)?"
    r"|(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\s*,\s*\d{1,2}:\d{2}(?:\s*[AP]M)?"
    r")\s*",
    re.I,
)


def normalize_segment(text: str) -> str:
    """Remove only transport-level timestamp/markup noise."""
    value = str(text or "")
    value = re.sub(r"<br\s*/?>", "\n", value, flags=re.I)
    value = re.sub(r"[*_`~]", "", value)
    value = re.sub(r"\s*\|\s*$", "", value)
    return value.strip()


def split_source_messages(text: str) -> list[str]:
    """Split raw inventory text into source messages without losing content.

    The text before the first recognized timestamp is retained as a legitimate
    source unit. A pipe is a boundary only when it precedes a recognized
    timestamp, so ordinary pipe characters inside values are not discarded.
    """
    raw = str(text or "").replace("\r\n", "\n").replace("\r", "\n")
    if not raw.strip():
        return []

    matches = list(_MESSAGE_MARKER.finditer(raw))
    if not matches:
        return [normalize_segment(x) for x in re.split(r"\n|<br\s*/?>", raw, flags=re.I) if normalize_segment(x)]

    segments: list[str] = []
    prefix = normalize_segment(raw[:matches[0].start()])
    if prefix:
        segments.append(prefix)

    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(raw)
        value = normalize_segment(raw[start:end])
        if value:
            segments.append(value)
    return segments


def iter_source_units(text: str) -> list[str]:
    """Return canonical source-message units."""
    return split_source_messages(text)
