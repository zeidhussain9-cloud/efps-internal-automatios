"""Deterministic normalization for Stage 2 property processing.

Rules are mechanical and source-grounded. This module must not invent property
facts. Explicit source values win over defaults.
"""
from __future__ import annotations
import re

FIXED = {
    "transaction_type": "Rent",
    "city": "Bengaluru",
    "whatsapp_contact_link": "https://wa.me/919148338801",
    "whatsapp_group_link": "https://chat.whatsapp.com/FxOPO0xAOsD6lNwPcIDdFM",
}

NUMERIC_FIELDS = {
    "pincode", "built_up_area", "carpet_area", "age_of_property_years",
    "total_floors", "bathrooms", "balconies", "open_parking",
    "monthly_rent", "security_deposit",
}

SEMI_FURNISHED_DEFAULTS = ("Wardrobe", "Modular Kitchen", "Geyser", "Fan", "Light")
FULLY_FURNISHED_DEFAULTS = SEMI_FURNISHED_DEFAULTS + (
    "Fridge", "Washing Machine", "TV", "Sofa", "Bed", "Dining Table",
)
CARPET_RATIO = 0.90

PORTAL_SUBTYPE_MAP = {
    "Triplex Villa": "Villa",
    "Complex Villa": "Villa",
    "Villa Complex": "Villa",
    "Triplex": "Independent House",
    "Builder Floor": "Independent Floor",
    "Independent Building": "Independent House",
}
NO_FLOOR_SUBTYPES = {"Villa", "Independent House", "Farm House", "Duplex"}
STANDALONE_SUBTYPES = {"independent house", "independent floor", "farm house"}

GATED_COMMUNITY_DEFAULTS = (
    "Lift", "Gym", "CCTV", "Power Backup", "Swimming Pool", "Gated Community",
    "Club House", "Garden", "Sports", "Kids Area", "Community Hall",
)
SEMI_GATED_AMENITIES = ("CCTV", "Power Backup", "Regular Water Supply")

_GATED_KW = re.compile(r"\bgated\s*(?:community|society)\b", re.I)
_SEMI_GATED_KW = re.compile(r"\bsemi[-\s]*gated\b", re.I)
_STANDALONE_WORDS = re.compile(
    r"\b(villa|independent house|independent floor|builder floor|farm ?house|"
    r"duplex|triplex|penthouse|studio)\b", re.I
)
_RK_RE = re.compile(r"\b(\d)\s*rk\b", re.I)
_MAINTENANCE_LINE = re.compile(r"maintenance\s*:\s*([^\n]+)", re.I)
_MAINTENANCE_NUMERIC = re.compile(r"^[\d.,]+\s*(k|l|lakh|lakhs)?\.?$", re.I)
_UTILITY = re.compile(r"\butilit(?:y|ies)\b", re.I)
_SLACK_LINK = re.compile(r"^<(?P<url>[^|>]+)(\|[^>]*)?>$")
_MONTHS = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*(?:months?|mnths?|mos?)\s*$", re.I)


def strip_slack_markup(value: str) -> str:
    match = _SLACK_LINK.match(str(value or "").strip())
    return match.group("url").strip() if match else str(value or "").strip()


def clean_number(value: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    cleaned = re.sub(r"[₹,\s]", "", raw)
    cleaned = re.sub(r"(?:sq\.?\s*ft\.?|sqft|sft|rs\.?|inr)", "", cleaned, flags=re.I)
    if re.fullmatch(r"\d+(?:\.\d+)?", cleaned):
        return cleaned.rstrip("0").rstrip(".") if "." in cleaned else cleaned
    return raw


def resolve_deposit(value: str, monthly_rent: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    match = _MONTHS.match(raw)
    if not match:
        return clean_number(raw)
    rent = clean_number(monthly_rent)
    if not re.fullmatch(r"\d+(?:\.\d+)?", rent):
        return raw
    return str(int(float(match.group(1)) * float(rent)))


def _verified_in_text(value: str, raw_text: str) -> bool:
    def norm(text: str) -> str:
        return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", str(text or "").lower())).strip()
    needle = norm(value)
    return bool(needle) and needle in norm(raw_text)


def _gating_level_from_text(raw_text: str, row: dict) -> str:
    text = str(raw_text or "").lower()
    subtype = str(row.get("property_subtype", "")).strip().lower()
    if _GATED_KW.search(text):
        return "Gated Community"
    if _SEMI_GATED_KW.search(text):
        return "Semi Gated"
    if subtype in STANDALONE_SUBTYPES:
        return "Standalone"
    return "Standalone"


def set_internal_type(row: dict, raw_text: str) -> dict:
    """Set the three-tier internal type and deterministic amenity defaults."""
    classification = _gating_level_from_text(raw_text, row)
    row["internal_property_type"] = classification
    if not str(row.get("society_amenities", "")).strip():
        if classification == "Gated Community":
            row["society_amenities"] = ", ".join(GATED_COMMUNITY_DEFAULTS)
        elif classification == "Semi Gated":
            row["society_amenities"] = ", ".join(SEMI_GATED_AMENITIES)
        elif classification == "Standalone":
            subtype = str(row.get("property_subtype", "")).strip().lower()
            if subtype and subtype not in STANDALONE_SUBTYPES:
                row["society_amenities"] = ", ".join(SEMI_GATED_AMENITIES)
    return row


def apply_tenant_bachelor_rule(row: dict, raw_text: str) -> dict:
    """Family/family-only forces Not Allowed unless an explicit source value says otherwise."""
    tenant = str(row.get("preferred_tenant_type", "")).strip().lower()
    if tenant not in {"family", "family only"}:
        return row
    current = str(row.get("bachelor_preference", "")).strip()
    if current and _verified_in_text(current, raw_text):
        return row
    row["bachelor_preference"] = "Not Allowed"
    return row


def preserve_stated_maintenance_term(row: dict, raw_text: str) -> dict:
    """Preserve a stated non-numeric maintenance term such as Water Charges."""
    if str(row.get("maintenance", "")).strip():
        return row
    match = _MAINTENANCE_LINE.search(raw_text or "")
    if not match:
        return row
    stated = match.group(1).strip().rstrip(".")
    if not stated or _MAINTENANCE_NUMERIC.match(stated) or stated.lower() == "included":
        return row
    row["maintenance"] = stated
    if not str(row.get("maintenance_included", "")).strip():
        row["maintenance_included"] = "No"
    return row


def default_property_subtype(row: dict, raw_text: str) -> dict:
    """Use Apartment only when a floor is explicitly stated and no standalone form is stated."""
    if str(row.get("property_subtype", "")).strip():
        return row
    if not str(row.get("floor_number", "")).strip():
        return row
    if _STANDALONE_WORDS.search(raw_text or ""):
        return row
    row["property_subtype"] = "Apartment"
    return row


def floor_for_standalone(row: dict) -> dict:
    subtype = str(row.get("property_subtype", "")).strip()
    if subtype in NO_FLOOR_SUBTYPES and not str(row.get("floor_number", "")).strip():
        row["floor_number"] = subtype
    return row


def preserve_rk_wording(row: dict, raw_text: str) -> dict:
    match = _RK_RE.search(raw_text or "")
    if not match:
        return row
    rk_label = f"{match.group(1)} RK"
    for field_name in ("catalog_title", "property_highlights"):
        text = str(row.get(field_name, ""))
        if not text or rk_label.lower() in text.lower():
            continue
        if "studio" in text.lower():
            text = re.sub(r"\bstudio\b", rk_label, text, count=1, flags=re.I)
        else:
            text = f"{text} ({rk_label})".strip()
        row[field_name] = text
    return row


def construct_deterministic_highlights(row: dict, raw_text: str, original_subtype: str) -> list[str]:
    fragments: list[str] = []
    if _UTILITY.search(raw_text or ""):
        fragments.append("Utility area")
    if original_subtype and original_subtype in PORTAL_SUBTYPE_MAP:
        fragments.append(original_subtype)
    floors = [f.strip() for f in str(row.get("floor_number", "")).split(",") if f.strip()]
    if len(floors) >= 2:
        fragments.append(f"Multiple units available (floors {', '.join(floors)})")
    match = _RK_RE.search(raw_text or "")
    if match:
        fragments.append(f"{match.group(1)} RK")
    return list(dict.fromkeys(fragments))


def normalize(row: dict, raw_text: str = "") -> dict:
    out = {k: str(v or "").strip() for k, v in row.items()}
    for key, value in list(out.items()):
        out[key] = strip_slack_markup(value)
    out.update(FIXED)

    for field in NUMERIC_FIELDS:
        if out.get(field):
            out[field] = clean_number(out[field])

    if out.get("security_deposit"):
        out["security_deposit"] = resolve_deposit(row.get("security_deposit", ""), out.get("monthly_rent", ""))

    if out.get("maintenance_included", "").lower() == "yes":
        out["maintenance_included"] = "Yes"
        out["maintenance"] = "0"
    elif out.get("maintenance_included", "").lower() == "no":
        out["maintenance_included"] = "No"

    # The extractor can leave 1 RK/Studio in BHK/subtype; normalize only stated forms.
    val = out.get("BHK", "")
    if val.lower() == "studio" or re.fullmatch(r"1\s*[- ]?\s*rk", val, re.I):
        out["BHK"] = "1 RK"
    else:
        match = re.fullmatch(r"(\d+)\s*[- ]?\s*bhk", val, re.I)
        if match:
            out["BHK"] = f"{match.group(1)} BHK"

    original_subtype = out.get("property_subtype", "")
    if original_subtype in PORTAL_SUBTYPE_MAP:
        out["property_subtype"] = PORTAL_SUBTYPE_MAP[original_subtype]

    default_property_subtype(out, raw_text)
    floor_for_standalone(out)

    if not out.get("flat_furnishings"):
        if out.get("furnish_type") == "Semi Furnished":
            out["flat_furnishings"] = ", ".join(SEMI_FURNISHED_DEFAULTS)
        elif out.get("furnish_type") == "Fully Furnished":
            out["flat_furnishings"] = ", ".join(FULLY_FURNISHED_DEFAULTS)

    if not out.get("carpet_area") and out.get("built_up_area", "").isdigit():
        out["carpet_area"] = str(int(round(int(out["built_up_area"]) * CARPET_RATIO)))

    if not out.get("servant_room"):
        out["servant_room"] = "No"

    preserve_stated_maintenance_term(out, raw_text)
    set_internal_type(out, raw_text)
    apply_tenant_bachelor_rule(out, raw_text)

    fragments = construct_deterministic_highlights(out, raw_text, original_subtype)
    if fragments and not str(out.get("property_highlights", "")).strip():
        out["property_highlights"] = " | ".join(fragments)
    preserve_rk_wording(out, raw_text)
    return out
