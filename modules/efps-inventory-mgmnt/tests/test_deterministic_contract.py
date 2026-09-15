from __future__ import annotations

from src.pipeline import deterministic
from src import extract
from src import validate


def test_internal_property_type_has_single_source_of_truth_and_no_sheet_fallback():
    raw = "2 BHK\nRent: 40000\nLocation: Harlur"
    row = {"internal_property_type": "Gated Community", "society_amenities": "-"}
    out = deterministic(raw, row=row)
    assert out["internal_property_type"] == ""
    assert out["society_amenities"] == ""


def test_explicit_property_type_overrides_generic_wording_in_same_source():
    raw = "Property Type: Semi Gated\nNote: gated community amenities are not applicable"
    out = deterministic(raw)
    assert out["internal_property_type"] == "Semi Gated"
    assert out["society_amenities"] == "Security, Lift, CCTV, Power Backup"


def test_later_explicit_property_type_correction_wins():
    raw = "Property Type: Gated Community\nProperty Type: Standalone"
    out = deterministic(raw)
    assert out["internal_property_type"] == "Standalone"
    assert out["society_amenities"] == "-"


def test_negative_gating_is_terminal_against_later_generic_positive_wording():
    raw = "Gated Community: No\nNote: gated community amenities mentioned elsewhere"
    out = deterministic(raw)
    assert out["internal_property_type"] == "Standalone"
    assert out["society_amenities"] == "-"


def test_gated_community_source_syntax_is_supported():
    out = deterministic("2 BHK\nRent: 50000\nGated: Community\nLocation: Harlur")
    assert out["internal_property_type"] == "Gated Community"
    assert out["covered_parking"] == "1"
    assert out["society_amenities"] == "Club House, Lift, Gym, CCTV, Power Backup, Swimming Pool, Garden, Sports, Kids Area"


def test_semi_gated_source_syntax_is_supported():
    out = deterministic("2 BHK\nRent: 50000\nSemi Gated: Community\nLocation: Harlur")
    assert out["internal_property_type"] == "Semi Gated"
    assert out["covered_parking"] == "1"


def test_maintenance_included_is_zero_and_yes():
    out = deterministic("Rent: 50000\nMaintenance: Included")
    assert out["maintenance"] == "0"
    assert out["maintenance_included"] == "Yes"


def test_maintenance_included_plus_water_is_water_additional():
    out = deterministic("Rent: 50000\nMaintenance: Included + Water")
    assert out["maintenance"] == "Water Charges Additional"
    assert out["maintenance_included"] == "Yes"
    errors = validate.validate(out)
    assert not any("maintenance" in e for e in errors)


def test_maintenance_amount_is_not_included():
    out = deterministic("Rent: 50000\nMaintenance: 2777")
    assert out["maintenance"] == "2777"
    assert out["maintenance_included"] == "No"


def test_maintenance_qualifier_is_preserved():
    out = deterministic("Rent: 50000\nMaintenance: 2777 + Water")
    assert out["maintenance"] == "2777 + Water"
    assert out["maintenance_included"] == "No"
    assert not any("maintenance" in e for e in validate.validate(out))


def test_unrelated_numbers_never_become_maintenance():
    out = extract.scan("Rent: 50000\nDeposit: 3L\nSqft: 1500")
    assert "maintenance" not in out


def test_duplex_villa_is_portal_villa():
    out = deterministic("4 BHK Duplex Villa\nRent: 80000\nLocation: Harlur")
    assert out["property_subtype"] == "Villa"


def test_one_rk_is_studio():
    out = deterministic("1 RK\nRent: 20000\nLocation: Harlur")
    assert out["BHK"] == "1 RK"
    assert out["property_subtype"] == "Studio"


def test_normal_apartment_is_apartment():
    out = deterministic("2 BHK Apartment\nRent: 40000\nLocation: Harlur")
    assert out["property_subtype"] == "Apartment"


def test_maps_url_is_extracted_without_network_enrichment():
    raw = "Location: Kartik Nagar, Doddanekundi\n📍 Bren Avalon:\nhttps://maps.app.goo.gl/example"
    out = deterministic(raw)
    assert out["google_maps_url"] == "https://maps.app.goo.gl/example"
    assert out["society_name"] == "Bren Avalon"


def test_landmark_maps_url_is_not_stored_as_landmark():
    raw = "Location: Harlur\n📍 Landmark:\nhttps://maps.app.goo.gl/example"
    out = deterministic(raw)
    assert out["google_maps_url"] == "https://maps.app.goo.gl/example"
    assert out["landmark"] == ""


def test_locality_is_not_copied_to_landmark_during_deterministic_projection():
    out = deterministic("2 BHK\nRent: 40000\nLocation: Harlur")
    assert out["locality"] == "Harlur"
    assert out["landmark"] == ""


def test_society_name_fallback_is_last_resort_in_production_path():
    out = deterministic("2 BHK\nRent: 40000\nLocation: Harlur")
    assert out["society_name"] == ""


def test_model_projection_normalizes_units_but_does_not_use_sheet_values():
    raw = "Semi Furnished 2.5 BHK\nMaintenance: 8.2K\nLocation: Harlur"
    row = {"BHK": "5 BHK", "maintenance": "8", "internal_property_type": "Gated Community"}
    out = deterministic(raw, row=row)
    assert out["BHK"] == "2.5 BHK"
    assert out["maintenance"] == "8200"
    assert out["internal_property_type"] == ""
