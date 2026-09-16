"""Quota-safe, resumable Phase-1 runner for existing inventory rows."""
from __future__ import annotations

from shared.google_sheets import schema
from shared.google_sheets.client import GoogleSheetsClient

try:
    from .phase1 import Phase1Result
    from .pipeline import phase1_ranges_for_row, process_phase1
except ImportError:
    from phase1 import Phase1Result
    from pipeline import phase1_ranges_for_row, process_phase1

RAW = "Raw"
NEEDS_REVIEW = "Needs Review"
PROTECTED_FIELDS = (
    "listing_state", "posted_url", "posted_at", "error_notes",
    "meta_catalog_id", "meta_catalog_status",
)


def eligible(row: dict) -> bool:
    return (
        bool(str(row.get("listing_id", "")).strip())
        and str(row.get("intake_status", "")).strip() == RAW
        and bool(str(row.get("raw_message_text", "")).strip())
    )


def _assert_protected_fields_unchanged(before: dict, after: dict, row_number: int) -> None:
    changed = [field for field in PROTECTED_FIELDS if str(before.get(field, "")) != str(after.get(field, ""))]
    if changed:
        raise PermissionError(f"row {row_number}: Stage-3 protected fields changed: {', '.join(changed)}")


def _field_report(result: Phase1Result) -> dict:
    report = result.report
    return {
        "populated": report.get("populated_fields", []),
        "blank": report.get("blank_fields", []),
        "unresolved": report.get("unresolved_fields", []),
        "review_flags": report.get("review_flags", []),
        "trace": report.get("trace", {}),
    }


def _canonical_rows(values: list[list]) -> list[list]:
    """Map the operational A:AT read into the intact 48-field schema."""
    width = schema.GRID_WIDTH - len(schema.RESERVED_COLUMNS)
    normalized = []
    for row in values:
        if len(row) == width:
            normalized.append(list(row) + [""] * len(schema.RESERVED_COLUMNS))
        else:
            normalized.append(row)
    return normalized


def run(
    client: GoogleSheetsClient,
    *,
    start_row: int = 2,
    end_row: int | None = None,
    limit: int | None = None,
) -> dict:
    """Process a bounded sheet range through the canonical Phase-1 runner.

    The function performs one read and one batch write for the whole run. A
    failed write leaves eligible rows Raw/Raw so the same command can be safely
    rerun; already Processed rows are skipped. No Maps network call or AI call
    is made by this batch path.
    """
    if start_row < 2:
        raise ValueError("start_row must be >= 2")
    if end_row is not None and end_row < start_row:
        raise ValueError("end_row must be >= start_row")
    if limit is not None and limit < 0:
        raise ValueError("limit must be >= 0")

    final_row = end_row if end_row is not None else None
    read_range = f"A{start_row}:AT{final_row}" if final_row is not None else f"A{start_row}:AT"
    values = _canonical_rows(client.read_range(schema.SHEET_ID, schema.WORKSHEET_NAME, read_range))

    considered = processed = needs_review = skipped = 0
    errors: list[str] = []
    row_results: list[dict] = []
    writes: list[tuple[str, list[list[str]]]] = []
    pending_rows: list[tuple[int, dict, dict, list[str]]] = []

    for offset, raw_values in enumerate(values):
        row_number = start_row + offset
        if len(raw_values) != schema.GRID_WIDTH:
            errors.append(f"row {row_number}: invalid width {len(raw_values)}")
            row_results.append({"row": row_number, "result": "error", "error": "invalid width"})
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
            result = process_phase1(str(row.get("raw_message_text", "")), row=row)
            updated = result.row
            issues = list(result.issues)
            _assert_protected_fields_unchanged(row, updated, row_number)
            writes.extend(phase1_ranges_for_row(row_number, updated))
            pending_rows.append((row_number, updated, _field_report(result), issues))
        except Exception as exc:
            errors.append(f"{listing_id}: {type(exc).__name__}: {exc}")
            row_results.append({
                "row": row_number,
                "listing_id": listing_id,
                "result": "error",
                "error": f"{type(exc).__name__}: {exc}",
            })

    write_error = None
    if writes:
        try:
            client.write_ranges(schema.SHEET_ID, schema.WORKSHEET_NAME, writes)
        except Exception as exc:
            write_error = f"{type(exc).__name__}: {exc}"
            errors.append(f"batch write failed; no Phase-1 rows were confirmed: {write_error}")

    if write_error is None:
        for row_number, updated, field_report, issues in pending_rows:
            listing_id = str(updated.get("listing_id", row_number)).strip()
            if str(updated.get("status", "")) == NEEDS_REVIEW:
                needs_review += 1
                result_name = "needs_review"
            else:
                processed += 1
                result_name = "processed"
            errors.extend(f"{listing_id}: {issue}" for issue in issues)
            row_results.append({
                "row": row_number,
                "listing_id": listing_id,
                "result": result_name,
                "issues": issues,
                "fields": field_report,
            })
    else:
        for row_number, updated, field_report, issues in pending_rows:
            row_results.append({
                "row": row_number,
                "listing_id": str(updated.get("listing_id", row_number)).strip(),
                "result": "write_failed",
                "issues": issues,
                "fields": field_report,
            })

    return {
        "start_row": start_row,
        "end_row": end_row,
        "considered": considered,
        "processed": processed,
        "needs_review": needs_review,
        "skipped": skipped,
        "write_failed": bool(write_error),
        "errors": errors,
        "rows": row_results,
    }
