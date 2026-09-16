from __future__ import annotations

from . import intake, pipeline
from shared.google_maps.client import MapsResolution
from shared.google_sheets import schema

def test_initial_row_is_canonical_and_stage_one_safe():
    row=pipeline.initial_row("EF-2609-0001",onboarded_on="2026-09-15T00:00:00+00:00")
    assert list(row)==list(schema.NAMES);assert row["listing_id"]=="EF-2609-0001";assert row["status"]=="Raw";assert row["intake_status"]=="Raw";assert row["onboarded_on"]=="2026-09-15T00:00:00+00:00";assert row["transaction_type"]=="Rent";assert row["city"]=="Bengaluru";assert row["posted_url"]=="";assert row["meta_catalog_id"]=="";assert row["source_group"]=="";assert row["inventory_locked"]==""
def test_deterministic_processing_preserves_verified_business_rules():
    raw="""Fully Furnished 2 BHK
Floor: 3/10
Built-up Area: 1200 sqft
Rent: 50000
Maintenance: Water Charges
Deposit: 2 months
Preferred Tenant: Family
Utility area
Gated Community"""
    row=pipeline.deterministic(raw,pipeline.initial_row("EF-2609-0002"));assert row["BHK"]=="2 BHK";assert row["property_subtype"]=="Apartment";assert row["floor_number"]=="3";assert row["total_floors"]=="10";assert row["carpet_area"]=="1080";assert row["monthly_rent"]=="50000";assert row["security_deposit"]=="100000";assert row["maintenance"]=="Water Charges";assert row["maintenance_included"]=="No";assert row["preferred_tenant_type"]=="Family";assert row["bachelor_preference"]=="";assert row["internal_property_type"]=="Gated Community";assert "Utility area" in row["property_highlights"];assert "Wardrobe" in row["flat_furnishings"];assert "Fridge" in row["flat_furnishings"]
def test_project_drops_historical_reserved_sheet_values():
    row=pipeline.initial_row("EF-2609-RESERVED",raw_text="2 BHK\nRent: 40000\nGated Community\nLocation: Harlur");row["source_group"]="historical-chat-id";row["inventory_locked"]="historical-lock";projected=pipeline.deterministic(row["raw_message_text"],row=row);assert projected["source_group"]=="";assert projected["inventory_locked"]==""
def test_family_bachelor_explicit_value_is_not_overwritten():
    raw="2 BHK\nRent: 40000\nPreferred Tenant: Family\nBachelor: Open for both";row=pipeline.deterministic(raw,pipeline.initial_row("EF-2609-0003"));assert row["preferred_tenant_type"]=="Family";assert row["bachelor_preference"]=="Open for both"
def test_family_female_bachelors_uses_exact_sheet_vocabulary():
    raw="2 BHK\nRent: 40000\nPreferred Tenant: Family & Female Bachelors";row=pipeline.deterministic(raw,pipeline.initial_row("EF-2609-0005"));assert row["preferred_tenant_type"]=="Open For All";assert row["bachelor_preference"]=="Female Only ";assert row["bachelor_preference"] in schema.BY_NAME["bachelor_preference"].allowed_values
def test_explicit_female_bachelor_preference_is_normalized_to_exact_sheet_value():
    raw="2 BHK\nRent: 40000\nPreferred Tenant: Open For All\nBachelor: Female Only";row=pipeline.deterministic(raw,pipeline.initial_row("EF-2609-0006"));assert row["bachelor_preference"]=="Female Only "
def test_real_message_formats_are_extracted_deterministically():
    raw="""👉Semi Furnished 2.5 BHK with 2 Bathrooms, 2 Balconies & Utility<br><br>Rent: 39K<br>Maintenance: Included<br>Deposit: 1.25L<br>Sqft: 1450<br>Floor: 2/4<br>Preferred tenant: Open For All<br>Pets: Allowed<br>Location: Harlur<br>Gated Community""";row=pipeline.deterministic(raw,pipeline.initial_row("EF-2609-0025"));assert row["BHK"]=="2.5 BHK";assert row["floor_number"]=="2";assert row["total_floors"]=="4";assert row["monthly_rent"]=="39000";assert row["maintenance"]=="0";assert row["maintenance_included"]=="Yes";assert row["security_deposit"]=="125000";assert row["preferred_tenant_type"]=="Open For All";assert row["pet_friendly"]=="Yes";assert row["internal_property_type"]=="Gated Community"
def test_semi_gated_uses_exact_sheet_amenity_combination():
    raw="2 BHK\nRent: 40000\nSemi Gated";row=pipeline.deterministic(raw,pipeline.initial_row("EF-2609-0007"));assert row["internal_property_type"]=="Semi Gated";assert row["society_amenities"]=="Security, Lift, CCTV, Power Backup"
def test_explicit_society_amenities_are_preserved_for_validation():
    raw="2 BHK\nRent: 40000\nGated Community\nAmenities: Club House, Lift, Gym, CCTV, Power Backup, Swimming Pool, Garden, Sports, Kids Area";row=pipeline.deterministic(raw,pipeline.initial_row("EF-2609-0008"));assert row["society_amenities"]=="Club House, Lift, Gym, CCTV, Power Backup, Swimming Pool, Garden, Sports, Kids Area"
def test_ground_floor_and_mixed_maintenance_are_normalized():
    raw="""Semi Furnished 2 BHK<br>Rent: 42K<br>Maintenance: 2,777 + Water<br>Deposit: 120000<br>Sqft: 1211<br>Floor: G/4<br>Preferred Tenant: Open For All<br>Pets: Not Allowed<br>Gated Community""";row=pipeline.deterministic(raw,pipeline.initial_row("EF-2609-0026"));assert row["floor_number"]=="0";assert row["total_floors"]=="4";assert row["maintenance"]=="2777 + Water";assert row["security_deposit"]=="120000"
def test_gated_colon_variant_is_classified_as_gated():
    raw="3 BHK\nRent: 75000\nFloor: 1/14\nGated: Community";row=pipeline.deterministic(raw,pipeline.initial_row("EF-2609-0027"));assert row["internal_property_type"]=="Gated Community";assert row["society_amenities"]=="Club House, Lift, Gym, CCTV, Power Backup, Swimming Pool, Garden, Sports, Kids Area"
def test_unfurnished_source_does_not_create_non_sheet_furnish_value():
    raw="2 BHK\nRent: 40000\nUnfurnished apartment";row=pipeline.deterministic(raw,pipeline.initial_row("EF-2609-0028"));assert row["furnish_type"]=="";assert row["flat_furnishings"]==""
def test_stage_two_maps_integration_accepts_only_verified_resolution():
    raw="""2.5 BHK semi furnished apartment for rent in Harlur.
Rent 60000 + maintenance.
Deposit 6 months.
2 bathrooms, 2 balconies.
5th floor out of 10.
Built-up area 1868 sqft.
Family preferred.
Gated community.
Google Maps: https://www.google.com/maps/search/?api=1&query=12.9081,77.6476
"""
    class FakeMaps:
        def extract_url(self,text):return "https://www.google.com/maps/search/?api=1&query=12.9081,77.6476"
        def resolve(self,*,maps_url="",address=""):
            assert maps_url
            return MapsResolution(canonical_url="https://www.google.com/maps/search/?api=1&query=12.9080334,77.6475765&query_place_id=test-place",formatted_address="1100, 23rd A Cross Rd, Garden Layout, Sector 2, HSR Layout, Bengaluru, Karnataka 560102, India",locality="HSR Layout",pincode="560102",latitude=12.9080334,longitude=77.6475765,confidence="VERIFIED")
    row=pipeline.initial_row("EF-TEST-STAGE2-MAPS",raw_text=raw);processed,issues=pipeline.process_closed_session(raw,row=row,maps_client=FakeMaps(),ai_llm=None);assert processed["status"]=="Pending";assert processed["intake_status"]=="Processed";assert processed["internal_property_type"]=="Gated Community";assert processed["BHK"]=="2.5 BHK";assert processed["built_up_area"]=="1868";assert processed["carpet_area"]=="1681";assert processed["monthly_rent"]=="60000";assert processed["security_deposit"]=="360000";assert processed["locality"]=="HSR Layout";assert processed["pincode"]=="560102";assert processed["google_maps_url"].startswith("https://www.google.com/maps/");assert issues==[];assert processed["source_group"]=="";assert processed["inventory_locked"]==""
def test_new_marker_opens_then_closes_same_sender_session():
    store=intake.InMemorySessionStore();sender="917975102130";assert intake.ingest({"sender":sender,"body":"NEW","chat_id":sender},store)[0]=="opened";state,session=intake.ingest({"sender":sender,"body":"2 BHK Rent 45000","message_id":"m1","chat_id":sender},store);assert state=="collecting";assert "2 BHK Rent 45000" in session.raw_text;state,closed=intake.ingest({"sender":sender,"body":"NEW","chat_id":sender},store);assert state=="closed";assert closed.raw_text.endswith("2 BHK Rent 45000");assert store.get(sender) is None
def test_duplicate_message_id_is_not_appended_twice():
    store=intake.InMemorySessionStore();sender="919902024973";intake.ingest({"sender":sender,"body":"NEW","chat_id":sender},store);msg={"sender":sender,"body":"Rent 50000","message_id":"same","chat_id":sender};intake.ingest(msg,store);intake.ingest(msg,store);session=store.get(sender);assert session is not None;assert session.raw_text.count("Rent 50000")==1
class FakeSheets:
    def __init__(self):self.writes=[]
    def write_ranges(self,spreadsheet_id,worksheet_name,updates):self.writes.extend((range_name,values) for range_name,values in updates)
    def write_range(self,spreadsheet_id,worksheet_name,range_name,values):self.writes.append((range_name,values))
def test_stage_two_writer_never_touches_reserved_or_downstream_columns():
    client=FakeSheets();row=pipeline.initial_row("EF-2609-0004");row["internal_property_type"]="Standalone";row["listing_state"]="Rented Out";row["posted_url"]="https://housing.example/listing";row["posted_at"]="2026-09-15T00:00:00Z";row["error_notes"]="existing downstream state";row["meta_catalog_id"]="meta-1";row["meta_catalog_status"]="active";row["source_group"]="historical-chat-id";row["inventory_locked"]="historical-lock";pipeline.write_phase1_update(client,12,row);assert [x[0] for x in client.writes]==["A12:D12","F12:AO12"];assert all("E12" not in x[0] and "AP12" not in x[0] and "AU12" not in x[0] and "AV12" not in x[0] for x in client.writes)
