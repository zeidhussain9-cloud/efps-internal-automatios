"""Repair deterministic fields that depend on a manually adjudicated property type.

This is a bounded, quota-safe repair for rows that already passed intake and are
already marked Processed. It trusts only the current sheet value of
internal_property_type after explicit human adjudication, preserves explicit
child values, validates the full projected row, protects Stage-3 fields, and
writes all repairs in one batch request.
"""
from __future__ import annotations

import argparse

from shared.google_sheets import schema
from shared.google_sheets.client import GoogleSheetsClient
from src import validate

GATED_AMENITIES = "Club House, Lift, Gym, CCTV, Power Backup, Swimming Pool, Garden, Sports, Kids Area"
SEMI_GATED_AMENITIES = "Security, Lift, CCTV, Power Backup"

PROTECTED_FIELDS = (
    "listing_state", "posted_url", "posted_at", "error_notes",
    "meta_catalog_id", "meta_catalog_status", "inventory_locked",
)


def repair_rows(client: GoogleSheetsClient, *, start_row: int, end_row: int) -> dict:
    if start_row < 2 or end_row < start_row:
        raise ValueError("start_row/end_row must describe a sheet data range starting at row 2 or later")

    values = client.read_range(schema.SHEET_ID, schema.WORKSHEET_NAME, f"A{start_row}:AV{end_row}")
    updates: list[tuple[str, list[list[str]]]] = []
    repaired_rows: list[int] = []
    issues: list[str] = []

    for offset, raw_values in enumerate(values):
        row_number = start_row + offset
        if len(raw_values) != schema.GRID_WIDTH:
            raise ValueError(f"row {row_number}: invalid width {len(raw_values)}")

        row = schema.row_to_mapping(raw_values)
        listing_id = str(row.get("listing_id", "")).strip() or str(row_number)
        if str(row.get("intake_status", "")).strip() != "Processed":
            continue

        property_type = str(row.get("internal_property_type", "")).strip()
        if property_type not in {"Gated Community", "Semi Gated", "Standalone"}:
            issues.append(f"{listing_id}: invalid internal_property_type={property_type!r}")
            continue

        updated = dict(row)
        if property_type in {"Gated Community", "Semi Gated"} and not str(updated.get("covered_parking", "")).strip():
            updated["covered_parking"] = "1"
        if not str(updated.get("open_parking", "")).strip():
            updated["open_parking"] = "-"
        if not str(updated.get("society_amenities", "")).strip():
            updated["society_amenities"] = (
                GATED_AMENITIES if property_type == "Gated Community"
                else SEMI_GATED_AMENITIES if property_type == "Semi Gated"
                else "-"
            )

        errors = validate.validate(updated)
        if errors:
            issues.extend(f"{listing_id}: {error}" for error in errors)
            continue

        protected_changed = [
            field for field in PROTECTED_FIELDS
            if str(row.get(field, "")) != str(updated.get(field, ""))
        ]
        if protected_changed:
            raise PermissionError(
                f"{listing_id}: protected Stage-3 fields changed: {', '.join(protected_changed)}"
            )

        # A previously blocked row becomes Pending only after the repaired
        # canonical row validates cleanly. Otherwise preserve its status.
        if row.get("status") == "Needs Review":
            updated["status"] = "Pending"

        for field in ("status", "covered_parking", "open_parking", "society_amenities"):
            if str(row.get(field, "")) != str(updated.get(field, "")):
                updates.append((schema.range_for(field, field, row_number), [[updated[field]]]))

        if any(str(row.get(field, "")) != str(updated.get(field, "")) for field in ("status", "covered_parking", "open_parking", "society_amenities")):
            repaired_rows.append(row_number)

    if updates:
        client.write_ranges(schema.SHEET_ID, schema.WORKSHEET_NAME, updates)

    return {
        "start_row": start_row,
        "end_row": end_row,
        "repaired_rows": repaired_rows,
        "writes": len(updates),
        "issues": issues,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-row", type=int, required=True)
    parser.add_argument("--end-row", type=int, required=True)
    args = parser.parse_args()

    result = repair_rows(
        GoogleSheetsClient(),
        start_row=args.start_row,
        end_row=args.end_row,
    )
    print(result)


if __name__ == "__main__":
    main()
