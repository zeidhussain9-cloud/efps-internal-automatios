"""Phase-1 batch runner for existing and newly ingested inventory rows.

The batch runner is intentionally deterministic-first. It reads canonical rows,
processes eligible Raw rows through the same Stage-2 pipeline used by webhook
closure, and writes only Stage-1/2-owned fields.
"""
from __future__ import annotations

from typing import Callable

from shared.google_sheets import schema
from shared.google_sheets.client import GoogleSheetsClient
from shared.google_maps import GoogleMapsClient

from .pipeline import process_closed_session, write_phase1_update

RAW = "Raw"
PROCESSED = "Processed"
NEEDS_REVIEW = "Needs Review"


def eligible(row: dict) -> bool:
    return (
        str(row.get("listing_id", "")).strip() != ""
        and str(row.get("intake_status", "")).strip() == RAW
        and str(row.get("raw_message_text", "")).strip() != ""
    )


def run(client: GoogleSheetsClient, *, maps_client=None, ai_llm=None, limit: int | None = None) -> dict:
    """Process waiting rows and return an operational summary.

    Existing downstream/lifecycle values are preserved because
    ``write_phase1_update`` writes only the Stage-1/2 owned ranges.
    """
    rows = client.read_range(schema.SHEET_ID, schema.WORKSHEET_NAME, "A2:AV")
    processed = 0
    review = 0
    errors: list[str] = []

    for row_number, values in enumerate(rows, start=2):
        if len(values) != schema.GRID_WIDTH:
            errors.append(f"row {row_number}: invalid width {len(values)}")
            continue
        row = schema.row_to_mapping(values)
        if not eligible(row):
            continue
        if limit is not None and processed + review >= limit:
            break
        try:
            updated, issues = process_closed_session(
                str(row.get("raw_message_text", "")),
                row=row,
                maps_client=maps_client or GoogleMapsClient(),
                ai_llm=ai_llm,
            )
            write_phase1_update(client, row_number, updated)
            if str(updated.get("status", "")) == NEEDS_REVIEW:
                review += 1
            else:
                processed += 1
            errors.extend(f"{row.get('listing_id', row_number)}: {item}" for item in issues)
        except Exception as exc:  # batch must continue and report row-level failure
            errors.append(f"{row.get('listing_id', row_number)}: {type(exc).__name__}: {exc}")

    return {
        "processed": processed,
        "needs_review": review,
        "errors": errors,
    }
