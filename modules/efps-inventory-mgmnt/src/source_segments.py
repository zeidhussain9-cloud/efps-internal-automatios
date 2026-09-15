"""Canonical segmentation of concatenated WhatsApp inventory source messages.

Stage-2 field extraction must operate on source-message boundaries. This module
contains no business rules; it only identifies message boundaries and returns
clean source segments so field-specific extractors cannot consume a later
message's value.
"""
from __future__ import annotations

import re

# Supported source forms seen in inventory exports:
#   [2026-09-15 10:00] Message
#   2026-09-15 10:00 Message
#   2026-09-15 10:00:00 Message
#   common slash-date timestamp forms
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
    return value.strip()


def split_source_messages(text: str) -> list[str]:
    """Split raw inventory text into source messages without losing content.

    Newline and pipe are also treated as message separators only when followed
    by a recognized timestamp. A plain pipe therefore remains part of a field
    value unless it is clearly a transport delimiter.
    """
    raw = str(text or "").replace("\r\n", "\n").replace("\r", "\n")
    if not raw.strip():
        return []
    matches = list(_MESSAGE_MARKER.finditer(raw))
    if not matches:
        return [normalize_segment(x) for x in re.split(r"\n|<br\s*/?>", raw, flags=re.I) if normalize_segment(x)]

    segments: list[str] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(raw)
        value = normalize_segment(raw[start:end])
        if value:
            segments.append(value)
    return segments


def iter_source_units(text: str) -> list[str]:
    """Return message units plus ordinary un-timestamped lines as source units."""
    return split_source_messages(text)
