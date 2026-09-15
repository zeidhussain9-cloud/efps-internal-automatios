import sys
from pathlib import Path

MODULE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MODULE_ROOT))

from src.extract import scan
from src.normalize import normalize
from src.pipeline import deterministic
from src.source_segments import split_source_messages


def test_timestamped_direct_fields_stop_at_next_message():
    raw = "[2026-09-15 10:00] Property Type: Semi Gated\n[2026-09-15 10:01] Society Name: Example Residency\n[2026-09-15 10:02] Landmark: Near Main Road\n[2026-09-15 10:03] Location: Harlur\n[2026-09-15 10:04] Rent: 40000"
    extracted = scan(raw)
    assert extracted["internal_property_type"] == "Semi Gated"
    assert extracted["society_name"] == "Example Residency"
    assert extracted["landmark"] == "Near Main Road"
    assert extracted["locality"] == "Harlur"
    assert extracted["monthly_rent"] == "40000"


def test_timestamped_direct_fields_support_inline_message_delimiters():
    raw = "2026-09-15 10:00 Property Type: Gated Community | 2026-09-15 10:01 Society Name: Example Heights | 2026-09-15 10:02 Location: Bellandur"
    extracted = scan(raw)
    assert extracted["internal_property_type"] == "Gated Community"
    assert extracted["society_name"] == "Example Heights"
    assert extracted["locality"] == "Bellandur"


def test_source_segmentation_handles_bracketed_and_inline_timestamps():
    raw = "[2026-09-15 10:00] Property Type: Semi Gated\n2026-09-15 10:01 Society Name: Example Heights | 2026-09-15 10:02 Location: Bellandur"
    assert split_source_messages(raw) == ["Property Type: Semi Gated", "Society Name: Example Heights", "Location: Bellandur"]


def test_direct_field_does_not_consume_following_message():
    raw = "[2026-09-15 10:00] Society Name: First Residency\n[2026-09-15 10:01] Society Name: Second Residency\n[2026-09-15 10:02] Location: Harlur"
    assert scan(raw)["society_name"] == "First Residency"


def test_boolean_gated_field_is_authoritative():
    raw = "[2026-09-15 10:00] Property Type: Apartment\n[2026-09-15 10:01] Gated Community: Yes\n[2026-09-15 10:02] Location: Whitefield"
    out = deterministic(raw)
    assert out["internal_property_type"] == "Gated Community"
    assert out["society_amenities"] == "Club House, Lift, Gym, CCTV, Power Backup, Swimming Pool, Garden, Sports, Kids Area"


def test_boolean_semi_gated_field_is_authoritative():
    raw = "[2026-09-15 10:00] Property Type: Apartment\n[2026-09-15 10:01] Semi Gated: Yes\n[2026-09-15 10:02] Location: Harlur"
    out = deterministic(raw)
    assert out["internal_property_type"] == "Semi Gated"
    assert out["society_amenities"] == "Security, Lift, CCTV, Power Backup"


def test_negative_boolean_gated_field_is_not_positive_gating_evidence():
    raw = "[2026-09-15 10:00] Gated Community: No"
    out = deterministic(raw)
    assert out["internal_property_type"] == "Standalone"
    assert out["society_amenities"] == "-"


def test_property_type_normalization_prefers_explicit_semi_gated():
    raw = "[2026-09-15 10:00] Property Type: Semi Gated"
    out = deterministic(raw)
    assert out["internal_property_type"] == "Semi Gated"
    assert out["society_amenities"] == "Security, Lift, CCTV, Power Backup"


def test_mixed_maintenance_is_preserved_as_source_fact():
    raw = "[2026-09-15 10:00] Maintenance: 2777 + Water"
    extracted = scan(raw)
    assert extracted["maintenance"] == "2777 + Water"
    assert extracted["maintenance_included"] == "No"


def test_maintenance_k_value_is_normalized_without_losing_amount():
    assert scan("[2026-09-15 10:00] Maintenance: 3.7K")["maintenance"] == "3700"
    assert scan("[2026-09-15 10:00] Maintenance: 8.2K")["maintenance"] == "8200"


def test_rent_plus_maintenance_format_uses_second_amount():
    assert scan("[2026-09-15 10:00] Rent: 50K + 6K Maintenance")["maintenance"] == "6000"


def test_bhk_decimal_is_preserved():
    assert scan("[2026-09-15 10:00] Semi Furnished 2.5 BHK with 2 Bathrooms")["BHK"] == "2.5 BHK"


def test_later_bhk_message_is_treated_as_correction():
    raw = "[2026-09-15 10:00] BHK: 5 BHK\n[2026-09-15 10:01] Correct BHK: 2.5 BHK"
    assert scan(raw)["BHK"] == "2.5 BHK"


def test_negative_gating_cannot_be_overridden_by_later_generic_gated_text():
    raw = "[2026-09-15 10:00] Gated Community: No\n[2026-09-15 10:01] Note: gated community amenities not applicable"
    assert deterministic(raw)["internal_property_type"] == "Standalone"


def test_sheet_values_are_not_used_as_deterministic_source():
    raw = "[2026-09-15 10:00] Semi Furnished 2.5 BHK\n[2026-09-15 10:01] Maintenance: 5K\n[2026-09-15 10:02] Location: Harlur"
    row = {"BHK": "5 BHK", "maintenance": "3", "internal_property_type": "Gated Community"}
    out = deterministic(raw, row=row)
    assert out["BHK"] == "2.5 BHK"
    assert out["maintenance"] == "5000"
    assert out["internal_property_type"] == "Standalone"
