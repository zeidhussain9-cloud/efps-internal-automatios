"""Source-first reconciliation helpers for deterministic inventory fields."""
from __future__ import annotations
import re

from .source_segments import split_source_messages

_CANONICAL = (
    (re.compile(r"\bsemi[-\s]*gated\s*(?:community|society|property)?\b", re.I), "Semi Gated"),
    (re.compile(r"\bgated\s*(?:community|society|property)\b", re.I), "Gated Community"),
    (re.compile(r"\bstand[-\s]*alone\b", re.I), "Standalone"),
)
_LABEL = re.compile(
    r"\b(?:internal\s+property\s+type|property\s+(?:type|classification)|gating\s+type)\b"
    r"\s*(?:[:=|\-])\s*([^|\n<]+)", re.I,
)
_BOOLEAN_GATING = re.compile(
    r"\b(?P<label>semi[-\s]*gated|gated\s*(?:community|society|property)?)\b"
    r"\s*(?:[:=|\-])\s*(?P<value>[^|\n<]+)", re.I,
)


def _canonical_value(value: str) -> str:
    value = re.sub(r"[*_`~]", "", str(value or "")).strip()
    for pattern, canonical in _CANONICAL:
        if pattern.search(value): return canonical
    return "Standalone" if re.fullmatch(r"stand[-\s]*alone", value, re.I) else ""


def _boolean_value(value: str) -> bool | None:
    cleaned = re.sub(r"[*_`~]", "", str(value or "")).strip().lower()
    if cleaned in {"yes","y","true","1","allowed"}: return True
    if cleaned in {"no","n","false","0","not allowed","not permitted","none"}: return False
    return None


def extract_property_type(raw_text: str) -> str:
    """Return explicit canonical property type from source evidence only."""
    for unit in split_source_messages(raw_text):
        # Boolean gating is checked before free-text canonical phrase matching;
        # otherwise ``Gated Community: No`` would be mistaken for a positive
        # canonical phrase merely because the label itself contains the phrase.
        for match in _BOOLEAN_GATING.finditer(unit):
            value = _boolean_value(match.group("value"))
            if value is True:
                label = match.group("label").lower()
                return "Semi Gated" if "semi" in label else "Gated Community"
            if value is False:
                continue

        for match in _LABEL.finditer(unit):
            value = _canonical_value(match.group(1))
            if value: return value

        # Standalone/semi-gated/gated phrases are accepted only within this
        # source unit, never by concatenating evidence from different messages.
        value = _canonical_value(unit)
        if value:
            # A negative boolean form was already handled above. Reject any
            # remaining explicit negative gating phrase defensively.
            if re.search(r"\b(?:gated|semi[-\s]*gated)\b\s*(?:community|society|property)?\s*(?:[:=|\-])\s*(?:no|false|0|not\s+allowed|not\s+permitted)\b", unit, re.I):
                continue
            return value
    return ""


def reconcile_property_type(row: dict, raw_text: str) -> dict:
    """Apply explicit source classification before downstream normalization."""
    value = extract_property_type(raw_text)
    if value: row["internal_property_type"] = value
    return row
