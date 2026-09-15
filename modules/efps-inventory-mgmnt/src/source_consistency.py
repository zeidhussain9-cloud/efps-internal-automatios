"""Source-first reconciliation helpers for deterministic inventory fields."""
from __future__ import annotations
import re

_CANONICAL = (
    (re.compile(r"\bsemi[-\s]*gated\s*(?:community|society|property)?\b", re.I), "Semi Gated"),
    (re.compile(r"\bgated\s*(?:community|society|property)\b", re.I), "Gated Community"),
    (re.compile(r"\bstand[-\s]*alone\b", re.I), "Standalone"),
)
_LABEL = re.compile(
    r"\b(?:internal\s+property\s+type|property\s+(?:type|classification)|gating\s+type|gated\s*(?:community|society|property)?)\b"
    r"\s*(?:[:=|\-])\s*(.*?)"
    r"(?=(?:<br\s*/?>)|\n|\s*(?:\[(?:\d{4}[-/]\d{1,2}[-/]\d{1,2})[^\]]*\]|(?:\d{4}[-/]\d{1,2}[-/]\d{1,2}[ T]\d{1,2}:\d{2}(?::\d{2})?))|$)",
    re.I,
)


def _canonical_value(value: str) -> str:
    value = re.sub(r"[*_`~]", "", str(value or "")).strip()
    for pattern, canonical in _CANONICAL:
        if pattern.search(value):
            return canonical
    return "Standalone" if re.fullmatch(r"stand[-\s]*alone", value, re.I) else ""


def extract_property_type(raw_text: str) -> str:
    """Return an explicit canonical property type, never an inferred guess.

    Labelled values outrank free-text mentions. Free-text canonical phrases are
    accepted only as complete source phrases; unrelated words such as ``type``
    are never used as a classifier.
    """
    text = str(raw_text or "")
    for match in _LABEL.finditer(text):
        value = _canonical_value(match.group(1))
        if value:
            return value

    # Evaluate each source line/message independently so a later message cannot
    # contaminate an earlier classification.
    chunks = re.split(r"(?:<br\s*/?>|\n)", text, flags=re.I)
    for chunk in chunks:
        value = _canonical_value(chunk)
        if value:
            return value
    return ""


def reconcile_property_type(row: dict, raw_text: str) -> dict:
    """Apply explicit source classification before downstream normalization."""
    value = extract_property_type(raw_text)
    if value:
        row["internal_property_type"] = value
    return row
