"""Read-only Inventory Phase-1 deterministic model audit.

The audit compares deterministic Stage-2 output with persisted Sheet values but
never uses persisted Stage-2 values as extraction input. Differences are
classified so stale/historical Sheet values are not mistaken for parser bugs.
"""
from __future__ import annotations

import argparse
import importlib
import sys
from collections import Counter
from pathlib import Path

from shared.google_sheets import schema
from shared.google_sheets.client import GoogleSheetsClient

MODULE_ROOT = Path(__file__).resolve().parents[1] / "modules" / "efps-inventory-mgmnt"
sys.path.insert(0, str(MODULE_ROOT))
deterministic = importlib.import_module("src.pipeline").deterministic

PROTECTED = {"listing_state", "posted_url", "posted_at", "error_notes", "meta_catalog_id", "meta_catalog_status", "inventory_locked"}
STAGE2 = tuple(name for name in schema.NAMES if schema.stage_of(name) == schema.STAGE_2)
LIFECYCLE = {"status", "intake_status"}
FORMAT_ONLY = {"property_highlights"}
SOURCE_AUDIT_FIELDS = {"BHK", "maintenance", "internal_property_type"}


def _maintenance_base(value: str) -> str:
    return str(value or "").strip().split(" + ", 1)[0].strip()


def _raw_supports_field(field: str, raw: str, projected: str) -> bool:
    """Confirm that a populated model result is grounded in raw text/contract."""
    text = str(raw or "")
    if field == "BHK":
        return bool(importlib.import_module("src.field_resolution").resolve_bhk(text))
    if field == "maintenance":
        value, _ = importlib.import_module("src.field_resolution").resolve_maintenance(text)
        return bool(value)
    if field == "internal_property_type":
        # Explicit source evidence or the declared Standalone fallback is a
        # deterministic contract result; either is independent of Sheet value.
        resolver = importlib.import_module("src.field_resolution").resolve_internal_property_type
        return bool(resolver(text))
    return False


def classify(field: str, sheet: str, model: str, raw: str) -> str:
    s, m = str(sheet or "").strip(), str(model or "").strip()
    if s == m:
        return "same"
    if field in LIFECYCLE:
        return "lifecycle_projection"
    if not s and m:
        return "expected_projection"
    if field in FORMAT_ONLY and s.replace("✨", "").strip() == m.replace("✨", "").strip():
        return "formatting_only"
    if field == "maintenance" and _maintenance_base(s) == _maintenance_base(m) and "+ " in m:
        return "historical_sheet_qualifier_difference"
    if field in SOURCE_AUDIT_FIELDS and _raw_supports_field(field, raw, m):
        return "historical_sheet_value_conflict"
    return "populated_source_conflict"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-row", type=int, default=2)
    parser.add_argument("--end-row", type=int, default=26)
    args = parser.parse_args()
    if args.start_row < 2 or args.end_row < args.start_row:
        raise SystemExit("invalid row range")

    client = GoogleSheetsClient()
    rows = client.read_range(schema.SHEET_ID, schema.WORKSHEET_NAME, f"A{args.start_row}:AV{args.end_row}")
    counters = Counter(); conflicts = []; protected_changes = []
    print("=" * 80); print("EFPS INVENTORY PHASE-1 — READ-ONLY DETERMINISTIC MODEL AUDIT"); print("=" * 80)
    print(f"RANGE       : A{args.start_row}:AV{args.end_row}"); print("MODE        : READ-ONLY"); print("SHEETS WRITE: 0"); print()

    for offset, values in enumerate(rows):
        row_number = args.start_row + offset
        row = schema.row_to_mapping(values); raw = str(row.get("raw_message_text", "") or "")
        if not raw.strip():
            counters["blank_raw"] += 1
            continue
        model = deterministic(raw, row=row)
        for field in STAGE2:
            kind = classify(field, row.get(field, ""), model.get(field, ""), raw); counters[kind] += 1
            if kind in {"historical_sheet_value_conflict", "historical_sheet_qualifier_difference", "populated_source_conflict"}:
                conflicts.append((row_number, row.get("listing_id", ""), field, kind, f"{row.get(field)!r} -> {model.get(field)!r}"))
        for field in PROTECTED:
            if str(row.get(field, "") or "") != str(model.get(field, "") or ""):
                protected_changes.append((row_number, field))

    print("RESULT")
    print(f"ROWS PROCESSED                    : {args.end_row - args.start_row + 1 - counters['blank_raw']}")
    print(f"BLANK RAW                         : {counters['blank_raw']}")
    print(f"EXPECTED PROJECTIONS              : {counters['expected_projection']}")
    print(f"LIFECYCLE PROJECTIONS             : {counters['lifecycle_projection']}")
    print(f"FORMATTING-ONLY DIFFERENCES       : {counters['formatting_only']}")
    print(f"HISTORICAL SHEET VALUE CONFLICTS  : {counters['historical_sheet_value_conflict']}")
    print(f"HISTORICAL QUALIFIER DIFFERENCES  : {counters['historical_sheet_qualifier_difference']}")
    print(f"UNADJUDICATED SOURCE CONFLICTS    : {counters['populated_source_conflict']}")
    print(f"PROTECTED COLUMN CHANGES           : {len(protected_changes)}")
    print()
    if conflicts:
        print("POPULATED DIFFERENCES REQUIRING NO MODEL CHANGE")
        for row_number, listing_id, field, kind, change in conflicts:
            print(f"ROW {row_number} | {listing_id} | {field} | {kind} | {change}")
    else:
        print("POPULATED DIFFERENCES: NONE")
    if protected_changes:
        print("PROTECTED COLUMN VIOLATIONS")
        for row_number, field in protected_changes:
            print(f"ROW {row_number} | {field}")
    else:
        print("PROTECTED COLUMN VIOLATIONS: NONE")
    print(); print("GOOGLE SHEETS WRITES: 0"); print("LIVE EXTRACTION      : NOT PERFORMED"); print("=" * 80)
    return 1 if counters["populated_source_conflict"] or protected_changes else 0


if __name__ == "__main__":
    raise SystemExit(main())
