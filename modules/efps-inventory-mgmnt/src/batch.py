"""Deterministic-first Phase-1 batch runner for existing inventory rows."""
from __future__ import annotations

from shared.google_sheets import schema
from shared.google_sheets.client import GoogleSheetsClient
from shared.google_maps import GoogleMapsClient

from .pipeline import process_closed_session, write_phase1_update

RAW = "Raw"
NEEDS_REVIEW = "Needs Review"

# These columns belong to downstream/lifecycle owners and must survive every
# Inventory Phase-1 processing pass unchanged.
PROTECTED_FIELDS = (
    "listing_state",
    "posted_url",
    "posted_at",
    "error_notes",
    "meta_catalog_id",
    "meta_catalog_status",
    "inventory_locked",
)


def eligible(row: dict) -> bool:
    return (
        bool(str(row.get("listing_id", "")).strip())
        and str(row.get("intake_status", "")).strip() == RAW
        and bool(str(row.get("raw_message_text", "")).strip())
    )


def _assert_protected_fields_unchanged(before: dict, after: dict, row_number: int) -> None:
    changed = [
        field for field in PROTECTED_FIELDS
        if str(before.get(field, "")) != str(after.get(field, ""))
    ]
    if changed:
        raise PermissionError(
            f"row {row_number}: Stage-3 protected fields changed: {', '.join(changed)}"
        )


def run(
    client: GoogleSheetsClient,
    *,
    maps_client=None,
    ai_llm=None,
    limit: int | None = None,
) -> dict:
    """Process all eligible rows and write only Stage-1/2-owned columns."""
    return run_range(
        client,
        start_row=2,
        end_row=None,
        maps_client=maps_client,
        ai_llm=ai_llm,
        limit=limit,
    )


def run_range(
    client: GoogleSheetsClient,
    *,
    start_row: int,
    end_row: int | None,
    maps_client=None,
    ai_llm=None,
    limit: int | None = None,
) -> dict:
    """Process an explicit sheet row range, e.g. rows 2 through 26.

    Rows outside the supplied range are not read or written. Ineligible rows
    inside the range are reported as skipped rather than treated as failures.
    """
    if start_row < 2:
        raise ValueError("start_row must be >= 2")
    if end_row is not None and end_row < start_row:
        raise ValueError("end_row must be >= start_row")
    if limit is not None and limit < 0:
        raise ValueError("limit must be >= 0")

    final_row = end_row if end_row is not None else None
    read_range = (
        f"A{start_row}:AV{final_row}"
        if final_row is not None
        else f"A{start_row}:AV"
    )
    values = client.read_range(schema.SHEET_ID, schema.WORKSHEET_NAME, read_range)

    processed = 0
    needs_review = 0
    skipped = 0
    errors: list[str] = []
    row_results: list[dict] = []
    considered = 0

    for offset, raw_values in enumerate(values):
        row_number = start_row + offset
        if len(raw_values) != schema.GRID_WIDTH:
            errors.append(f"row {row_number}: invalid width {len(raw_values)}")
            row_results.append({"row": row_number, "result": "error"})
            continue

        row = schema.row_to_mapping(raw_values)
        if not eligible(row):
            skipped += 1
            row_results.append({
                "row": row_number,
                "listing_id": str(row.get("listing_id", "")).strip(),
                "result": "skipped",
            })
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
            _assert_protected_fields_unchanged(row, updated, row_number)
            write_phase1_update(client, row_number, updated)

            if str(updated.get("status", "")) == NEEDS_REVIEW:
                needs_review += 1
                result = "needs_review"
            else:
                processed += 1
                result = "processed"

            errors.extend(f"{listing_id}: {issue}" for issue in issues)
            row_results.append({
                "row": row_number,
                "listing_id": listing_id,
                "result": result,
                "issues": issues,
            })
        except Exception as exc:
            errors.append(f"{listing_id}: {type(exc).__name__}: {exc}")
            row_results.append({
                "row": row_number,
                "listing_id": listing_id,
                "result": "error",
                "error": f"{type(exc).__name__}: {exc}",
            })

    return {
        "start_row": start_row,
        "end_row": end_row,
        "considered": considered,
        "processed": processed,
        "needs_review": needs_review,
        "skipped": skipped,
        "errors": errors,
        "rows": row_results,
    }
