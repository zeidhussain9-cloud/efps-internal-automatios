"""Stage-2 inventory processing and safe Stage-1/2 Sheets persistence."""
from __future__ import annotations
from datetime import datetime, timezone
from shared.google_sheets import schema
from shared.google_sheets.client import GoogleSheetsClient
from shared.google_maps import GoogleMapsClient
from . import extract, normalize, validate, listing_id

FIXED = {
    "transaction_type": "Rent",
    "city": "Bengaluru",
    "whatsapp_contact_link": "https://wa.me/919148338801",
    "whatsapp_group_link": "https://chat.whatsapp.com/FxOPO0xAOsD6lNwPcIDdFM",
}
PANEL_FIELDS = tuple(name for name in schema.NAMES if schema.owner_of(name) == schema.PANEL)


def empty_row() -> dict[str, str]:
    return {name: "" for name in schema.NAMES}


def initial_row(listing_id_value: str, raw_text: str = "", source_group: str = "", onboarded_on: str = "") -> dict[str, str]:
    row = empty_row()
    row.update({
        "listing_id": listing_id_value,
        "status": "Raw",
        "intake_status": "Raw",
        "onboarded_on": onboarded_on or datetime.now(timezone.utc).isoformat(),
        "raw_message_text": raw_text,
        "source_group": source_group,
        **FIXED,
    })
    return row


def deterministic(raw_text: str, row: dict | None = None) -> dict:
    """Stage 2 deterministic extraction + normalization/business rules."""
    out = empty_row() if row is None else dict(row)
    out.update(extract.scan(raw_text))
    return normalize.normalize(out, raw_text)


def process_closed_session(raw_text: str, *, row: dict | None = None, maps_client=None, ai_llm=None):
    """Run the complete Stage-2 property-processing sequence."""
    out = deterministic(raw_text, row)
    issues: list[str] = []

    maps = maps_client or GoogleMapsClient()
    maps_url = out.get("google_maps_url", "") or maps.extract_url(raw_text)
    if maps_url:
        resolved = maps.resolve(maps_url=maps_url)
        if resolved.confidence == "VERIFIED":
            out.update({
                "google_maps_url": resolved.canonical_url or maps_url,
                "locality": resolved.locality,
                "pincode": resolved.pincode,
            })
        elif resolved.confidence in ("PARTIAL_MATCH", "NEEDS_RUNTIME_VERIFICATION"):
            issues.append("Google Maps verification is not fully verified")
        elif resolved.confidence not in ("NOT_FOUND", ""):
            issues.append("Google Maps resolution returned an unrecognized verification state")

    out["status"] = "Pending"
    errors = validate.validate(out)
    if errors:
        out["status"] = "Needs Review"
        issues.extend(errors)

    # AI is advisory and wording-only. A deterministic failure is never hidden by AI.
    if out["status"] == "Pending":
        from .ai import apply
        out = apply(out, raw_text, ai_llm)
        if out.get("_ai_conflicts"):
            issues.extend(str(x) for x in out["_ai_conflicts"])
            out["status"] = "Needs Review"
            out.pop("_ai_conflicts", None)

    out["intake_status"] = "Processed"
    return out, issues


def write_new_property(client: GoogleSheetsClient, row: dict):
    """Append one canonical 48-column Stage-1 row."""
    validate_errors = validate.validate_raw(row)
    if validate_errors:
        raise ValueError("Refusing invalid raw inventory row: " + "; ".join(validate_errors))
    schema.assert_writable(schema.PANEL, list(PANEL_FIELDS))
    return client.append_rows(schema.SHEET_ID, schema.WORKSHEET_NAME, [schema.mapping_to_row(row)])


def write_phase1_update(client: GoogleSheetsClient, row_number: int, row: dict):
    """Update panel-owned ranges only; never overwrite AP:AT downstream columns."""
    schema.assert_writable(schema.PANEL, list(PANEL_FIELDS))
    left_names = schema.NAMES[:41]   # A:AO
    right_names = schema.NAMES[46:48]  # AU:AV
    left = [row[name] for name in left_names]
    right = [row[name] for name in right_names]
    client.write_range(
        schema.SHEET_ID,
        schema.WORKSHEET_NAME,
        schema.range_for("listing_id", "city", row_number),
        [left],
    )
    client.write_range(
        schema.SHEET_ID,
        schema.WORKSHEET_NAME,
        schema.range_for("source_group", "inventory_locked", row_number),
        [right],
    )


def next_listing_id(client: GoogleSheetsClient) -> str:
    rows = client.read_range(schema.SHEET_ID, schema.WORKSHEET_NAME, "A2:A")
    return listing_id.generate((r[0] for r in rows if r))
