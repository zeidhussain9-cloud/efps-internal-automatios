from __future__ import annotations

from . import intake, pipeline
from shared.google_sheets import schema


def test_initial_row_is_canonical_and_stage_one_safe():
    row = pipeline.initial_row("EF-2609-0001", source_group="919902024973", onboarded_on="2026-09-15T00:00:00+00:00")
    assert list(row) == list(schema.NAMES)
    assert row["listing_id"] == "EF-2609-0001"
    assert row["status"] == "Raw"
    assert row["intake_status"] == "Raw"
    assert row["onboarded_on"] == "2026-09-15T00:00:00+00:00"
    assert row["transaction_type"] == "Rent"
    assert row["city"] == "Bengaluru"
    assert row["posted_url"] == ""
    assert row["meta_catalog_id"] == ""


def test_deterministic_processing_preserves_verified_business_rules():
    raw = """Fully Furnished 2 BHK
Floor: 3/10
Built-up Area: 1200 sqft
Rent: 50000
Maintenance: Water Charges
Deposit: 2 months
Preferred Tenant: Family
Utility area
Gated Community"""
    row = pipeline.deterministic(raw, pipeline.initial_row("EF-2609-0002"))
    assert row["BHK"] == "2 BHK"
    assert row["property_subtype"] == "Apartment"
    assert row["floor_number"] == "3"
    assert row["total_floors"] == "10"
    assert row["carpet_area"] == "1080"
    assert row["monthly_rent"] == "50000"
    assert row["security_deposit"] == "100000"
    assert row["maintenance"] == "Water Charges"
    assert row["maintenance_included"] == "No"
    assert row["preferred_tenant_type"] == "Family"
    assert row["bachelor_preference"] == "Not Allowed"
    assert row["internal_property_type"] == "Gated Community"
    assert "Swimming Pool" in row["society_amenities"]
    assert "Utility area" in row["property_highlights"]
    assert "Wardrobe" in row["flat_furnishings"]
    assert "Fridge" in row["flat_furnishings"]


def test_family_bachelor_explicit_value_is_not_overwritten():
    raw = "2 BHK\nRent: 40000\nPreferred Tenant: Family\nBachelor: Open for both"
    row = pipeline.deterministic(raw, pipeline.initial_row("EF-2609-0003"))
    assert row["preferred_tenant_type"] == "Family"
    assert row["bachelor_preference"] == "Open for both"


def test_new_marker_opens_then_closes_same_sender_session():
    store = intake.InMemorySessionStore()
    sender = "917975102130"
    assert intake.ingest({"sender": sender, "body": "NEW", "chat_id": sender}, store)[0] == "opened"
    state, session = intake.ingest({"sender": sender, "body": "2 BHK Rent 45000", "message_id": "m1", "chat_id": sender}, store)
    assert state == "collecting"
    assert "2 BHK Rent 45000" in session.raw_text
    state, closed = intake.ingest({"sender": sender, "body": "NEW", "chat_id": sender}, store)
    assert state == "closed"
    assert closed.raw_text.endswith("2 BHK Rent 45000")
    assert store.get(sender) is None


def test_duplicate_message_id_is_not_appended_twice():
    store = intake.InMemorySessionStore()
    sender = "919902024973"
    intake.ingest({"sender": sender, "body": "NEW", "chat_id": sender}, store)
    msg = {"sender": sender, "body": "Rent 50000", "message_id": "same", "chat_id": sender}
    intake.ingest(msg, store)
    intake.ingest(msg, store)
    session = store.get(sender)
    assert session is not None
    assert session.raw_text.count("Rent 50000") == 1
