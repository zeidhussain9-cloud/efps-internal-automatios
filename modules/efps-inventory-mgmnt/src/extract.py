"""Deterministic extraction: read only facts explicitly written in raw text."""
from __future__ import annotations
import re

from shared.ola_maps.links import MapsLinks
from source_segments import split_source_messages
from field_resolution import resolve_bhk, resolve_internal_property_type, resolve_maintenance, resolve_property_subtype


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
    pattern = re.compile(rf"\b(?:{label})\b\s*(?::|[-–—|=])\s*([^|\n<]+)", re.I)
    for unit in split_source_messages(text):
        match = pattern.search(unit)
        if match:
            value = _clean_source_value(match.group(1))
            if value: return value
    return ""


def _first_line_value(text: str, labels: tuple[str, ...]) -> str:
    for label in labels:
        value = _line_value(text, label)
        if value: return value
    return ""


def _marker_candidates(text: str) -> tuple[str, str, str]:
    """Read the common EFPS '📍 Name:' source marker without swallowing URLs."""
    society=""; landmark=""; maps_url=MapsLinks.extract_url(text)
    pattern=re.compile(r"(?:📍|:round_pushpin:|:pushpin:)\s*([^:\n|]+?)\s*:\s*(?:\n\s*)?",re.I)
    for match in pattern.finditer(text or ""):
        name=_clean_source_value(match.group(1))
        tail=(text[match.end():match.end()+500] if match.end() < len(text or "") else "")
        if re.fullmatch(r"(?:landmark|location)\s*",name,re.I):
            if not maps_url:
                lm=re.split(r"\s+",tail,1)[0].strip()
                landmark=lm if lm and not MapsLinks.extract_url(lm) else landmark
            continue
        if name and not society: society=name
    return society, landmark, maps_url



def prose_location(text: str) -> dict[str, str]:
    """Read a bounded comma-separated property header, not arbitrary sentences.

    Supported headers: society, locality, property type; or locality, property
    type. Explicit labeled fields take precedence in scan(). The locality is a
    source candidate only: the intake adapter must still match its live options.
    Ambiguous/negative headers are left unresolved rather than invented.
    """
    first_line = next((line.strip() for line in (text or "").splitlines() if line.strip()), "")
    parts = [_clean_source_value(part) for part in first_line.split(",")]
    markers = [i for i, part in enumerate(parts) if re.fullmatch(
        r"(?:gated\s+community|semi[- ]gated(?:\s+community)?|standalone)", part, re.I)]
    if len(markers) != 1 or markers[0] not in (1, 2):
        return {}
    prefix = parts[:markers[0]]
    # Don't reinterpret prices, requirements, alternatives or labeled data as names.
    forbidden = r"[:/|;?]|\b(?:not|no|near|or|and|rent|budget|available|bhk|bedrooms?|bathrooms?|looking|wanted|preferred|anywhere|maintenance)\b"
    if any(not value or len(value) > 120 or not re.search(r"[a-z]", value, re.I)
           or re.search(forbidden, value, re.I) or re.search(r"\d", value)
           for value in prefix):
        return {}
    result = {"locality": prefix[-1]}
    if len(prefix) == 2:
        result["society_name"] = prefix[0]
    return result


def scan(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    text = text or ""

    bhk = resolve_bhk(text)
    if bhk: out["BHK"] = bhk

    m = (re.search(r"(?:rent|rental)\D{0,12}?(?:rs\.?|inr|₹)?\s*(\d[\d,]*\.?\d*)\s*(k|lakh|l)?\b", text, re.I)
         or re.search(r"(?:rs\.?|inr|₹)\s*(\d[\d,]*)\s*(k)?\b", text, re.I))
    if m:
        v = _scale(m.group(1), m.group(2) if m.lastindex and m.lastindex > 1 else "")
        if 3000 <= int(v) <= 100000000: out["monthly_rent"] = v

    # Area (Zeid, 24 Nov 2026 6:57 PM and 7:03 PM): a labelled carpet or built-up
    # value goes to its own column; an unlabelled "Sqft" figure is the CARPET area.
    _unit = r"(?:\(?\s*(?:sq\.?\s*ft\.?|sqft|sft)\s*\)?)?"
    for key, pat in (("carpet_area", r"\bcarpet(?:[\s\-]*area)?\s*" + _unit + r"\s*[:\-=]*\s*(\d{3,5})"),
                     ("built_up_area", r"(?<!super\s)(?<!super-)\bbuilt[\s\-]*up(?:[\s\-]*area)?\s*" + _unit + r"\s*[:\-=]*\s*(\d{3,5})")):
        m = re.search(pat, text, re.I)
        if m: out[key] = m.group(1)
    if "carpet_area" not in out and "built_up_area" not in out:
        m = re.search(r"sq\.?\s*ft\.?\s*[:\-]\s*(\d{3,5})|sqft\s*[:\-]\s*(\d{3,5})", text, re.I) or re.search(r"\b(\d{3,5})\s*(?:sq\.?\s*ft|sqft|sft)\b", text, re.I)
        if m: out["carpet_area"] = next(g for g in m.groups() if g)

    m = re.search(r"floor\s*[:\-]\s*(g|ground|\d{1,2})\s*(?:/|of)\s*(\d{1,2})", text, re.I)
    if m:
        out["floor_number"] = "0" if m.group(1).lower() in {"g","ground"} else m.group(1)
        out["total_floors"] = m.group(2)
    else:
        # A labelled single floor is complete without a total-floor count.
        # Anchor the entire line so ranges, alternatives and qualifiers cannot
        # silently become one exact floor. Existing x/y and prose paths stay.
        labelled = re.findall(r"^[ \t]*floor[ \t]*[:=-][ \t]*(\d{1,2})(?:st|nd|rd|th)?[ \t]*$", text, re.I | re.M)
        if len(set(labelled)) == 1:
            out["floor_number"] = str(int(labelled[0]))
        m = re.search(r"\b(\d{1,2})[ \t]*(?:st|nd|rd|th)?[ \t]*floor\b", text, re.I)
        if m:
            out["floor_number"] = m.group(1)
            tail = text[m.end():m.end()+25]
            n = re.search(r"(?:out of|of|/)\s*(\d{1,2})", tail, re.I)
            if n: out["total_floors"] = n.group(1)

    patterns = {
        "bathrooms": r"\b(\d)[ \t]*(?:(?!(?:bhk|with|and|no|without|bath|balcon)\w*\b)[A-Za-z-]+[ \t]+){0,2}(?:bath|bathroom|toilet|washroom)s?\b",
        "balconies": r"\b(\d+(?:\.\d+)?)[ \t]*(?:(?!(?:bhk|with|and|no|without|bath|balcon)\w*\b)[A-Za-z-]+[ \t]+){0,2}balcon(?:y|ies)\b",
        "covered_parking": r"(\d)\s*covered\s*parking",
        "open_parking": r"(\d)\s*open\s*parking",
    }
    for key, pat in patterns.items():
        m = re.search(pat, text, re.I)
        if m: out[key] = m.group(1)

    # A singular, explicitly mentioned "Balcony" means one balcony when no
    # numeric balcony count was supplied. Negative wording must not invent one.
    if "balconies" not in out:
        has_negative_balcony = re.search(r"\b(?:no|without)\s+(?:a\s+)?balcony\b", text, re.I)
        has_singular_balcony = re.search(r"\b(?:with\s+)?balcony\b", text, re.I)
        if has_singular_balcony and not has_negative_balcony:
            out["balconies"] = "1"

    marker_society, marker_landmark, marker_maps = _marker_candidates(text)
    society=_first_line_value(text, (r"society\s*name", r"society", r"apartment\s*name", r"community\s*name", r"building\s*name")) or marker_society
    landmark=_first_line_value(text, (r"landmark",)) or marker_landmark
    locality=_first_line_value(text, (r"property\s*location", r"location", r"locality", r"area"))
    prose = prose_location(text)
    locality = locality or prose.get("locality", "")
    society = society or prose.get("society_name", "")
    subtype=resolve_property_subtype(text)
    direct = {
        "internal_property_type": resolve_internal_property_type(text),
        "society_name": society,
        "landmark": landmark,
        "locality": locality,
        "property_subtype": subtype,
        "property_highlights": _first_line_value(text, (r"property\s*highlights", r"highlights")),
        "age_of_property_years": _first_line_value(text, (r"age\s*of\s*property", r"property\s*age")),
        "google_maps_url": marker_maps or MapsLinks.extract_url(text),
    }
    for key, value in direct.items():
        if value: out[key] = value

    maintenance, included = resolve_maintenance(text)
    if maintenance:
        out["maintenance"] = maintenance
        out["maintenance_included"] = included

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
