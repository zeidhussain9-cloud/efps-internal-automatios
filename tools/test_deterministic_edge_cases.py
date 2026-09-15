"""Focused regression tests for the 2026-09-15 deterministic extraction review."""
from __future__ import annotations

from modules.efps_inventory_mgmnt.src.field_resolution import resolve_internal_property_type, resolve_property_subtype, resolve_maintenance
from modules.efps_inventory_mgmnt.src import extract, normalize


def test_gated_colon_community():
    assert resolve_internal_property_type("Gated: Community") == "Gated Community"


def test_duplex_villa_is_villa():
    assert resolve_property_subtype("Fully Furnished 4 BHK Duplex Villa") == "Villa"


def test_one_rk_is_studio():
    assert resolve_property_subtype("1 RK with balcony") == "Studio"


def test_pet_negative_wins():
    assert normalize._pet_value("Pets: Not Allowed") == "No"
    assert normalize._pet_value("Pets: Allowed") == "Yes"


def test_singular_balcony_is_one():
    result = extract.scan("Semi Furnished 2.5 BHK with 2 Bathrooms, Balcony & Utility")
    assert result["balconies"] == "1"


def test_landmark_maps_url_is_not_landmark():
    result = extract.scan("Location: Harlur\n📍 Landmark:\nhttps://maps.app.goo.gl/example")
    assert result.get("landmark", "") == ""
    assert result.get("google_maps_url", "").startswith("https://maps.app.goo.gl/")


def test_society_marker_and_maps_url_are_separate():
    result = extract.scan("Location: Harlur\n📍 BM Silver Woods:\nhttps://maps.app.goo.gl/example")
    assert result["society_name"] == "BM Silver Woods"
    assert result["google_maps_url"].startswith("https://maps.app.goo.gl/")


def test_maintenance_included_contract():
    assert resolve_maintenance("Maintenance: Included") == ("0", "Yes")
    assert resolve_maintenance("Maintenance: Included + Water") == ("0 + Water", "Yes")
    assert resolve_maintenance("Maintenance: 5K") == ("5000", "No")


def test_parking_and_amenities_follow_property_type():
    row = {"internal_property_type": "Gated Community", "covered_parking": "", "society_amenities": ""}
    normalize.apply_parking_defaults(row)
    assert row["covered_parking"] == "1"


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
    print("deterministic edge-case tests: PASS")
