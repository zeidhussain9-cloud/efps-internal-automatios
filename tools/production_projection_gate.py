"""Fail-closed field-contract gate for the live 25-row production projection.

This is read-only. It uses raw_message_text as source authority and does not
compare deterministic correctness to persisted Stage-2 values. Optional or
enrichment-owned blanks, especially pincode, are not treated as failures.
"""
from __future__ import annotations

import argparse
import importlib
import re
import sys
from pathlib import Path

from shared.google_sheets import schema
from shared.google_sheets.client import GoogleSheetsClient
from shared.google_maps import GoogleMapsClient

MODULE_ROOT = Path(__file__).resolve().parents[1] / "modules" / "efps-inventory-mgmnt"
sys.path.insert(0, str(MODULE_ROOT))
pipeline = importlib.import_module("src.pipeline")
field_resolution = importlib.import_module("src.field_resolution")

PLACEHOLDERS = {"", "*", "-", "—", "n/a", "na", "none", "not available", "not mentioned", "nil"}
TARGET_FIELDS = {
    "internal_property_type",
    "property_subtype",
    "society_name",
    "locality",
    "pincode",
    "landmark",
    "google_maps_url",
    "maintenance",
    "society_amenities",
    "covered_parking",
    "property_highlights",
}
GREEN_GUARD_FIELDS = {
    "raw_message_text",
    "furnish_type",
    "flat_furnishings",
    "monthly_rent",
    "maintenance_included",
    "security_deposit",
    "preferred_tenant_type",
    "bachelor_preference",
    "pet_friendly",
    "balconies",
    "catalog_title",
}


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[*_`~]", "", str(value or ""))).strip(" -–—")


def line_value(raw: str, labels: tuple[str, ...]) -> str:
    for label in labels:
        match = re.search(rf"\b(?:{label})\b\s*(?::|[-–—|=])\s*([^|\n<]+)", raw, re.I)
        if match:
            value = clean(match.group(1))
            if value and value.lower() not in PLACEHOLDERS:
                return value
    return ""


def marker_society(raw: str) -> str:
    match = re.search(r"📍\s*([^:\n|]+?)\s*:\s*", raw or "", re.I)
    if not match:
        return ""
    value = clean(match.group(1))
    return "" if re.fullmatch(r"(?:landmark|location)", value, re.I) else value


def raw_society(raw: str) -> str:
    return line_value(raw, (r"society\s*name", r"society", r"apartment\s*name", r"community\s*name", r"building\s*name")) or marker_society(raw)


def raw_locality(raw: str) -> str:
    return line_value(raw, (r"property\s*location", r"location", r"locality", r"area"))


def canonical_maps_url(raw: str) -> str:
    return GoogleMapsClient.extract_url(raw)


def check_row(row_number: int, raw: str, model: dict[str, str]) -> list[str]:
    failures: list[str] = []
    expected_loc = raw_locality(raw)
    if expected_loc and model.get("locality", "").strip() != expected_loc:
        failures.append(f"locality expected {expected_loc!r}, got {model.get('locality')!r}")

    expected_society = raw_society(raw)
    if expected_society and model.get("society_name", "").strip() != expected_society:
        failures.append(f"society_name expected {expected_society!r}, got {model.get('society_name')!r}")

    expected_url = canonical_maps_url(raw)
    actual_url = model.get("google_maps_url", "").strip()
    if expected_url and actual_url != expected_url:
        failures.append(f"google_maps_url expected exact source URL {expected_url!r}, got {actual_url!r}")

    landmark = model.get("landmark", "").strip()
    if GoogleMapsClient.is_maps_url(landmark):
        failures.append("landmark contains a Maps URL")

    source_subtype = field_resolution.resolve_property_subtype(raw)
    if source_subtype and model.get("property_subtype", "").strip() != source_subtype:
        failures.append(f"property_subtype expected {source_subtype!r}, got {model.get('property_subtype')!r}")

    expected_maintenance, expected_included = field_resolution.resolve_maintenance(raw)
    if expected_maintenance and model.get("maintenance", "").strip() != expected_maintenance:
        failures.append(f"maintenance expected {expected_maintenance!r}, got {model.get('maintenance')!r}")
    if expected_included and model.get("maintenance_included", "").strip() != expected_included:
        failures.append(f"maintenance_included expected {expected_included!r}, got {model.get('maintenance_included')!r}")

    source_pet = model.get("pet_friendly", "").strip()
    expected_pet = "No" if re.search(r"\b(?:pets?|animals?)\s*(?::|=|-)?\s*(?:are\s*)?(?:not\s*allowed|not\s*permitted|prohibited|banned)\b|\b(?:no|without)\s+pets?\b", raw, re.I) else "Yes"
    if source_pet != expected_pet:
        failures.append(f"pet_friendly expected {expected_pet!r}, got {source_pet!r}")

    balcony_count = re.search(r"\b(\d+(?:\.\d+)?)\s*balcon(?:y|ies)\b", raw, re.I)
    if balcony_count and model.get("balconies", "").strip() != balcony_count.group(1):
        failures.append(f"balconies expected {balcony_count.group(1)!r}, got {model.get('balconies')!r}")
    elif not balcony_count and re.search(r"\b(?:with\s+)?balcony\b", raw, re.I) and model.get("balconies", "").strip() != "1":
        failures.append(f"balconies expected '1', got {model.get('balconies')!r}")

    if "property highlights:" in raw.lower() or "highlights:" in raw.lower():
        explicit = line_value(raw, (r"property\s*highlights", r"highlights"))
        if explicit and model.get("property_highlights", "").strip() != explicit:
            failures.append(f"property_highlights expected explicit {explicit!r}, got {model.get('property_highlights')!r}")

    pincode = model.get("pincode", "").strip()
    if pincode and not re.fullmatch(r"\d{6}", pincode):
        failures.append(f"pincode is nonblank but invalid: {pincode!r}")

    property_type = model.get("internal_property_type", "").strip()
    if property_type not in {"", "Gated Community", "Semi Gated", "Standalone"}:
        failures.append(f"invalid internal_property_type {property_type!r}")

    if property_type == "Gated Community":
        if model.get("society_amenities", "").strip() != "Club House, Lift, Gym, CCTV, Power Backup, Swimming Pool, Garden, Sports, Kids Area":
            failures.append("society_amenities does not match Gated Community dependency")
        if not model.get("covered_parking", "").strip():
            failures.append("covered_parking blank for Gated Community")
    elif property_type == "Semi Gated":
        if model.get("society_amenities", "").strip() != "Security, Lift, CCTV, Power Backup":
            failures.append("society_amenities does not match Semi Gated dependency")
        if not model.get("covered_parking", "").strip():
            failures.append("covered_parking blank for Semi Gated")
    elif property_type == "Standalone":
        if not model.get("covered_parking", "").strip() and model.get("society_amenities", "").strip() not in {"", "-"}:
            failures.append("Standalone dependency produced a noncanonical amenity bundle")
    else:
        if model.get("society_amenities", "").strip() not in {"", "-"}:
            failures.append("unresolved property type must not invent a society amenity bundle")

    if model.get("raw_message_text", "").strip() != raw.strip():
        failures.append("raw_message_text changed during projection")
    furnish = "Fully Furnished" if re.search(r"\bfully\s*furnish", raw, re.I) else "Semi Furnished" if re.search(r"\bsemi[-\s]*furnish", raw, re.I) else ""
    if furnish and model.get("furnish_type", "").strip() != furnish:
        failures.append(f"furnish_type regressed: expected {furnish!r}, got {model.get('furnish_type')!r}")

    known_type = field_resolution.resolve_internal_property_type(raw)
    if known_type and property_type != known_type:
        failures.append(f"internal_property_type expected {known_type!r}, got {property_type!r}")

    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-row", type=int, default=2)
    parser.add_argument("--end-row", type=int, default=26)
    args = parser.parse_args()
    if args.start_row < 2 or args.end_row < args.start_row:
        raise SystemExit("invalid row range")

    client = GoogleSheetsClient()
    rows = client.read_range(schema.SHEET_ID, schema.WORKSHEET_NAME, f"A{args.start_row}:AV{args.end_row}")
    total_failures = 0
    rows_with_failures = 0
    print("EFPS PRODUCTION PROJECTION CONTRACT GATE")
    print(f"ROWS: {args.start_row}-{args.end_row} | SOURCE: raw_message_text | SHEET WRITES: 0")

    for offset, values in enumerate(rows):
        row_number = args.start_row + offset
        row = schema.row_to_mapping(values)
        raw = str(row.get("raw_message_text", "") or "")
        if not raw.strip():
            continue
        model = pipeline.deterministic(raw, row=row)
        failures = check_row(row_number, raw, model)
        if failures:
            rows_with_failures += 1
            total_failures += len(failures)
            print(f"ROW {row_number} {row.get('listing_id','')}: FAIL")
            for failure in failures:
                print(f"  - {failure}")
        else:
            print(f"ROW {row_number} {row.get('listing_id','')}: PASS")

    print(f"ROWS WITH FAILURES: {rows_with_failures}")
    print(f"CONTRACT FAILURES: {total_failures}")
    print("PINCODE: BLANK IS NON-BLOCKING")
    if total_failures:
        print("PRODUCTION PROJECTION CONTRACT GATE: FAIL")
        return 1
    print("PRODUCTION PROJECTION CONTRACT GATE: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
