"""Deterministic Inventory contract audit helpers.

This tool is intentionally read-only. It exercises canonical deterministic
processing against supplied rows and reports source-backed/historical Sheet
conflicts separately from unresolved deterministic contradictions.
"""
from __future__ import annotations

from collections.abc import Iterable

from shared.google_sheets import schema
from shared.google_sheets.client import GoogleSheetsClient

from modules.efps_inventory_mgmnt_src_adapter import canonical_projection  # type: ignore

# This import shim is replaced by the executable CLI below when loaded from repo root.

RESERVED_FIELDS = set(schema.RESERVED_COLUMNS)
PROTECTED = {"listing_state", "posted_url", "posted_at", "error_notes", "meta_catalog_id", "meta_catalog_status"}


def _same_numeric_maintenance(sheet: str, model: str) -> bool:
    def base(value: str) -> str:
        return value.split(" + ", 1)[0].strip()
    return base(sheet) == base(model) and "+ " in model


def classify_populated_conflict(field: str, sheet: str, model: str, raw: str) -> str:
    """Classify a populated mismatch without treating stale Sheet values as source truth."""
    if field == "maintenance" and _same_numeric_maintenance(sheet, model):
        return "historical_sheet_qualifier_difference"
    if field in {"BHK", "maintenance", "internal_property_type"}:
        return "historical_sheet_value_conflict" if raw.strip() else "unadjudicated_source_conflict"
    return "populated_source_conflict"


def audit_rows(rows: Iterable[dict[str, str]]) -> dict[str, int]:
    counters = {"same": 0, "expected_projection": 0, "lifecycle_projection": 0, "formatting_only": 0, "historical_sheet_conflict": 0, "historical_sheet_qualifier_difference": 0, "unadjudicated_source_conflict": 0, "populated_source_conflict": 0, "protected_column_change": 0}
    for row in rows:
        raw = str(row.get("raw_message_text", "") or "")
        model = canonical_projection(raw, row)
        for field in schema.NAMES:
            if field in RESERVED_FIELDS:
                continue
            sheet = str(row.get(field, "") or "").strip(); projected = str(model.get(field, "") or "").strip()
            if sheet == projected:
                counters["same"] += 1
            elif field in {"status", "intake_status"}:
                counters["lifecycle_projection"] += 1
            elif not sheet and projected:
                counters["expected_projection"] += 1
            elif field == "property_highlights" and sheet.replace("✨", "").strip() == projected.replace("✨", "").strip():
                counters["formatting_only"] += 1
            else:
                kind = classify_populated_conflict(field, sheet, projected, raw)
                counters[kind] += 1
        for field in PROTECTED:
            if str(row.get(field, "") or "") != str(model.get(field, "") or ""):
                counters["protected_column_change"] += 1
    return counters
