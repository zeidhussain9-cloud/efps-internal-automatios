"""Inventory processing and safe Stage-1/2 Sheets persistence."""
from __future__ import annotations

from datetime import datetime, timezone

from shared.google_maps import GoogleMapsClient
from shared.google_sheets import schema
from shared.google_sheets.client import GoogleSheetsClient

try:
    from . import ai, listing_id, validate
    from .phase1 import Phase1Result, project as deterministic_project, run_phase1
except ImportError:
    import ai, listing_id, validate
    from phase1 import Phase1Result, project as deterministic_project, run_phase1

FIXED = {
    "transaction_type": "Rent",
    "city": "Bengaluru",
    "whatsapp_contact_link": "https://wa.me/919148338801",
    "whatsapp_group_link": "https://chat.whatsapp.com/FxOPO0xAOsD6lNwPcIDdFM",
}
PANEL_FIELDS = tuple(name for name in schema.NAMES if schema.owner_of(name) == schema.PANEL)
STAGE_3_PROTECTED = {
    "listing_state", "posted_url", "posted_at", "error_notes",
    "meta_catalog_id", "meta_catalog_status",
}
STAGE_1_2_WRITABLE = tuple(name for name in PANEL_FIELDS if name not in STAGE_3_PROTECTED)


def empty_row() -> dict[str, str]:
    return {name: "" for name in schema.NAMES}


def initial_row(listing_id_value: str, raw_text: str = "", onboarded_on: str = "") -> dict[str, str]:
    row = empty_row()
    row.update({
        "listing_id": listing_id_value,
        "status": "Raw",
        "intake_status": "Raw",
        "listing_state": "Available",
        "onboarded_on": onboarded_on or datetime.now(timezone.utc).isoformat(),
        "raw_message_text": raw_text,
        **FIXED,
    })
    return row


def deterministic(raw_text: str, row: dict | None = None) -> dict[str, str]:
    """Canonical deterministic projection with no AI or Maps network access."""
    return deterministic_project(raw_text, row=row)


def process_phase1(raw_text: str, *, row: dict | None = None) -> Phase1Result:
    """Run the production Phase-1 boundary and return its execution report."""
    return run_phase1(raw_text, row=row)


def process_closed_session(raw_text: str, *, row: dict | None = None, maps_client=None, ai_llm=None):
    """Run Phase-1 first, then optional runtime Maps verification and AI."""
    result = run_phase1(raw_text, row=row)
    out = result.row
    issues = list(result.issues)
    maps = maps_client or GoogleMapsClient()
    maps_url = out.get("google_maps_url", "")
    if maps_url:
        resolved = maps.resolve(maps_url=maps_url)
        if resolved.confidence == "VERIFIED":
            out.update({
                "google_maps_url": resolved.canonical_url or maps_url,
                "locality": resolved.locality or out.get("locality", ""),
                "pincode": resolved.pincode or out.get("pincode", ""),
            })
            place_name = str(getattr(resolved, "place_name", "") or "").strip()
            if place_name:
                source_society = str(out.get("society_name", "") or "").strip()
                if not source_society or source_society == out.get("locality", ""):
                    out["society_name"] = place_name
        else:
            issues.append(f"Google Maps verification failed or is incomplete: {resolved.confidence}")
    try:
        from .phase1 import apply_location_contract
    except ImportError:
        from phase1 import apply_location_contract
    apply_location_contract(out)
    errors = validate.validate(out)
    if errors:
        out["status"] = "Needs Review"
        issues.extend(errors)
    else:
        out["status"] = "Pending"
    if out["status"] == "Pending":
        out = ai.apply(out, raw_text, ai_llm)
        if out.get("_ai_conflicts"):
            issues.extend(str(x) for x in out["_ai_conflicts"])
            out["status"] = "Needs Review"
            out.pop("_ai_conflicts", None)
    out["intake_status"] = "Processed"
    return out, issues


def write_new_property(client: GoogleSheetsClient, row: dict):
    validate_errors = validate.validate_raw(row)
    if validate_errors:
        raise ValueError("Refusing invalid raw inventory row: " + "; ".join(validate_errors))
    schema.assert_writable(schema.PANEL, list(STAGE_1_2_WRITABLE))
    return client.insert_rows(schema.SHEET_ID, schema.WORKSHEET_NAME, [schema.mapping_to_row(row)])


def _phase1_ranges(row_number: int, row: dict) -> list[tuple[str, list[list[str]]]]:
    return [
        (schema.range_for("listing_id", "internal_property_type", row_number), [[row[name] for name in schema.NAMES[0:4]]]),
        (schema.range_for("onboarded_on", "city", row_number), [[row[name] for name in schema.NAMES[5:41]]]),
    ]


def write_phase1_update(client: GoogleSheetsClient, row_number: int, row: dict):
    if row_number < 2:
        raise ValueError("inventory row_number must be >= 2")
    if set(row) != set(schema.NAMES):
        raise ValueError("inventory row does not match canonical 48-field schema")
    schema.assert_writable(schema.PANEL, list(STAGE_1_2_WRITABLE))
    return client.write_ranges(schema.SHEET_ID, schema.WORKSHEET_NAME, _phase1_ranges(row_number, row))


def phase1_ranges_for_row(row_number: int, row: dict) -> list[tuple[str, list[list[str]]]]:
    return _phase1_ranges(row_number, row)


def next_listing_id(client: GoogleSheetsClient) -> str:
    rows = client.read_range(schema.SHEET_ID, schema.WORKSHEET_NAME, "A2:A")
    return listing_id.generate((r[0] for r in rows if r))
