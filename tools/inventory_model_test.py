"""Full read-only Phase-1 deterministic field audit for Housing_Listings.

This is intentionally a model-vs-persisted audit, not a write path. It reads the
canonical A:AV row range, runs the deterministic Stage-2 model from raw_message_text,
prints every field for every tested row, then emits field-level gate statistics.

Persisted Stage-2 values are never used as extraction input.
"""
from __future__ import annotations

import argparse
import importlib
import sys
from collections import Counter, defaultdict
from pathlib import Path

from shared.google_sheets import schema
from shared.google_sheets.client import GoogleSheetsClient

MODULE_ROOT = Path(__file__).resolve().parents[1] / "modules" / "efps-inventory-mgmnt"
sys.path.insert(0, str(MODULE_ROOT))
_resolution = importlib.import_module("src.field_resolution")
_pipeline = importlib.import_module("src.pipeline")
deterministic = _pipeline.deterministic

PROTECTED = {
    "listing_state", "posted_url", "posted_at", "error_notes",
    "meta_catalog_id", "meta_catalog_status", "inventory_locked",
}
MODEL_FIELDS = tuple(
    name for name in schema.NAMES
    if schema.stage_of(name) == schema.STAGE_2
)
NON_MODEL_FIELDS = tuple(name for name in schema.NAMES if name not in MODEL_FIELDS)
SOURCE_AUDIT_FIELDS = {"BHK", "maintenance", "internal_property_type"}


def _maintenance_base(value: str) -> str:
    return str(value or "").strip().split(" + ", 1)[0].strip()


def _raw_supports_field(field: str, raw: str, projected: str) -> bool:
    if not str(projected or "").strip():
        return False
    if field == "BHK":
        return bool(_resolution.resolve_bhk(raw))
    if field == "maintenance":
        value, _ = _resolution.resolve_maintenance(raw)
        return bool(value)
    if field == "internal_property_type":
        return bool(_resolution.resolve_internal_property_type(raw))
    return False


def _verdict(field: str, persisted: str, model: str, raw: str) -> str:
    s, m = str(persisted or "").strip(), str(model or "").strip()
    if s == m:
        return "PASS_SAME"
    if not s and m:
        return "MODEL_POPULATES_BLANK"
    if field == "maintenance" and _maintenance_base(s) == _maintenance_base(m) and "+ " in m:
        return "PASS_QUALIFIER_NORMALIZED"
    if field in SOURCE_AUDIT_FIELDS and _raw_supports_field(field, raw, m):
        return "HISTORICAL_SHEET_CONFLICT"
    if field in MODEL_FIELDS and m:
        return "HISTORICAL_SHEET_CONFLICT"
    return "UNADJUDICATED_SOURCE_CONFLICT"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-row", type=int, default=2)
    parser.add_argument("--end-row", type=int, default=26)
    args = parser.parse_args()
    if args.start_row < 2 or args.end_row < args.start_row:
        raise SystemExit("invalid row range")

    client = GoogleSheetsClient()
    rows = client.read_range(
        schema.SHEET_ID,
        schema.WORKSHEET_NAME,
        f"A{args.start_row}:AV{args.end_row}",
    )

    field_stats = {field: Counter() for field in schema.NAMES}
    protected_changes = []
    blank_raw_rows = []

    print("=" * 120)
    print("EFPS INVENTORY PHASE-1 — FULL READ-ONLY DETERMINISTIC FIELD AUDIT")
    print("=" * 120)
    print(f"RANGE                  : A{args.start_row}:AV{args.end_row}")
    print("MODE                   : READ-ONLY")
    print("SHEETS WRITE           : 0")
    print(f"MODEL FIELDS           : {len(MODEL_FIELDS)} Stage-2 fields")
    print(f"NON-MODEL FIELDS       : {len(NON_MODEL_FIELDS)} Stage-1/3 owned fields")
    print("SOURCE AUTHORITY       : raw_message_text")
    print()

    processed = 0
    for offset, values in enumerate(rows):
        row_number = args.start_row + offset
        row = schema.row_to_mapping(values)
        raw = str(row.get("raw_message_text", "") or "")
        if not raw.strip():
            blank_raw_rows.append(row_number)
            continue

        processed += 1
        model = deterministic(raw, row=row)

        print("-" * 120)
        print(f"ROW {row_number} | LISTING {row.get('listing_id', '')}")
        print("-" * 120)

        for field in schema.NAMES:
            persisted = str(row.get(field, "") or "")
            projected = str(model.get(field, "") or "")
            owner = schema.owner_of(field)
            stage = schema.stage_of(field)

            if field in MODEL_FIELDS:
                verdict = _verdict(field, persisted, projected, raw)
                field_stats[field][verdict] += 1
            else:
                verdict = "PROTECTED_NOT_MODEL_OWNED" if field in PROTECTED else "NOT_MODEL_OWNED"

            print(
                f"ROW {row_number:>2} | {field:<28} | "
                f"persisted={persisted!r} | model={projected!r} | "
                f"verdict={verdict} | owner={owner} | stage={stage}"
            )

            if field in PROTECTED and persisted != projected:
                protected_changes.append((row_number, field, persisted, projected))

    print()
    print("=" * 120)
    print("FIELD-BY-FIELD GATE SUMMARY")
    print("=" * 120)
    print(
        f"{'FIELD':<30} {'MODEL':<6} {'ROWS':>5} {'SAME':>6} "
        f"{'POPULATE':>8} {'QUALIFIER':>10} {'HISTORICAL':>11} {'UNADJ':>7} {'GATE':<10}"
    )

    gate_failures = []
    total_model_projections = 0
    total_unadjudicated = 0

    for field in MODEL_FIELDS:
        stats = field_stats[field]
        rows_tested = sum(stats.values())
        same = stats["PASS_SAME"]
        populate = stats["MODEL_POPULATES_BLANK"]
        qualifier = stats["PASS_QUALIFIER_NORMALIZED"]
        historical = stats["HISTORICAL_SHEET_CONFLICT"]
        unadjudicated = stats["UNADJUDICATED_SOURCE_CONFLICT"]
        total_model_projections += rows_tested
        total_unadjudicated += unadjudicated
        gate = "PASS" if unadjudicated == 0 else "BLOCKED"
        if gate != "PASS":
            gate_failures.append(field)

        print(
            f"{field:<30} {'YES':<6} {rows_tested:>5} {same:>6} "
            f"{populate:>8} {qualifier:>10} {historical:>11} "
            f"{unadjudicated:>7} {gate:<10}"
        )

    print()
    print("=" * 120)
    print("CONTRACT / OWNERSHIP SUMMARY")
    print("=" * 120)
    print(f"TOTAL CANONICAL FIELDS       : {len(schema.NAMES)}")
    print(f"MODEL-OWNED STAGE-2 FIELDS   : {len(MODEL_FIELDS)}")
    print(f"STAGE-1/3 NON-MODEL FIELDS   : {len(NON_MODEL_FIELDS)}")
    print(f"ROWS PROCESSED               : {processed}")
    print(f"BLANK RAW ROWS               : {len(blank_raw_rows)}")
    print(f"MODEL FIELD PROJECTIONS      : {total_model_projections}")
    print(f"UNADJUDICATED CONFLICTS      : {total_unadjudicated}")
    print(f"PROTECTED COLUMN CHANGES     : {len(protected_changes)}")
    print()

    if gate_failures:
        print("BLOCKED MODEL FIELDS:")
        for field in gate_failures:
            print(f"  - {field}")
    else:
        print("BLOCKED MODEL FIELDS: NONE")

    if protected_changes:
        print("PROTECTED COLUMN VIOLATIONS:")
        for row_number, field, persisted, projected in protected_changes:
            print(f"  ROW {row_number} | {field} | {persisted!r} -> {projected!r}")
    else:
        print("PROTECTED COLUMN VIOLATIONS: NONE")

    if blank_raw_rows:
        print(f"BLANK RAW ROWS: {', '.join(map(str, blank_raw_rows))}")

    print()
    print("=" * 120)
    print("FINAL GATE")
    print("=" * 120)
    if not gate_failures and not protected_changes and not blank_raw_rows:
        print("PHASE-1 MODEL FIELD GATE: PASS")
        print("GOOGLE SHEETS WRITES: 0")
        print("LIVE EXTRACTION: NOT PERFORMED")
        return 0

    print("PHASE-1 MODEL FIELD GATE: BLOCKED")
    print("GOOGLE SHEETS WRITES: 0")
    print("LIVE EXTRACTION: NOT PERFORMED")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
