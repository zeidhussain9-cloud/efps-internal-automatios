import sys
from pathlib import Path

MODULE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MODULE_ROOT))

from src.extract import scan
from src.normalize import normalize


def test_timestamped_direct_fields_stop_at_next_message():
    raw = (
        "[2026-09-15 10:00] Property Type: Semi Gated\n"
        "[2026-09-15 10:01] Society Name: Example Residency\n"
        "[2026-09-15 10:02] Landmark: Near Main Road\n"
        "[2026-09-15 10:03] Location: Harlur\n"
        "[2026-09-15 10:04] Rent: 40000\n"
    )
    extracted = scan(raw)
    assert extracted["internal_property_type"] == "Semi Gated"
    assert extracted["society_name"] == "Example Residency"
    assert extracted["landmark"] == "Near Main Road"
    assert extracted["locality"] == "Harlur"
    assert extracted["monthly_rent"] == "40000"


def test_timestamped_direct_fields_support_inline_message_delimiters():
    raw = (
        "2026-09-15 10:00 Property Type: Gated Community | "
        "2026-09-15 10:01 Society Name: Example Heights | "
        "2026-09-15 10:02 Location: Bellandur"
    )
    extracted = scan(raw)
    assert extracted["internal_property_type"] == "Gated Community"
    assert extracted["society_name"] == "Example Heights"
    assert extracted["locality"] == "Bellandur"


def test_property_type_normalization_prefers_explicit_semi_gated():
    raw = "[2026-09-15 10:00] Property Type: Semi Gated"
    row = {"internal_property_type": "", "society_amenities": ""}
    out = normalize(row, raw)
    assert out["internal_property_type"] == "Semi Gated"
    assert out["society_amenities"] == "Security, Lift, CCTV, Power Backup"


def test_mixed_maintenance_is_preserved_as_source_fact():
    raw = "[2026-09-15 10:00] Maintenance: 2777 + Water"
    row = {"maintenance": ""}
    out = normalize(row, raw)
    assert out["maintenance"] == "2777 + Water"
    assert out["maintenance_included"] == "No"
