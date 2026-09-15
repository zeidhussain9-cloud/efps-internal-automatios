from __future__ import annotations

from src.pipeline import deterministic
from src import extract
from src import validate


def test_internal_property_type_has_single_source_of_truth_and_no_sheet_fallback():
    raw = "2 BHK\nRent: 40000\nLocation: Harlur"
    row = {"internal_property_type": "Gated Community", "society_amenities": "-"}
    out = deterministic(raw, row=row)
    assert out["internal_property_type"] == "Standalone"
    assert out["society_amenities"] == "-"


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


def test_maintenance_included_is_independent_from_amount():
    out = deterministic("Rent: 50000\nMaintenance: 3.7K included")
    assert out["maintenance"] == "3700"
    assert out["maintenance_included"] == "Yes"


def test_maintenance_qualifier_is_not_allowed_to_break_validation():
    out = deterministic("Rent: 50000\nMaintenance: 2777 + Water")
    assert out["maintenance"] == "2777 + Water"
    assert out["maintenance_included"] == "No"
    assert not any("maintenance" in e for e in validate.validate(out) if "maintenance" in e)


def test_unrelated_numbers_never_become_maintenance():
    out = extract.scan("Rent: 50000\nDeposit: 3L\nSqft: 1500")
    assert "maintenance" not in out


def test_model_projection_normalizes_units_but_does_not_use_sheet_values():
    raw = "Semi Furnished 2.5 BHK\nMaintenance: 8.2K\nLocation: Harlur"
    row = {"BHK": "5 BHK", "maintenance": "8", "internal_property_type": "Gated Community"}
    out = deterministic(raw, row=row)
    assert out["BHK"] == "2.5 BHK"
    assert out["maintenance"] == "8200"
    assert out["internal_property_type"] == "Standalone"
