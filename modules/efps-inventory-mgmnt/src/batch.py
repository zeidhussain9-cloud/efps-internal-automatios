"""Deterministic-first Phase-1 batch runner for existing inventory rows."""
from __future__ import annotations

from shared.google_sheets import schema
from shared.google_sheets.client import GoogleSheetsClient
from shared.google_maps import GoogleMapsClient

from .pipeline import process_closed_session, write_phase1_update

RAW = "Raw"
NEEDS_REVIEW = "Needs Review"


def eligible(row: dict) -> bool:
    return (
        bool(str(row.get("listing_id", "")).strip())
        and str(row.get("intake_status", "")).strip() == RAW
        and bool(str(row.get("raw_message_text", "")).strip())
    )


def run(client: GoogleSheetsClient, *, maps_client=None, ai_llm=None, limit: int | None = None) -> dict:
    """Process eligible rows and write only Stage-1/2-owned columns."""
    values = client.read_range(schema.SHEET_ID, schema.WORKSHEET_NAME, "A2:AV")
    processed = 0
    needs_review = 0
    errors: list[str] = []
    considered = 0

    for row_number, raw_values in enumerate(values, start=2):
        if len(raw_values) != schema.GRID_WIDTH:
            errors.append(f"row {row_number}: invalid width {len(raw_values)}")
            continue
        row = schema.row_to_mapping(raw_values)
        if not eligible(row):
            continue
        if limit is not None and considered >= limit:
            break
        considered += 1
        listing_id = str(row.get("listing_id", row_number)).strip()
        try:
            updated, issues = process_closed_session(
                str(row.get("raw_message_text", "")),
                row=row,
                maps_client=maps_client or GoogleMapsClient(),
                ai_llm=ai_llm,
            )
            write_phase1_update(client, row_number, updated)
            if str(updated.get("status", "")) == NEEDS_REVIEW:
                needs_review += 1
            else:
                processed += 1
            errors.extend(f"{listing_id}: {issue}" for issue in issues)
        except Exception as exc:
            errors.append(f"{listing_id}: {type(exc).__name__}: {exc}")

    return {
        "considered": considered,
        "processed": processed,
        "needs_review": needs_review,
        "errors": errors,
    }
