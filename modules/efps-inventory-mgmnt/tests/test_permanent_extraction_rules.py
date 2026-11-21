"""Proofs for the permanent extraction rules locked on 21 Nov 2026:
map-link caption standard, merged-field splitting, dropdown vocabulary lock,
catalog-title standard, tenant vocabulary merge."""
from __future__ import annotations

import pytest

from shared.ola_maps.links import MapsLinks
from src import notion_intake as intake
from src import pipeline


def test_standard_search_url_from_expanded_place_link():
    expanded = "https://www.google.com/maps/place/SJR+Park+Vista,+Off+Harlur+Rd,+HSR+Layout,+Bengaluru,+Karnataka+560102/data=!4m2!3m1!1s0x3bae137aba9d6727:0x18996930ebda7fd0"
    assert MapsLinks.standard_search_url(expanded) == (
        "https://www.google.com/maps/search/?api=1&query="
        "SJR+Park+Vista%2C+Off+Harlur+Rd%2C+HSR+Layout%2C+Bengaluru%2C+Karnataka+560102"
    ).replace("%2C", ",")


def test_standard_search_url_from_q_param_and_viewport_stripped():
    expanded = "https://www.google.com/maps?q=Sobha+Royal+Pavilion/@12.9122438,77.6638763,14z&ftid=0x3bae:0x1234"
    assert MapsLinks.standard_search_url(expanded) == "https://www.google.com/maps/search/?api=1&query=Sobha+Royal+Pavilion"


def test_standard_search_url_keeps_coordinate_query_comma():
    assert MapsLinks.standard_search_url("https://www.google.com/maps/search/?api=1&query=12.9081,77.6476") == \
        "https://www.google.com/maps/search/?api=1&query=12.9081,77.6476"


def test_standard_search_url_rejects_non_maps_and_queryless_links():
    assert MapsLinks.standard_search_url("https://example.com/maps/place/Foo") == ""
    assert MapsLinks.standard_search_url("https://www.google.com/maps?geocode=FXoAxQAdXTuhBA%3D%3D") == ""
    assert MapsLinks.standard_search_url("") == ""


def _row(**overrides):
    row = {
        "listing_id": "EF-2609-TEST",
        "furnish_type": "Semi Furnished",
        "BHK": "2 BHK",
        "bathrooms": "2",
        "monthly_rent": "45000",
        "security_deposit": "150000",
        "built_up_area": "1350",
        "floor_number": "2",
        "total_floors": "14",
        "locality": "Varthur",
        "society_name": "CLPD Sunrise",
        "google_maps_url": "https://maps.app.goo.gl/AbC123",
    }
    row.update(overrides)
    return row


def test_caption_carries_only_the_canonical_maps_url():
    resolved = "https://www.google.com/maps/search/?api=1&query=CLPD+Sunrise,+Varthur,+Bengaluru"
    caption = intake.build_whatsapp_post(
        _row(), "Pets: Not Allowed\nGated Community", maps_verified=False,
        resolved_maps_url=resolved,
    )
    assert resolved in caption
    assert "goo.gl" not in caption
    assert "Original Maps link" not in caption
    assert "*📍 CLPD Sunrise:" in caption


def test_caption_without_resolution_keeps_legacy_unverified_behaviour():
    caption = intake.build_whatsapp_post(
        _row(), "Pets: Not Allowed", maps_verified=False, allow_unverified_source_map=True,
    )
    assert "*📍 Original Maps link (not verified):\nhttps://maps.app.goo.gl/AbC123" in caption


def test_merged_pets_gating_line_splits_in_caption():
    raw = "Semi Furnished 1 RK\nRent: 15000\nLocation: Chikkanayakanahalli\nPets: Allowed Semi Gated"
    projected = pipeline.deterministic(raw, pipeline.initial_row("EF-2609-J8QY-STYLE"))
    assert projected["internal_property_type"] == "Semi Gated"
    assert projected["pet_friendly"] == "Yes"
    caption = intake.build_whatsapp_post(
        projected, raw, maps_verified=True,
        resolved_maps_url="https://www.google.com/maps/search/?api=1&query=Chikkanayakanahalli",
    )
    assert "\nPets: Allowed\n" in caption + "\n"
    assert "Semi Gated Community" in caption
    assert "Allowed Semi Gated" not in caption


def test_pipeline_sets_canonical_caption_url_from_expanded_link():
    raw = "2 BHK\nRent: 40000\nLocation: Harlur\nGated Community\nhttps://maps.app.goo.gl/AbC123"

    class FakeMaps:
        class _Resolution:
            confidence = "OLA_EVIDENCE"
            evidence = {"link_status": "reachable", "expanded_url": "https://www.google.com/maps/place/Prestige+Sunrise,+Harlur,+Bengaluru/data=!4m2!3m1!1s0x3bae:0x99"}
            locality = ""
            pincode = ""
            place_name = ""

        def resolve(self, *, maps_url="", address="", expected_locality=""):
            return self._Resolution()

    processed, _ = pipeline.process_closed_session(raw, row=pipeline.initial_row("EF-TEST-CAPTION-URL"), maps_client=FakeMaps())
    assert processed["_caption_maps_url"] == "https://www.google.com/maps/search/?api=1&query=Prestige+Sunrise,+Harlur,+Bengaluru"


def test_tenant_vocabulary_merges_family_variants_to_family_only():
    for raw_value in ("Family", "Family only", "Families Only", "family preferred"):
        row = pipeline.deterministic(f"2 BHK\nRent: 40000\nPreferred Tenant: {raw_value}", pipeline.initial_row("EF-TEST-TENANT-MERGE"))
        assert row["preferred_tenant_type"] == "Family Only", raw_value


def test_catalog_title_standard_is_furnish_bhk_location():
    row = pipeline.deterministic("Semi Furnished 3 BHK\nRent: 80000\nLocation: Haralur", pipeline.initial_row("EF-TEST-TITLE-001"))
    assert row["catalog_title"] == "Semi Furnished 3 BHK - Haralur"
    assert "for Rent" not in row["catalog_title"]


def test_select_vocabulary_lock_blocks_unknown_option():
    schema = {"Availability": {"type": "select", "select": {"options": [{"name": "Available"}, {"name": "Rented Out"}]}}}
    intake.enforce_select_vocabulary(schema, {"Availability": {"select": {"name": "Available"}}})
    with pytest.raises(intake.IntakeError):
        intake.enforce_select_vocabulary(schema, {"Availability": {"select": {"name": "Temporarily Free"}}})


def test_multi_select_vocabulary_lock_blocks_unknown_option():
    schema = {"live at": {"type": "multi_select", "multi_select": {"options": [{"name": "Meta Catalogue"}]}}}
    with pytest.raises(intake.IntakeError):
        intake.enforce_select_vocabulary(schema, {"live at": {"multi_select": [{"name": "Meta Catalogue"}, {"name": "Flyer"}]}})


def test_tenant_and_bachelor_serialize_as_dropdown_selects():
    from notion_intake import listing_notion_properties
    row = {
        "listing_id": "EF-2611-TEST", "catalog_title": "Semi Furnished 2 BHK - Haralur",
        "preferred_tenant_type": "Open For All", "bachelor_preference": "Female Only",
    }
    props = listing_notion_properties(row)
    assert props["preferred_tenant_type"] == {"select": {"name": "Open For All"}}
    assert props["bachelor_preference"] == {"select": {"name": "Female Only"}}
    # Blank values clear the dropdown instead of writing free text.
    row["bachelor_preference"] = ""
    props = listing_notion_properties(row)
    assert props["bachelor_preference"] == {"select": None}


def test_tenant_and_bachelor_locked_to_dropdown_options():
    import pytest
    from notion_intake import IntakeError, enforce_select_vocabulary, listing_notion_properties
    schema = {
        "preferred_tenant_type": {"type": "select", "select": {"options": [{"name": "Family Only"}, {"name": "Open For All"}]}},
        "bachelor_preference": {"type": "select", "select": {"options": [{"name": "Open for both"}, {"name": "Female Only"}, {"name": "Male Only"}]}},
    }
    row = {"listing_id": "EF-2611-TEST", "catalog_title": "T", "preferred_tenant_type": "Family", "bachelor_preference": "Females welcome"}
    with pytest.raises(IntakeError):
        enforce_select_vocabulary(schema, listing_notion_properties(row))


def test_bachelor_variants_normalize_to_dropdown_options():
    import pipeline
    for raw_bachelor, expected in (
        ("Bachelor: Female Only", "Female Only"),
        ("Bachelor: Not Allowed", "Not Allowed"),
        ("Bachelor: Open for both", "Open for both"),
    ):
        row = pipeline.deterministic(f"2 BHK\nRent: 40000\nPreferred Tenant: Open For All\n{raw_bachelor}", pipeline.initial_row("EF-2609-TST1"))
        assert row["bachelor_preference"] == expected, raw_bachelor
