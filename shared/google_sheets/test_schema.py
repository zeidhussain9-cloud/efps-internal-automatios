from __future__ import annotations

import pytest
from . import schema
EXPECTED=("listing_id","status","intake_status","internal_property_type","listing_state","onboarded_on","raw_message_text","locality","society_name","landmark","pincode","google_maps_url","furnish_type","BHK","bathrooms","balconies","floor_number","total_floors","built_up_area","carpet_area","monthly_rent","maintenance","maintenance_included","security_deposit","preferred_tenant_type","bachelor_preference","pet_friendly","servant_room","covered_parking","open_parking","society_amenities","flat_furnishings","property_highlights","catalog_title","cloudinary_image_urls","age_of_property_years","whatsapp_contact_link","whatsapp_group_link","transaction_type","property_subtype","city","posted_url","posted_at","error_notes","meta_catalog_id","meta_catalog_status","source_group","inventory_locked")
def test_contract_is_exactly_latest_48_columns():
    assert schema.NAMES==EXPECTED;assert schema.GRID_WIDTH==48;assert schema.LAST_COLUMN=="AV"
    for name,column in {"listing_id":"A","raw_message_text":"G","google_maps_url":"L","transaction_type":"AM","property_subtype":"AN","city":"AO","posted_url":"AP","posted_at":"AQ","error_notes":"AR","meta_catalog_id":"AS","meta_catalog_status":"AT","source_group":"AU","inventory_locked":"AV"}.items():assert schema.letter(name)==column
def test_verified_sheet_vocabularies_are_recorded_in_schema():
    assert schema.BY_NAME["internal_property_type"].allowed_values==("Gated Community","Semi Gated","Standalone")
    assert schema.BY_NAME["furnish_type"].allowed_values==("Fully Furnished","Semi Furnished")
    assert schema.BY_NAME["preferred_tenant_type"].allowed_values==("Family","Open For All")
    assert schema.BY_NAME["bachelor_preference"].allowed_values==("Female Only ","Male Only","Open for both")
    assert schema.BY_NAME["pet_friendly"].allowed_values==("Yes","No")
    assert schema.BY_NAME["society_amenities"].allowed_values==("Security, Lift, CCTV, Power Backup","Club House, Lift, Gym, CCTV, Power Backup, Swimming Pool, Garden, Sports, Kids Area","-")
    assert schema.BY_NAME["flat_furnishings"].allowed_values==("Wardrobe, Modular Kitchen, Geyser, Fan, Light","Wardrobe, Modular Kitchen, Geyser, Fan, Light, Fridge, Washing Machine, TV, Sofa, Bed, Dining Table")
def test_reserved_columns_are_physical_but_not_operational():
    assert schema.RESERVED_COLUMNS==("source_group","inventory_locked")
    assert schema.owner_of("source_group")==schema.RESERVED and schema.owner_of("inventory_locked")==schema.RESERVED
    assert schema.BY_NAME["source_group"].stage==schema.RESERVED_STAGE and schema.BY_NAME["inventory_locked"].stage==schema.RESERVED_STAGE
    assert "source_group" not in schema.writable_by(schema.PANEL) and "inventory_locked" not in schema.writable_by(schema.PANEL)
    with pytest.raises(PermissionError):schema.assert_writable(schema.PANEL,["source_group"])
    with pytest.raises(PermissionError):schema.assert_writable(schema.PANEL,["inventory_locked"])
def test_verified_field_dependencies_are_recorded_in_schema():
    assert schema.BY_NAME["society_amenities"].depends_on==("internal_property_type",);assert schema.BY_NAME["flat_furnishings"].depends_on==("furnish_type",);assert schema.BY_NAME["bachelor_preference"].depends_on==("preferred_tenant_type",);assert schema.BY_NAME["maintenance"].depends_on==("maintenance_included",);assert schema.BY_NAME["security_deposit"].depends_on==("monthly_rent",)
def test_row_mapping_round_trip():
    row=[f"v{i}" for i in range(schema.GRID_WIDTH)];assert schema.mapping_to_row(schema.row_to_mapping(row))==row
def test_row_width_is_enforced():
    with pytest.raises(ValueError):schema.validate_row(["only-one"])
def test_downstream_ownership_is_exact():
    assert schema.writable_by(schema.HOUSING_AGENT)==("posted_url","posted_at","error_notes");assert schema.writable_by(schema.META_CATALOG)==("meta_catalog_id","meta_catalog_status")
def test_unknown_and_foreign_writes_are_rejected():
    with pytest.raises(KeyError):schema.mapping_to_row({"not_a_field":"x"})
    with pytest.raises(KeyError):schema.assert_writable(schema.PANEL,["not_a_field"])
    with pytest.raises(PermissionError):schema.assert_writable(schema.PANEL,["posted_url"])
    with pytest.raises(PermissionError):schema.assert_writable(schema.HOUSING_AGENT,["listing_id"])
