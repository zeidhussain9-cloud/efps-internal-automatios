from __future__ import annotations

import pytest

from . import schema

EXPECTED = (
    "listing_id", "status", "intake_status", "internal_property_type", "listing_state", "onboarded_on",
    "raw_message_text", "locality", "society_name", "landmark", "pincode", "google_maps_url",
    "furnish_type", "BHK", "bathrooms", "balconies", "floor_number", "total_floors", "built_up_area",
    "carpet_area", "monthly_rent", "maintenance", "maintenance_included", "security_deposit",
    "preferred_tenant_type", "bachelor_preference", "pet_friendly", "servant_room", "covered_parking",
    "open_parking", "society_amenities", "flat_furnishings", "property_highlights", "catalog_title",
    "cloudinary_image_urls", "age_of_property_years", "whatsapp_contact_link", "whatsapp_group_link",
    "transaction_type", "property_subtype", "city", "posted_url", "posted_at", "error_notes",
    "meta_catalog_id", "meta_catalog_status", "source_group", "inventory_locked",
)


def test_contract_is_exactly_latest_48_columns() -> None:
    assert schema.NAMES == EXPECTED
    assert schema.GRID_WIDTH == 48
    assert schema.LAST_COLUMN == "AV"
    for name, column in {
        "listing_id": "A", "raw_message_text": "G", "google_maps_url": "L",
        "transaction_type": "AM", "property_subtype": "AN", "city": "AO",
        "posted_url": "AP", "posted_at": "AQ", "error_notes": "AR",
        "meta_catalog_id": "AS", "meta_catalog_status": "AT", "source_group": "AU",
        "inventory_locked": "AV",
    }.items():
        assert schema.letter(name) == column


def test_row_mapping_round_trip() -> None:
    row = [f"v{i}" for i in range(schema.GRID_WIDTH)]
    assert schema.mapping_to_row(schema.row_to_mapping(row)) == row


def test_row_width_is_enforced() -> None:
    with pytest.raises(ValueError):
        schema.validate_row(["only-one"])


def test_downstream_ownership_is_exact() -> None:
    assert schema.writable_by(schema.HOUSING_AGENT) == ("posted_url", "posted_at", "error_notes")
    assert schema.writable_by(schema.META_CATALOG) == ("meta_catalog_id", "meta_catalog_status")
    assert "source_group" in schema.writable_by(schema.PANEL)
    assert "inventory_locked" in schema.writable_by(schema.PANEL)


def test_unknown_and_foreign_writes_are_rejected() -> None:
    with pytest.raises(KeyError):
        schema.mapping_to_row({"not_a_field": "x"})
    with pytest.raises(KeyError):
        schema.assert_writable(schema.PANEL, ["not_a_field"])
    with pytest.raises(PermissionError):
        schema.assert_writable(schema.PANEL, ["posted_url"])
    with pytest.raises(PermissionError):
        schema.assert_writable(schema.HOUSING_AGENT, ["listing_id"])
