"""Deterministic extraction: read only facts explicitly written in raw text."""
from __future__ import annotations
import re

from .source_segments import split_source_messages


def _scale(n: str, s: str = "") -> str:
    v = float(n.replace(",", ""))
    s = (s or "").lower()
    if s == "k": v *= 1000
    elif s in ("l", "lakh"): v *= 100000
    return str(int(v))


def _clean_source_value(value: str) -> str:
    value = re.sub(r"<br\s*/?>", "\n", str(value or ""), flags=re.I)
    value = re.sub(r"[*_`~]", "", value).strip()
    value = re.sub(r"\s+", " ", value)
    return value.strip(" -–—")


def _line_value(text: str, label: str) -> str:
    """Extract a labelled value from one source unit at a time.

    This is deliberately source-unit scoped. It prevents a label in one
    WhatsApp message from consuming the value belonging to a later message.
    """
    pattern = re.compile(rf"\b{label}\b\s*(?::|[-–—|=])\s*([^|\n<]+)", re.I)
    for unit in split_source_messages(text):
        match = pattern.search(unit)
        if match:
            value = _clean_source_value(match.group(1))
            if value:
                return value
    return ""


def _first_line_value(text: str, labels: tuple[str, ...]) -> str:
    for label in labels:
        value = _line_value(text, label)
        if value: return value
    return ""


def scan(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    text = text or ""
    m = (
        re.search(r"\b(\d+(?:\.\d+)?)\s*[- ]?\s*bhk\b", text, re.I)
        or re.search(r"\bbed\s*rooms?\s*[:\-]\s*(\d+(?:\.\d+)?)\b", text, re.I)
        or re.search(r"\b(\d+(?:\.\d+)?)\s*[- ]?\s*bed\s*rooms?\b", text, re.I)
    )
    if m: out["BHK"] = f"{m.group(1)} BHK"
    elif re.search(r"\bstudio\b", text, re.I): out["property_subtype"] = "Studio"

    m = (re.search(r"(?:rent|rental)\D{0,12}?(?:rs\.?|inr|₹)?\s*(\d[\d,]*\.?\d*)\s*(k|lakh|l)?\b", text, re.I)
         or re.search(r"(?:rs\.?|inr|₹)\s*(\d[\d,]*)\s*(k)?\b", text, re.I))
    if m:
        v = _scale(m.group(1), m.group(2) if m.lastindex and m.lastindex > 1 else "")
        if 3000 <= int(v) <= 100000000: out["monthly_rent"] = v

    for key, pat in (("carpet_area", r"carpet\s*area\D{0,5}(\d{3,5})"),("built_up_area", r"built-?up\s*area\D{0,5}(\d{3,5})")):
        m = re.search(pat, text, re.I)
        if m: out[key] = m.group(1)
    if "built_up_area" not in out:
        m = re.search(r"sqft\s*[:\-]\s*(\d{3,5})", text, re.I) or re.search(r"\b(\d{3,5})\s*(?:sq\.?\s*ft|sqft|sft)\b", text, re.I)
        if m: out["built_up_area"] = m.group(1)

    m = re.search(r"floor\s*[:\-]\s*(g|ground|\d{1,2})\s*(?:/|of)\s*(\d{1,2})", text, re.I)
    if m:
        out["floor_number"] = "0" if m.group(1).lower() in {"g","ground"} else m.group(1)
        out["total_floors"] = m.group(2)
    else:
        m = re.search(r"\b(\d{1,2})\s*(?:st|nd|rd|th)?\s*floor\b", text, re.I)
        if m:
            out["floor_number"] = m.group(1)
            tail = text[m.end():m.end()+25]
            n = re.search(r"(?:out of|of|/)\s*(\d{1,2})", tail, re.I)
            if n: out["total_floors"] = n.group(1)

    patterns = {"bathrooms": r"\b(\d)\s*(?:bath|bathroom|toilet|washroom)s?\b","balconies": r"\b(\d)\s*balcon(?:y|ies)\b","covered_parking": r"(\d)\s*covered\s*parking","open_parking": r"(\d)\s*open\s*parking"}
    for key, pat in patterns.items():
        m = re.search(pat, text, re.I)
        if m: out[key] = m.group(1)

    direct = {
        "internal_property_type": _first_line_value(text, (r"internal\s*property\s*type", r"property\s*type", r"property\s*classification", r"gating\s*type")),
        "society_name": _first_line_value(text, (r"society\s*name", r"society", r"apartment\s*name", r"community\s*name", r"building\s*name")),
        "landmark": _first_line_value(text, (r"landmark",)),
        "locality": _first_line_value(text, (r"property\s*location", r"location", r"locality", r"area")),
        "property_subtype": _first_line_value(text, (r"property\s*subtype", r"subtype")),
        "property_highlights": _first_line_value(text, (r"property\s*highlights", r"highlights")),
        "age_of_property_years": _first_line_value(text, (r"age\s*of\s*property", r"property\s*age")),
    }
    for key, value in direct.items():
        if value: out[key] = value

    maintenance = _line_value(text, r"maintenance")
    if maintenance:
        numeric = re.fullmatch(r"\s*([\d.,]+)\s*(k|lakh|l)?\s*", maintenance, re.I)
        out["maintenance"] = _scale(numeric.group(1), numeric.group(2)) if numeric else maintenance
        out["maintenance_included"] = "Yes" if maintenance.strip().lower() == "included" else "No"
    if re.search(r"maintenance\s*[:\-]\s*included\b", text, re.I): out["maintenance_included"] = "Yes"

    for key, label in (("preferred_tenant_type", r"preferred\s*tenant"),("bachelor_preference", r"bachelor(?:s)?"),("pet_friendly", r"pets?"),("servant_room", r"servant\s*room")):
        value = _line_value(text, label)
        if value: out[key] = value

    m = re.search(r"(?:deposit|dep|advance)\D{0,12}?(\d[\d,]*\.?\d*)\s*(k|lakh|l|months?|mnths?)?", text, re.I)
    if m:
        unit = (m.group(2) or "").lower()
        out["security_deposit"] = (str(int(float(m.group(1).replace(",", ""))*int(out["monthly_rent"]))) if unit.startswith(("month","mnth")) and out.get("monthly_rent","").isdigit() else _scale(m.group(1),m.group(2)))

    for pat, label in ((r"\bfully\s*furnish", "Fully Furnished"),(r"\bsemi[-\s]*furnish", "Semi Furnished")):
        if re.search(pat, text, re.I): out["furnish_type"] = label; break
    return out
