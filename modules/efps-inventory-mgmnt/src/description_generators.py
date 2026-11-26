"""Independent EFPS channel description formatters.

All formatters consume canonical Housing Listings facts plus original intake
text. They do not extract or invent property facts and do not publish.
"""
from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse

WHATSAPP_GROUP_LINK = "https://chat.whatsapp.com/FxOPO0xAOsD6lNwPcIDdFM"
CONTACT_NUMBER = "91483 38801"


def _text(row, key):
    value = row.get(key)
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return str(value or "").strip()


def _money(value):
    try:
        amount = Decimal(str(value).replace(",", "").strip())
    except (InvalidOperation, TypeError, ValueError):
        return ""
    if amount <= 0:
        return ""
    whole = str(int(amount))
    if len(whole) <= 3:
        return whole
    head, tail = whole[:-3], whole[-3:]
    groups = []
    while head:
        groups.insert(0, head[-2:])
        head = head[:-2]
    return ",".join(groups + [tail])


def _compact(value):
    try:
        amount = Decimal(str(value).replace(",", "").strip())
    except (InvalidOperation, TypeError, ValueError):
        return str(value or "").strip()
    if amount >= 100000:
        text = format(amount / Decimal(100000), "f")
        return (text.rstrip("0").rstrip(".") if "." in text else text) + "L"
    if amount >= 1000:
        text = format(amount / Decimal(1000), "f")
        return (text.rstrip("0").rstrip(".") if "." in text else text) + "K"
    return format(amount, "f").rstrip("0").rstrip(".") if "." in format(amount, "f") else format(amount, "f")


def _short_maps_link(raw_text):
    # Only preserve the owner's original short Maps URL from the submitted text.
    for candidate in re.findall(r"https?://[^\s<>]+", str(raw_text or ""), flags=re.I):
        candidate = candidate.rstrip(".,);]")
        parsed = urlparse(candidate)
        host = (parsed.hostname or "").lower()
        if parsed.scheme == "https" and (
            host in {"maps.app.goo.gl", "share.google"}
            or (host == "goo.gl" and parsed.path.startswith("/maps"))
        ):
            return candidate
    return ""


def _raw_maps_url(raw_text):
    """Return the first original Google Maps URL exactly as supplied at intake."""
    for candidate in re.findall(r"https?://[^\s<>]+", str(raw_text or ""), flags=re.I):
        candidate = candidate.rstrip(".,);]")
        parsed = urlparse(candidate)
        host = (parsed.hostname or "").lower()
        is_google_maps = (
            host in {"maps.app.goo.gl", "share.google", "maps.google.com"}
            or (host == "goo.gl" and parsed.path.startswith("/maps"))
            or (host.endswith(".google.com") and "/maps" in parsed.path)
            or (host.endswith(".google.co.in") and "/maps" in parsed.path)
        )
        if parsed.scheme == "https" and is_google_maps:
            return candidate
    return ""


def _availability(raw_text):
    text = str(raw_text or "")
    match = re.search(r"\b(?:available\s+from|available\s+on|availability)\s*[:\-]\s*([^\n\r]+)", text, re.I)
    if not match:
        if re.search(r"\b(?:ready\s+to\s+occupy|immediately\s+available|available\s+immediately)\b", text, re.I):
            return "Ready to Occupy"
        return ""
    value = match.group(1).strip(" .;")
    if re.search(r"\b(?:now|immediate|immediately|ready\s+to\s+occupy)\b", value, re.I):
        return "Ready to Occupy"
    return value


def _pets(raw_text):
    text = str(raw_text or "")
    if re.search(r"\b(?:pets?\s*(?::|=|-)?\s*(?:are\s*)?allowed|pet\s*friendly|pets?\s*(?::|=|-)?\s*welcome)\b", text, re.I):
        return "Allowed"
    if re.search(r"\b(?:no\s+pets?|pets?\s*(?::|=|-)?\s*(?:are\s*)?not\s+allowed|pets?\s*(?::|=|-)?\s*prohibited)\b", text, re.I):
        return "Not Allowed"
    return ""

def _facebook_availability(raw_text):
    value = _availability(raw_text)
    if not value or value == "Ready to Occupy":
        return value
    for fmt in ("%d %B %Y", "%d %b %Y", "%B %d, %Y", "%b %d, %Y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            parsed = datetime.strptime(value, fmt).date()
            return "" if parsed < date.today() else value
        except ValueError:
            continue
    return value



def _features(row, raw_text):
    raw = str(raw_text or "")
    features = []
    if re.search(r"\bprivate\s+terrace\b", raw, re.I):
        features.append("private terrace")
    if re.search(r"\butility\b", raw, re.I):
        features.append("Utility")
    if re.search(r"\bseparate\s+kitchen\b", raw, re.I):
        features.append("separate kitchen")
    if re.search(r"\b(?:large|spacious)\s+balcon(?:y|ies)\b", raw, re.I):
        features.append("large balcony")
    elif _text(row, "balconies") and _text(row, "balconies") not in {"0", "0.0"}:
        features.append(f"{_compact(row['balconies'])} balcony" if _text(row, "balconies") == "1" else f"{_compact(row['balconies'])} balconies")
    attached = re.search(r"\b(\d+)\s+attached\s+bathrooms?\b", raw, re.I)
    if attached:
        features.append(f"{attached.group(1)} attached bathrooms")
    elif _text(row, "bathrooms"):
        count = _compact(row["bathrooms"])
        features.append(f"{count} bathroom" + ("" if count == "1" else "s"))
    return features


def build_whatsapp_group_description(row, raw_text, *, verified_society_name="", maps_verified=False, issues=None):
    """WhatsApp Group v8.0 with original Raw Property Data link fallback."""
    issues = issues if issues is not None else []
    furnish = _text(row, "furnish_type")
    bhk = _text(row, "BHK")
    locality = _text(row, "locality")
    raw_maps_link = _raw_maps_url(raw_text)
    if not furnish or not bhk or (not locality and (maps_verified or not raw_maps_link)):
        issues.append("WhatsApp Group description not generated: furnishing, BHK or verified locality is missing.")
        return ""

    features = _features(row, raw_text)
    # Lead with the strongest supplied feature, then add one useful bathroom /
    # balcony detail where it fits. Never infer a feature from BHK count.
    primary_features = [
        feature for feature in features
        if feature.casefold() in {"private terrace", "utility", "separate kitchen", "large balcony"}
    ]
    bathroom_features = [feature for feature in features if "bathroom" in feature.casefold()]
    balcony_features = [feature for feature in features if "balcony" in feature.casefold()]
    title_features = (primary_features + bathroom_features + balcony_features)[:2]
    title_suffix = " with " + " & ".join(feature.title() for feature in title_features) if title_features else ""
    title = f"*👉{furnish} {bhk}{title_suffix}*"
    lines = [title]

    rent = _compact(row.get("monthly_rent"))
    if rent:
        lines.append(f"Rent: {rent}")
    included = _text(row, "maintenance_included").lower() in {"yes", "true", "1"}
    maintenance = _text(row, "maintenance")
    if included:
        lines.append("Maintenance: Included")
    elif maintenance:
        lines.append(f"Maintenance: {_compact(maintenance)}")
    deposit = _compact(row.get("security_deposit"))
    if deposit:
        lines.append(f"Deposit: {deposit}")
    sqft = _text(row, "built_up_area") or _text(row, "carpet_area")
    if sqft:
        lines.append(f"Sqft: {sqft}")
    floor = _text(row, "floor_number")
    total_floors = _text(row, "total_floors")
    if floor:
        lines.append(f"Floor: {floor}/{total_floors}" if total_floors and "/" not in floor else f"Floor: {floor}")
    available = _availability(raw_text)
    if available:
        lines.append(f"Available from: {available}")
    tenant = _text(row, "preferred_tenant_type")
    if tenant:
        lines.append(f"Preferred tenant: {'Open For All' if tenant.lower() in {'anyone', 'open for all'} else tenant}")
    pet = _pets(raw_text)
    if pet:
        lines.append(f"Pets: {pet}")
    property_type = _text(row, "internal_property_type")
    if property_type.lower() == "gated community":
        lines.append("Gated Community")
    elif property_type.lower() == "semi gated":
        lines.append("Semi Gated")
    if locality:
        lines.append(f"Location: *{locality}*")

    # Prefer the original short URL for a verified Group caption. If Maps
    # verification fails, retain the exact Maps URL supplied in Raw Property
    # Data as the user's requested last-resort fallback, but never claim a
    # society or locality was verified from it.
    short_maps_link = _short_maps_link(raw_text)
    if maps_verified and short_maps_link:
        society = _text({"name": verified_society_name}, "name")
        label = society if society and society.casefold() != locality.casefold() else "Landmark"
        lines.extend(["", f"*📍 {label}:*", short_maps_link])
    elif not maps_verified and raw_maps_link:
        # The generic label avoids falsely asserting a society identity.
        # Omit the Location line because the supplied Maps link did not verify it.
        lines = [line for line in lines if not line.startswith("Location: ")]
        lines.extend(["", "*📍 Landmark:*", raw_maps_link])
        issues.append("Maps verification failed; original URL from Raw Property Data retained as an unverified fallback. Locality/society needs review.")
    elif raw_maps_link:
        issues.append("Maps link has no verified original short URL; review required.")
    return "\n".join(lines)


def build_facebook_marketplace_description(row, raw_text):
    """Facebook Marketplace v7.0. Preview text only; never publishes."""
    locality = _text(row, "locality")
    furnish = _text(row, "furnish_type")
    bhk = _text(row, "BHK")
    if not locality or not bhk:
        return ""
    features = _features(row, raw_text)
    internal_type = _text(row, "internal_property_type")
    hook = f"{furnish} {bhk}".strip()
    if internal_type.lower() == "gated community":
        hook = f"Gated Community {bhk}"
    elif features:
        hook = f"{hook} with {features[0]}"
    title = f"🏡 {hook} | {locality}"

    # Keep the location paragraph factual. Use only locality and a verified,
    # non-society landmark explicitly supplied in the original text.
    paragraph_parts = [f"Located in {locality}."]
    # Do not promote an unverified landmark or society name into public copy.
    if features:
        paragraph_parts.append(f"Features include {features[0]}.")
    paragraph = " ".join(paragraph_parts)

    rent = _money(row.get("monthly_rent"))
    if not rent:
        return ""
    maintenance = _text(row, "maintenance")
    included = _text(row, "maintenance_included").lower() in {"yes", "true", "1"}
    if included:
        rent_line = f"Rent: ₹{rent} (Maintenance Included)"
    elif maintenance and re.search(r"\bwater\b", maintenance, re.I):
        rent_line = f"Rent: ₹{rent} + Water Charges"
    elif maintenance:
        rent_line = f"Rent: ₹{rent} + Maintenance"
    else:
        rent_line = f"Rent: ₹{rent}"

    lines = [title, "", paragraph, "", rent_line]
    available = _facebook_availability(raw_text)
    if available:
        lines.append(available if available == "Ready to Occupy" else f"Available from {available}")
    if _text(row, "preferred_tenant_type").lower() in {"anyone", "open for all"}:
        lines.append("Open for All")
    if _pets(raw_text) == "Allowed":
        lines.append("Pet Friendly")
    lines.extend([
        "",
        f"🔗 For more properties, join our WhatsApp group: {WHATSAPP_GROUP_LINK}",
        "",
        f"☎️ {CONTACT_NUMBER}",
        "Brokerage applicable.",
    ])
    return "\n".join(lines)
