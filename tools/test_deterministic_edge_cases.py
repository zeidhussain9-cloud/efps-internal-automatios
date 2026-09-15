"""Focused regression tests for the deterministic extraction contract."""
from __future__ import annotations
import pathlib
import sys

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT / "modules" / "efps-inventory-mgmnt"))

from src.field_resolution import resolve_internal_property_type, resolve_property_subtype, resolve_maintenance
from src import extract, normalize, pipeline


def test_gated_colon_community():
    assert resolve_internal_property_type("Gated: Community") == "Gated Community"

def test_explicit_community_variants_are_case_insensitive():
    cases=(
        ("Community: Gated Community","Gated Community"),
        ("community: gated","Gated Community"),
        ("COMMUNITY:GATED COMMUNITY","Gated Community"),
        ("Community : Semi-Gated Community","Semi Gated"),
        ("community: semigated","Semi Gated"),
        ("COMMUNITY: STAND ALONE","Standalone"),
        ("Community: stand-alone","Standalone"),
    )
    for raw,expected in cases:
        assert resolve_internal_property_type(raw) == expected

def test_explicit_negative_gating_is_standalone():
    assert resolve_internal_property_type("Gated: No") == "Standalone"

def test_unknown_gating_is_unresolved_not_false_standalone():
    assert resolve_internal_property_type("2 BHK Apartment\nLocation: Harlur") == ""

def test_community_name_is_never_used_as_property_type_evidence():
    raw="Fully Furnished 2 BHK\nLocation: Sarjapur Road\n📍Prima Hilife:\nhttps://maps.app.goo.gl/pL58dyhfPsSrsB9r6?g_st=ic"
    assert resolve_internal_property_type(raw) == ""
    row=pipeline.deterministic(raw)
    assert row["internal_property_type"] == ""
    assert row["society_name"] == "Prima Hilife"
    assert row["locality"] == "Sarjapur Road"
    assert row["google_maps_url"].startswith("https://maps.app.goo.gl/")

def test_explicit_community_type_drives_dependents():
    row=pipeline.deterministic("2 BHK\nRent: 40000\nCommunity: Gated Community")
    assert row["internal_property_type"] == "Gated Community"
    assert row["covered_parking"] == "1"
    assert row["society_amenities"] == "Club House, Lift, Gym, CCTV, Power Backup, Swimming Pool, Garden, Sports, Kids Area"

def test_duplex_villa_is_villa():
    assert resolve_property_subtype("Fully Furnished 4 BHK Duplex Villa") == "Villa"

def test_one_rk_is_studio():
    assert resolve_property_subtype("1 RK with balcony") == "Studio"

def test_pet_negative_wins():
    assert normalize._pet_value("Pets: Not Allowed") == "No"
    assert normalize._pet_value("Pets: Allowed") == "Yes"

def test_singular_balcony_is_one():
    result=extract.scan("Semi Furnished 2.5 BHK with 2 Bathrooms, Balcony & Utility")
    assert result["balconies"] == "1"

def test_landmark_maps_url_is_not_landmark():
    result=extract.scan("Location: Harlur\n📍 Landmark:\nhttps://maps.app.goo.gl/example")
    assert result.get("landmark","") == ""
    assert result.get("google_maps_url","").startswith("https://maps.app.goo.gl/")

def test_society_marker_and_maps_url_are_separate():
    result=extract.scan("Location: Harlur\n📍 BM Silver Woods:\nhttps://maps.app.goo.gl/example")
    assert result["society_name"] == "BM Silver Woods"
    assert result["google_maps_url"].startswith("https://maps.app.goo.gl/")

def test_maintenance_included_contract():
    assert resolve_maintenance("Maintenance: Included") == ("0","Yes")
    assert resolve_maintenance("Maintenance: Included + Water") == ("0 + Water","Yes")
    assert resolve_maintenance("Maintenance: 5K") == ("5000","No")

def test_parking_default_follows_property_type():
    row={"internal_property_type":"Gated Community","covered_parking":""}
    normalize.apply_parking_defaults(row)
    assert row["covered_parking"] == "1"

def test_open_for_all_defaults_to_exact_sheet_dropdown_value():
    row={"preferred_tenant_type":"Open For All","bachelor_preference":""}
    normalize.apply_tenant_bachelor_rule(row,"Preferred Tenant: Open For All")
    assert row["preferred_tenant_type"] == "Open For All"
    assert row["bachelor_preference"] == "Open for both"

def test_explicit_bachelor_source_overrides_open_for_all_default():
    row={"preferred_tenant_type":"Open For All","bachelor_preference":"Female Only "}
    normalize.apply_tenant_bachelor_rule(row,"Preferred Tenant: Open For All\nBachelor Preference: Female Only")
    normalize.normalize_bachelor_preference(row)
    assert row["bachelor_preference"] == "Female Only "

def test_family_clears_bachelor_preference():
    row={"preferred_tenant_type":"Family","bachelor_preference":"Male Only"}
    normalize.apply_tenant_bachelor_rule(row,"Preferred Tenant: Family")
    assert row["bachelor_preference"] == ""

if __name__ == "__main__":
    for name,fn in sorted(globals().items()):
        if name.startswith("test_"):fn()
    print("deterministic edge-case tests: PASS")
