"""Pure deterministic regression checks derived from the 2026-09-15 projection audit."""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

MODULE_ROOT = Path(__file__).resolve().parents[1] / "modules" / "efps-inventory-mgmnt"
sys.path.insert(0, str(MODULE_ROOT))
field_resolution = importlib.import_module("src.field_resolution")
extract = importlib.import_module("src.extract")
pipeline = importlib.import_module("src.pipeline")

CASES = [
    ("explicit_gated_community", "Gated Community\nLocation: Harlur", lambda r: r == "Gated Community", field_resolution.resolve_internal_property_type),
    ("explicit_gated_colon_community", "Gated: Community\nLocation: Kasavanahalli", lambda r: r == "Gated Community", field_resolution.resolve_internal_property_type),
    ("explicit_semi_gated_colon_community", "Semi Gated: Community\nLocation: Harlur", lambda r: r == "Semi Gated", field_resolution.resolve_internal_property_type),
    ("negative_gating_does_not_claim_gated", "Gated: No\nLocation: Harlur", lambda r: r == "Standalone", field_resolution.resolve_internal_property_type),
    ("maintenance_included", "Rent: 70K\nMaintenance: Included", lambda r: r == ("0", "Yes"), field_resolution.resolve_maintenance),
    ("maintenance_included_water", "Rent: 42K\nMaintenance: Included + Water", lambda r: r == ("0 + Water", "Yes"), field_resolution.resolve_maintenance),
    ("maintenance_amount_water", "Rent: 42K\nMaintenance: 2,777 + Water", lambda r: r == ("2777 + Water", "No"), field_resolution.resolve_maintenance),
    ("maintenance_rent_suffix", "Rent: 50K + 6K Maintenance", lambda r: r == ("6000", "No"), field_resolution.resolve_maintenance),
    ("decimal_bhk_preserved", "Semi Furnished 2.5 BHK with 2 Bathrooms", lambda r: r == "2.5 BHK", field_resolution.resolve_bhk),
    ("duplex_villa_subtype", "Fully Furnished 4 BHK Duplex Villa", lambda r: r == "Villa", field_resolution.resolve_property_subtype),
    ("studio_subtype", "1 RK for Rent", lambda r: r == "Studio", field_resolution.resolve_property_subtype),
    ("singular_balcony", "Semi Furnished 3 BHK with Balcony", lambda r: r.get("balconies") == "1", extract.scan),
]


def main() -> int:
    failures: list[str] = []
    for name, source, predicate, fn in CASES:
        result = fn(source)
        ok = predicate(result)
        print(f"{name}: {'PASS' if ok else 'FAIL'} | {result!r}")
        if not ok:
            failures.append(name)

    integration_source = "Semi Furnished 3 BHK with 3 Bathrooms & 2 Balconies\nPets: Not Allowed\nGated Community"
    case = pipeline.deterministic(integration_source)
    integration = {
        "internal_property_type": case.get("internal_property_type") == "Gated Community",
        "balconies": case.get("balconies") == "2",
        "pet_friendly": case.get("pet_friendly") == "No",
        "covered_parking": case.get("covered_parking") == "1",
        "society_amenities": case.get("society_amenities") == "Club House, Lift, Gym, CCTV, Power Backup, Swimming Pool, Garden, Sports, Kids Area",
    }
    for name, ok in integration.items():
        print(f"integration_{name}: {'PASS' if ok else 'FAIL'} | {case.get(name)!r}")
        if not ok:
            failures.append(f"integration_{name}")

    if failures:
        print("FAILED:", ", ".join(failures))
        return 1
    print("ALL PROJECTION REGRESSIONS PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
