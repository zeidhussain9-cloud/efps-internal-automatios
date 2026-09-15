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


def classify(field: str, sheet: str, model: str) -> str:
    s, m = str(sheet or "").strip(), str(model or "").strip()
    if s == m: return "same"
    if field in LIFECYCLE: return "lifecycle_projection"
    if not s and m: return "expected_projection"
    if field in FORMAT_ONLY and s.replace("✨", "").strip() == m.replace("✨", "").strip(): return "formatting_only"
    return "populated_source_conflict"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-row", type=int, default=2)
    parser.add_argument("--end-row", type=int, default=26)
    args = parser.parse_args()
    if args.start_row < 2 or args.end_row < args.start_row: raise SystemExit("invalid row range")

    client = GoogleSheetsClient()
    rows = client.read_range(schema.SHEET_ID, schema.WORKSHEET_NAME, f"A{args.start_row}:AV{args.end_row}")
    counters = Counter(); conflicts = []; protected_changes = []
    print("=" * 80); print("EFPS INVENTORY PHASE-1 — READ-ONLY DETERMINISTIC MODEL TEST"); print("=" * 80)
    print(f"RANGE       : A{args.start_row}:AV{args.end_row}"); print("MODE        : READ-ONLY"); print("SHEETS WRITE: 0"); print()

    for offset, values in enumerate(rows):
        row_number = args.start_row + offset
        row = schema.row_to_mapping(values); raw = str(row.get("raw_message_text", "") or "")
        if not raw.strip(): counters["blank_raw"] += 1; continue
        model = deterministic(raw, row=row)
        for field in STAGE2:
            kind = classify(field, row.get(field, ""), model.get(field, "")); counters[kind] += 1
            if kind == "populated_source_conflict": conflicts.append((row_number, row.get("listing_id", ""), field, f"{row.get(field)!r} -> {model.get(field)!r}"))
        for field in PROTECTED:
            if str(row.get(field, "")) != str(model.get(field, "")): protected_changes.append((row_number, field))

    print("RESULT")
    print(f"ROWS PROCESSED             : {args.end_row - args.start_row + 1 - counters['blank_raw']}")
    print(f"BLANK RAW                  : {counters['blank_raw']}")
    print(f"EXPECTED PROJECTIONS       : {counters['expected_projection']}")
    print(f"LIFECYCLE PROJECTIONS      : {counters['lifecycle_projection']}")
    print(f"FORMATTING-ONLY DIFFERENCES: {counters['formatting_only']}")
    print(f"POPULATED SOURCE CONFLICTS : {counters['populated_source_conflict']}")
    print(f"PROTECTED COLUMN CHANGES   : {len(protected_changes)}")
    print()
    if conflicts:
        print("POPULATED SOURCE CONFLICTS")
        for row_number, listing_id, field, change in conflicts: print(f"ROW {row_number} | {listing_id} | {field} | {change}")
    else: print("POPULATED SOURCE CONFLICTS: NONE")
    if protected_changes:
        print("PROTECTED COLUMN VIOLATIONS")
        for row_number, field in protected_changes: print(f"ROW {row_number} | {field}")
    else: print("PROTECTED COLUMN VIOLATIONS: NONE")
    print(); print("GOOGLE SHEETS WRITES: 0"); print("LIVE EXTRACTION      : NOT PERFORMED"); print("=" * 80)
    return 1 if conflicts or protected_changes else 0


if __name__ == "__main__": raise SystemExit(main())
