"""Inventory processing core: deterministic Stage-1/2 parsing and projection. Notion is the canonical store; Google Sheets persistence is retired."""
from __future__ import annotations

from datetime import datetime, timezone

from shared.google_maps import GoogleMapsClient
from shared.google_sheets import schema
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
    maps_unverified = False
    if maps_url:
        try:
            resolved = maps.resolve(maps_url=maps_url)
        except Exception:
            # Maps is optional enrichment. Network, HTTP, billing, quota, and
            # credential failures must not discard a valid source-submitted URL.
            resolved = None
            issues.append("Google Maps API unavailable (credentials, billing, quota, authorization, or network); original source URL retained and labelled not verified.")
        if resolved is not None and resolved.confidence == "VERIFIED":
            out["google_maps_url"] = maps_url
            verified_locality = str(resolved.locality or "").strip()
            source_locality = str(out.get("locality", "") or "").strip()
            if verified_locality:
                if source_locality and source_locality.casefold() != verified_locality.casefold():
                    issues.append(f"Google Maps verified locality overrides source locality: {source_locality} -> {verified_locality}")
                out["locality"] = verified_locality
            else:
                issues.append("Google Maps verification failed or is incomplete: verified locality missing")
                maps_unverified = True
            if resolved.pincode:
                out["pincode"] = resolved.pincode
            place_name = str(getattr(resolved, "place_name", "") or "").strip()
            if place_name:
                source_society = str(out.get("society_name", "") or "").strip()
                if source_society and source_society.casefold() != place_name.casefold():
                    issues.append(f"Google Maps verified place name overrides source society: {source_society} -> {place_name}")
                out["society_name"] = place_name
                issues.append(f"Google Maps verified place name: {place_name}")
        elif resolved is not None:
            if resolved.confidence in {"API_UNAVAILABLE", "NEEDS_RUNTIME_VERIFICATION"}:
                    issues.append("Google Maps API unavailable (credentials, billing, quota, or authorization); original source URL retained and labelled not verified.")
            else:
                issues.append(f"Google Maps verification failed or is incomplete: {resolved.confidence}")
                maps_unverified = True
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
        out["status"] = "Needs Review" if maps_unverified else "Pending"
    if out["status"] == "Pending":
        out = ai.apply(out, raw_text, ai_llm)
        if out.get("_ai_conflicts"):
            issues.extend(str(x) for x in out["_ai_conflicts"])
            out["status"] = "Needs Review"
            out.pop("_ai_conflicts", None)
    out["intake_status"] = "Processed"
    return out, issues

