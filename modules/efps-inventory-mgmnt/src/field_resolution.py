"""Canonical deterministic candidate resolution for Inventory Stage 2.

Extraction discovers source candidates; this module chooses the authoritative
candidate. It contains no AI and never uses existing Sheet values as source
truth.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .source_segments import split_source_messages


@dataclass(frozen=True)
class Candidate:
    field: str
    value: str
    segment_index: int
    method: str
    explicit: bool
    position: int


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[*_`~]", "", str(value or ""))).strip(" -–—")


def _segments(text: str) -> list[str]:
    return split_source_messages(text)


def _label_candidates(text: str, label: str, field: str) -> list[Candidate]:
    out: list[Candidate] = []
    pattern = re.compile(rf"\b{label}\b\s*(?::|[-–—|=])\s*([^|\n<]+)", re.I)
    for i, segment in enumerate(_segments(text)):
        for match in pattern.finditer(segment):
            value = _clean(match.group(1))
            if value:
                out.append(Candidate(field, value, i, "label", True, match.start()))
    return out


def resolve_bhk(text: str) -> str:
    candidates: list[Candidate] = []
    for label in (r"bhk", r"bed\s*rooms?"):
        for i, segment in enumerate(_segments(text)):
            if label == r"bhk":
                pattern = re.compile(r"\b(\d+(?:\.\d+)?)\s*[- ]?\s*bhk\b", re.I)
                for m in pattern.finditer(segment):
                    candidates.append(Candidate("BHK", f"{m.group(1)} BHK", i, "direct", True, m.start()))
            else:
                for m in re.finditer(r"\bbed\s*rooms?\s*[:\-]\s*(\d+(?:\.\d+)?)\b", segment, re.I):
                    candidates.append(Candidate("BHK", f"{m.group(1)} BHK", i, "label", True, m.start()))
                for m in re.finditer(r"\b(\d+(?:\.\d+)?)\s*[- ]?\s*bed\s*rooms?\b", segment, re.I):
                    candidates.append(Candidate("BHK", f"{m.group(1)} BHK", i, "direct", True, m.start()))
    if not candidates and re.search(r"\bstudio\b", text, re.I):
        return "1 RK"
    if not candidates:
        return ""
    # Within the same source unit the first explicit property value wins.
    # Across source units, the latest explicit value wins because later
    # inventory messages commonly contain corrections.
    candidates.sort(key=lambda c: (c.segment_index, c.position))
    return candidates[-1].value


def resolve_maintenance(text: str) -> tuple[str, str]:
    candidates = _label_candidates(text, r"maintenance", "maintenance")
    if not candidates:
        # Also support "50K + 6K Maintenance" without allowing unrelated
        # numbers to become maintenance.
        pattern = re.compile(r"(?:₹|rs\.?\s*)?\s*(\d[\d,.]*)\s*(k|lakh|l)?\s*\+\s*(\d[\d,.]*)\s*(k|lakh|l)?\s*maintenance\b", re.I)
        for i, segment in enumerate(_segments(text)):
            for m in pattern.finditer(segment):
                candidates.append(Candidate("maintenance", f"{m.group(2) or ''}", i, "rent_suffix", True, m.start()))
    if not candidates:
        return "", ""

    chosen = sorted(candidates, key=lambda c: (c.segment_index, c.position))[-1]
    raw = chosen.value.strip()
    if raw.lower() == "included":
        return "0", "Yes"

    m = re.fullmatch(r"([\d.,]+)\s*(k|lakh|l)?\s*(?:\+\s*(.+))?", raw, re.I)
    if not m:
        return re.sub(r"(?<=\d),(?=\d)", "", raw), "No"

    number = float(m.group(1).replace(",", ""))
    unit = (m.group(2) or "").lower()
    if unit == "k": number *= 1000
    elif unit in {"l", "lakh"}: number *= 100000
    result = str(int(number))
    suffix = _clean(m.group(3) or "")
    return (f"{result} + {suffix}" if suffix else result), "No"


def resolve_internal_property_type(text: str) -> str:
    explicit: list[Candidate] = []
    label_patterns = (
        (r"internal\s*property\s*type", "internal"),
        (r"property\s*(?:type|classification)", "property_label"),
        (r"gating\s*type", "gating_label"),
    )
    for label, method in label_patterns:
        for candidate in _label_candidates(text, label, "internal_property_type"):
            value = candidate.value.lower()
            if "semi" in value and "gated" in value:
                explicit.append(Candidate(candidate.field, "Semi Gated", candidate.segment_index, method, True, candidate.position))
            elif "gated" in value:
                explicit.append(Candidate(candidate.field, "Gated Community", candidate.segment_index, method, True, candidate.position))
            elif "stand" in value:
                explicit.append(Candidate(candidate.field, "Standalone", candidate.segment_index, method, True, candidate.position))

    boolean: list[Candidate] = []
    pattern = re.compile(r"\b(?P<label>semi[-\s]*gated|gated\s*(?:community|society|property)?)\b\s*(?:[:=|\-])\s*(?P<value>[^|\n<]+)", re.I)
    yes = {"yes", "y", "true", "1", "allowed"}
    no = {"no", "n", "false", "0", "not allowed", "not permitted", "none"}
    for i, segment in enumerate(_segments(text)):
        for m in pattern.finditer(segment):
            value = _clean(m.group("value")).lower()
            if value in yes:
                canonical = "Semi Gated" if "semi" in m.group("label").lower() else "Gated Community"
                boolean.append(Candidate("internal_property_type", canonical, i, "boolean", True, m.start()))
            elif value in no:
                boolean.append(Candidate("internal_property_type", "Standalone", i, "boolean_negative", True, m.start()))

    # Explicit labelled/boolean evidence outranks generic words. A negative
    # explicit statement is authoritative and cannot later be overridden by a
    # generic gated keyword elsewhere in the source.
    if boolean:
        return sorted(boolean, key=lambda c: (c.segment_index, c.position))[-1].value
    if explicit:
        return sorted(explicit, key=lambda c: (c.segment_index, c.position))[-1].value

    generic: list[Candidate] = []
    for i, segment in enumerate(_segments(text)):
        if re.search(r"\bsemi[-\s]*gated\b", segment, re.I):
            generic.append(Candidate("internal_property_type", "Semi Gated", i, "generic", False, 0))
        elif re.search(r"\bgated\s*(?:community|society|property)\b", segment, re.I):
            generic.append(Candidate("internal_property_type", "Gated Community", i, "generic", False, 0))
        elif re.search(r"\b(?:independent\s+(?:house|floor)|farm\s*house|stand[-\s]*alone)\b", segment, re.I):
            generic.append(Candidate("internal_property_type", "Standalone", i, "generic", False, 0))
    if generic:
        return sorted(generic, key=lambda c: (c.segment_index, c.position))[-1].value
    return "Standalone"
