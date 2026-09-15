from __future__ import annotations

from . import pipeline


def test_direct_property_fields_and_fallbacks():
    raw = """2 BHK
Rent: 40000
Internal Property Type: Gated Community
Society Name: Lakeview Residency
Landmark: Harlur Main Road
Location: Harlur
Property Subtype: Apartment
Preferred Tenant: Anyone
Pets: Not Allowed
Servant Room: Yes
"""
    row = pipeline.deterministic(raw, pipeline.initial_row("EF-TEST-DIRECT-001"))
    assert row["internal_property_type"] == "Gated Community"
    assert row["society_name"] == "Lakeview Residency"
    assert row["landmark"] == "Harlur Main Road"
    assert row["locality"] == "Harlur"
    assert row["preferred_tenant_type"] == "Open For All"
    assert row["pet_friendly"] == "No"
    assert row["servant_room"] == "Yes"


def test_missing_society_and_landmark_use_location():
    raw = "2 BHK\nRent: 40000\nLocation: Harlur\nGated Community"
    row = pipeline.deterministic(raw, pipeline.initial_row("EF-TEST-DIRECT-002"))
    assert row["locality"] == "Harlur"
    assert row["society_name"] == "Harlur"
    assert row["landmark"] == "Harlur"


def test_pet_last_resort_is_yes_and_explicit_not_allowed_is_no():
    allowed = pipeline.deterministic("2 BHK\nRent: 40000\nLocation: Harlur", pipeline.initial_row("EF-TEST-PET-001"))
    blocked = pipeline.deterministic("2 BHK\nRent: 40000\nPets: Not Allowed", pipeline.initial_row("EF-TEST-PET-002"))
    assert allowed["pet_friendly"] == "Yes"
    assert blocked["pet_friendly"] == "No"


def test_covered_parking_defaults_for_gated_and_semi_gated():
    gated = pipeline.deterministic("2 BHK\nRent: 40000\nGated Community", pipeline.initial_row("EF-TEST-PARK-001"))
    semi = pipeline.deterministic("2 BHK\nRent: 40000\nSemi Gated", pipeline.initial_row("EF-TEST-PARK-002"))
    standalone = pipeline.deterministic("2 BHK\nRent: 40000\nStandalone", pipeline.initial_row("EF-TEST-PARK-003"))
    assert gated["covered_parking"] == "1"
    assert semi["covered_parking"] == "1"
    assert standalone["covered_parking"] == ""


def test_tenant_variants_normalize_to_sheet_vocabulary():
    for raw_value in ("Anyone", "anyone", "Open For All", "Vegetarian Family", "Family & Female"):
        row = pipeline.deterministic(
            f"2 BHK\nRent: 40000\nPreferred Tenant: {raw_value}",
            pipeline.initial_row("EF-TEST-TENANT-001"),
        )
        assert row["preferred_tenant_type"] in {"Family", "Open For All"}


def test_standalone_amenities_use_sheet_dash():
    row = pipeline.deterministic("2 BHK\nRent: 40000\nStandalone", pipeline.initial_row("EF-TEST-AMENITY-001"))
    assert row["internal_property_type"] == "Standalone"
    assert row["society_amenities"] == "-"


def test_property_subtype_is_direct_when_present_and_apartment_only_as_fallback():
    direct = pipeline.deterministic("2 BHK\nRent: 40000\nProperty Subtype: Villa", pipeline.initial_row("EF-TEST-SUBTYPE-001"))
    apartment = pipeline.deterministic("2 BHK\nRent: 40000\nFloor: 2/5", pipeline.initial_row("EF-TEST-SUBTYPE-002"))
    independent = pipeline.deterministic("2 BHK\nRent: 40000\nIndependent House", pipeline.initial_row("EF-TEST-SUBTYPE-003"))
    assert direct["property_subtype"] == "Villa"
    assert apartment["property_subtype"] == "Apartment"
    assert independent["property_subtype"] == ""


def test_catalog_title_and_highlights_are_deterministic_fallbacks():
    raw = "Semi Furnished 2 BHK\nRent: 40000\nLocation: Harlur\nUtility area"
    row = pipeline.deterministic(raw, pipeline.initial_row("EF-TEST-WORDING-001"))
    assert row["catalog_title"] == "Semi Furnished 2 BHK for Rent - Harlur"
    assert "Utility area" in row["property_highlights"]


def test_age_of_property_remains_blank_without_explicit_source_fact():
    row = pipeline.deterministic("2 BHK\nRent: 40000\nLocation: Harlur", pipeline.initial_row("EF-TEST-AGE-001"))
    assert row["age_of_property_years"] == ""
