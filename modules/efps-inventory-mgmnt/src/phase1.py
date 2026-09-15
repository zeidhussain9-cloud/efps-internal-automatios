"""Canonical Phase-1 inventory boundary.

Phase-1 is deliberately deterministic: raw source -> candidate extraction ->
canonical resolution -> normalization/dependencies -> deterministic Maps URL
extraction -> deterministic validation. Google Maps network resolution, AI
verification, and AI beautification happen only after this boundary.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import re

from shared.google_maps import GoogleMapsClient
from shared.google_sheets import schema

from . import extract, normalize, validate
from .community_property_types import resolve_known_community_property_type
from .source_segments import split_source_messages

CANONICAL_PROPERTY_TYPES = ("Gated Community", "Semi Gated", "Standalone")
GATED_AMENITIES = "Club House, Lift, Gym, CCTV, Power Backup, Swimming Pool, Garden, Sports, Kids Area"
SEMI_GATED_AMENITIES = "Security, Lift, CCTV, Power Backup"
STANDALONE_AMENITIES = "-"
PLACEHOLDERS = {"", "-", "—", "n/a", "na", "none", "nil", "not available", "not mentioned"}
REPORT_UNRESOLVED_FIELDS = (
    "internal_property_type",
    "locality",
)


@dataclass(frozen=True)
class Phase1Result:
    row: dict[str, str]
    issues: tuple[str, ...]
    report: dict[str, Any]


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[*_`~]", "", str(value or ""))).strip(" -–—")


def _segments(text: str) -> list[str]:
    return split_source_messages(text)


def _label_candidates(text: str, labels: str) -> list[tuple[int, int, str]]:
    pattern = re.compile(rf"\b(?:{labels})\b\s*(?::|[-–—|=])\s*([^|\n<]+)", re.I)
    found: list[tuple[int, int, str]] = []
    for segment_index, segment in enumerate(_segments(text)):
        for match in pattern.finditer(segment):
            value = _clean(match.group(1))
            if value:
                found.append((segment_index, match.start(), value))
    return found


def resolve_internal_property_type(text: str) -> str:
    """Resolve only the three canonical internal property types.

    Direct user-labelled evidence is authoritative, later source segments win,
    then explicit boolean gating evidence, then weaker wording, then the
    adjudicated community registry. Missing evidence remains unresolved; it is
    never converted to Standalone by absence alone.
    """
    explicit: list[tuple[int, int, str]] = []
    for segment_index, position, value in _label_candidates(
        text,
        r"internal\s*property\s*type|property\s*(?:type|classification)|gating\s*type",
    ):
        low = value.lower()
        if "semi" in low and "gated" in low:
            explicit.append((segment_index, position, "Semi Gated"))
        elif re.search(r"\bgated\b", low):
            explicit.append((segment_index, position, "Gated Community"))
        elif "stand" in low:
            explicit.append((segment_index, position, "Standalone"))
    if explicit:
        return sorted(explicit)[-1][2]

    boolean: list[tuple[int, int, str]] = []
    pattern = re.compile(
        r"\b(?P<label>semi[-\s]*gated(?:\s+community)?|gated(?:\s+community)?)\s*(?::|=|\||-)\s*(?P<value>[^|\n<]+)",
        re.I,
    )
    yes = {"yes", "y", "true", "1", "allowed", "community", "society", "property"}
    no = {"no", "n", "false", "0", "not allowed", "not permitted", "none"}
    for segment_index, segment in enumerate(_segments(text)):
        for match in pattern.finditer(segment):
            value = _clean(match.group("value")).lower()
            if value in yes:
                canonical = "Semi Gated" if "semi" in match.group("label").lower() else "Gated Community"
                boolean.append((segment_index, match.start(), canonical))
            elif value in no:
                boolean.append((segment_index, match.start(), "Standalone"))
    if boolean:
        return sorted(boolean)[-1][2]

    generic: list[tuple[int, int, str]] = []
    for segment_index, segment in enumerate(_segments(text)):
        for match in re.finditer(r"\bsemi[-\s]*gated\b", segment, re.I):
            generic.append((segment_index, match.start(), "Semi Gated"))
        for match in re.finditer(r"\bgated\s*(?:community|society|property)\b", segment, re.I):
            generic.append((segment_index, match.start(), "Gated Community"))
        for match in re.finditer(r"\b(?:independent\s+(?:house|floor)|farm\s*house|stand[-\s]*alone)\b", segment, re.I):
            generic.append((segment_index, match.start(), "Standalone"))
    if generic:
        return sorted(generic)[-1][2]

    source = extract.scan(text)
    society = str(source.get("society_name", "") or "").strip()
    if society:
        known = resolve_known_community_property_type(society)
        if known in CANONICAL_PROPERTY_TYPES:
            return known
    return ""


def resolve_parking_society_amenities(row: dict[str, str]) -> dict[str, str]:
    """Resolve the coupled property-type/parking/amenities state once."""
    property_type = str(row.get("internal_property_type", "") or "").strip()
    covered = str(row.get("covered_parking", "") or "").strip()
    open_parking = str(row.get("open_parking", "") or "").strip()

    if property_type in {"Gated Community", "Semi Gated"} and not covered:
        covered = "1"
    if not open_parking:
        open_parking = "-"

    if not str(row.get("society_amenities", "") or "").strip():
        if property_type == "Gated Community":
            amenities = GATED_AMENITIES
        elif property_type == "Semi Gated":
            amenities = SEMI_GATED_AMENITIES
        elif property_type == "Standalone":
            amenities = STANDALONE_AMENITIES
        else:
            amenities = ""
    else:
        amenities = str(row["society_amenities"]).strip()

    return {
        "internal_property_type": property_type,
        "covered_parking": covered,
        "open_parking": open_parking,
        "society_amenities": amenities,
    }


def apply_location_contract(row: dict[str, str]) -> dict[str, bool]:
    """Apply final deterministic location fallbacks and return review flags."""
    locality = str(row.get("locality", "") or "").strip()
    landmark = str(row.get("landmark", "") or "").strip()
    society = str(row.get("society_name", "") or "").strip()

    if GoogleMapsClient.is_maps_url(landmark):
        row["landmark"] = ""
        landmark = ""

    if not landmark and locality:
        row["landmark"] = locality

    society_fallback = False
    if society.lower() in PLACEHOLDERS:
        society = ""
    if not society and locality:
        row["society_name"] = locality
        society_fallback = True

    return {"society_name_locality_fallback": society_fallback}


def _report(row: dict[str, str], *, issues: list[str], review_flags: list[str], trace: dict[str, Any]) -> dict[str, Any]:
    populated = [name for name in schema.NAMES if str(row.get(name, "") or "").strip()]
    blank = [name for name in schema.NAMES if not str(row.get(name, "") or "").strip()]
    unresolved = [name for name in REPORT_UNRESOLVED_FIELDS if not str(row.get(name, "") or "").strip()]
    return {
        "populated_fields": populated,
        "blank_fields": blank,
        "unresolved_fields": unresolved,
        "review_flags": review_flags,
        "issues": list(issues),
        "trace": trace,
    }


def project(raw_text: str, row: dict[str, Any] | None = None) -> dict[str, str]:
    """Perform the deterministic projection only; never calls AI or Maps network."""
    base = {name: "" for name in schema.NAMES}
    if row is not None:
        for name in (
            "listing_id", "status", "intake_status", "onboarded_on", "raw_message_text",
            "whatsapp_contact_link", "whatsapp_group_link", "transaction_type", "city", "source_group",
            "cloudinary_image_urls", "listing_state", "posted_url", "posted_at", "error_notes",
            "meta_catalog_id", "meta_catalog_status", "inventory_locked",
        ):
            if name in base:
                base[name] = str(row.get(name, "") or "")
    base["raw_message_text"] = raw_text or base.get("raw_message_text", "")
    extracted = extract.scan(raw_text)
    base.update({name: value for name, value in extracted.items() if name in schema.BY_NAME})
    base["internal_property_type"] = resolve_internal_property_type(raw_text)
    base = normalize.normalize(base, raw_text, resolved_internal_property_type=base["internal_property_type"])

    coupled = resolve_parking_society_amenities(base)
    for name, value in coupled.items():
        base[name] = value

    # Deterministic Maps URL extraction is always executed explicitly here.
    maps_url = GoogleMapsClient.extract_url(raw_text)
    if maps_url:
        base["google_maps_url"] = maps_url

    apply_location_contract(base)
    if set(base) != set(schema.NAMES):
        raise ValueError("Phase-1 projection must contain exactly the canonical 48 fields")
    return base


def run_phase1(raw_text: str, *, row: dict[str, Any] | None = None) -> Phase1Result:
    """Canonical Phase-1 runner shared by batch rows and closed webhook sessions."""
    projected = project(raw_text, row=row)
    issues = validate.validate(projected)
    if issues:
        projected["status"] = "Needs Review"
    else:
        projected["status"] = "Pending"
    projected["intake_status"] = "Processed"

    trace = {
        "source_segments": split_source_messages(raw_text),
        "extracted_candidates": extract.scan(raw_text),
        "resolved": {
            "BHK": projected.get("BHK", ""),
            "maintenance": projected.get("maintenance", ""),
            "maintenance_included": projected.get("maintenance_included", ""),
            "internal_property_type": projected.get("internal_property_type", ""),
            "property_subtype": projected.get("property_subtype", ""),
            "google_maps_url": projected.get("google_maps_url", ""),
        },
    }
    review_flags: list[str] = []
    if projected.get("society_name", "").strip() and projected.get("society_name", "").strip() == projected.get("locality", "").strip():
        source_society = str(extract.scan(raw_text).get("society_name", "") or "").strip()
        if not source_society or source_society.lower() in PLACEHOLDERS:
            review_flags.append("society_name_locality_fallback")
    if not projected.get("internal_property_type", "").strip():
        review_flags.append("internal_property_type_unresolved")
    return Phase1Result(
        row=projected,
        issues=tuple(issues),
        report=_report(projected, issues=issues, review_flags=review_flags, trace=trace),
    )
