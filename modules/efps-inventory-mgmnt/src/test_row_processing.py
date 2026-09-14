from __future__ import annotations

from . import pipeline


def test_deterministic_full_contract_for_common_listing():
    raw = """Fully Furnished 2 BHK
Floor: 3/10
Built-up Area: 1200 sqft
Rent: 50000
Maintenance: Water Charges
Deposit: 2 months
Preferred Tenant: Family
Utility area
Gated Community"""
    row = pipeline.deterministic(raw, pipeline.initial_row("EF-2609-2001"))

    assert row["listing_id"] == "EF-2609-2001"
    assert row["BHK"] == "2 BHK"
    assert row["property_subtype"] == "Apartment"
    assert row["floor_number"] == "3"
    assert row["total_floors"] == "10"
    assert row["built_up_area"] == "1200"
    assert row["carpet_area"] == "1080"
    assert row["monthly_rent"] == "50000"
    assert row["security_deposit"] == "100000"
    assert row["maintenance"] == "Water Charges"
    assert row["maintenance_included"] == "No"
    assert row["preferred_tenant_type"] == "Family"
    assert row["bachelor_preference"] == "Not Allowed"
    assert row["internal_property_type"] == "Gated Community"
    assert row["city"] == "Bengaluru"
    assert row["transaction_type"] == "Rent"

    assert row["posted_url"] == ""
    assert row["posted_at"] == ""
    assert row["error_notes"] == ""
    assert row["meta_catalog_id"] == ""
    assert row["meta_catalog_status"] == ""
    assert row["inventory_locked"] == ""
