"""Read-only production-path deterministic projection dump for Housing_Listings.

Reads the canonical A:AT rows, restores the two reserved columns as in-memory
blanks, runs the exact Stage-2 deterministic production pipeline from
raw_message_text, and prints the model projection without writing to Google
Sheets. Existing persisted values are shown only as reference; they are never
used as extraction input or as pass/fail truth.
"""
from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path

from shared.google_sheets import schema
from shared.google_sheets.client import GoogleSheetsClient

MODULE_ROOT = Path(__file__).resolve().parents[1] / "modules" / "efps-inventory-mgmnt"
sys.path.insert(0, str(MODULE_ROOT))
_pipeline = importlib.import_module("src.pipeline")
deterministic = _pipeline.deterministic


def _display(value: object) -> str:
    text = str(value if value is not None else "")
    return text if text else "<blank>"


def _canonical_row(values: list) -> list:
    width = schema.GRID_WIDTH - len(schema.RESERVED_COLUMNS)
    if len(values) != width:
        raise ValueError(f"expected {width} active columns, got {len(values)}")
    return list(values) + [""] * len(schema.RESERVED_COLUMNS)


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
        f"A{args.start_row}:AT{args.end_row}",
    )

    print("=" * 120)
    print("EFPS INVENTORY — READ-ONLY PRODUCTION DETERMINISTIC PROJECTION")
    print("=" * 120)
    print(f"RANGE                  : A{args.start_row}:AT{args.end_row}")
    print("MODE                   : PRODUCTION PATH / READ-ONLY")
    print("SOURCE AUTHORITY       : raw_message_text")
    print("SHEET WRITE            : 0")
    print("RESERVED COLUMNS       : NOT READ / NOT WRITTEN")
    print("PERSISTED VALUES       : DISPLAY ONLY — NEVER EXTRACTION INPUT")
    print()

    processed = 0
    failed = []
    returned_fields = set()
    not_returned_fields = set(schema.NAMES)

    for offset, values in enumerate(rows):
        row_number = args.start_row + offset
        row = schema.row_to_mapping(_canonical_row(values))
        raw = str(row.get("raw_message_text", "") or "")

        print("=" * 120)
        print(f"ROW {row_number} | LISTING {row.get('listing_id', '')}")
        print("=" * 120)
        print("RAW SOURCE")
        print(raw if raw else "<BLANK>")
        print()

        if not raw.strip():
            print("MODEL STATUS            : SKIPPED — blank raw_message_text")
            print()
            continue

        try:
            model = deterministic(raw, row=row)
        except Exception as exc:
            failed.append((row_number, row.get("listing_id", ""), type(exc).__name__, str(exc)))
            print(f"MODEL STATUS            : ERROR — {type(exc).__name__}: {exc}")
            print()
            continue

        processed += 1
        returned_fields.update(model.keys())
        not_returned_fields.difference_update(model.keys())

        print("MODEL OUTPUT")
        for field in schema.NAMES:
            if field in model:
                print(
                    f"  {field:<28} = {_display(model[field])}"
                    f"    [CURRENT SHEET: {_display(row.get(field, ''))}]"
                )
            else:
                print(
                    f"  {field:<28} = NOT RETURNED BY DETERMINISTIC MODEL"
                    f"    [CURRENT SHEET: {_display(row.get(field, ''))}]"
                )
        print()
        print(f"MODEL FIELDS RETURNED     : {len(model)}")
        print(f"CANONICAL FIELDS MISSING  : {len(schema.NAMES) - len(model)}")
        print("SHEET WRITE               : 0")

    print()
    print("=" * 120)
    print("PROJECTION RUN SUMMARY")
    print("=" * 120)
    print(f"ROWS READ                 : {len(rows)}")
    print(f"ROWS WITH MODEL OUTPUT    : {processed}")
    print(f"ROWS WITH MODEL ERROR     : {len(failed)}")
    print(f"UNIQUE MODEL FIELDS SEEN  : {len(returned_fields)}")
    print(f"CANONICAL FIELDS          : {len(schema.NAMES)}")
    print(f"SHEET WRITES              : 0")
    print("LIVE EXTRACTION           : NOT PERFORMED")

    if failed:
        print()
        print("MODEL ERRORS")
        for row_number, listing_id, error_type, message in failed:
            print(f"  ROW {row_number} | {listing_id} | {error_type}: {message}")

    print()
    print("FIELDS NOT RETURNED BY MODEL IN ANY PROCESSED ROW")
    missing_any = sorted(not_returned_fields)
    if missing_any:
        for field in missing_any:
            print(f"  - {field}")
    else:
        print("  NONE")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
