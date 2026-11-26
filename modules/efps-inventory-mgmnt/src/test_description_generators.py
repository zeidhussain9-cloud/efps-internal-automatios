"""Focused tests for independent customer-facing description formatters."""
from __future__ import annotations

from description_generators import (
    build_facebook_marketplace_description,
    build_whatsapp_group_description,
)


def _row(**overrides):
    row = {
        "furnish_type": "Semi Furnished",
        "BHK": "2 BHK",
        "locality": "Haralur",
        "monthly_rent": 45000,
        "maintenance": "5000",
        "security_deposit": 135000,
        "built_up_area": 1100,
        "floor_number": "3",
        "total_floors": 5,
        "preferred_tenant_type": "Open For All",
        "internal_property_type": "Semi Gated",
        "bathrooms": 2,
        "balconies": 1,
        "society_name": "Private Society Name",
        "landmark": "Haralur Main Road",
    }
    row.update(overrides)
    return row


def test_group_title_and_field_order_follow_v8():
    text = build_whatsapp_group_description(
        _row(), "Pets allowed. Available from: Immediately.", maps_verified=False
    )
    assert text.startswith("*👉Semi Furnished 2 BHK with 2 Bathrooms & 1 Balcony*")
    assert "Rent: 45K" in text
    assert "Maintenance: 5K" in text
    assert "Deposit: 1.35L" in text
    assert "Sqft: 1100" in text
    assert "Floor: 3/5" in text
    assert "Available from: Ready to Occupy" in text
    assert "Preferred tenant: Open For All" in text
    assert "Pets: Allowed" in text
    assert "Semi Gated" in text
    assert "Location: *Haralur*" in text
    assert "Private Society Name" not in text


def test_group_uses_only_original_short_maps_link_when_verified():
    raw = "Semi Furnished 2 BHK https://maps.app.goo.gl/AbCdEf123"
    text = build_whatsapp_group_description(
        _row(), raw, verified_society_name="Verified Society", maps_verified=True
    )
    assert "*📍 Verified Society:*" in text
    assert "https://maps.app.goo.gl/AbCdEf123" in text


def test_group_keeps_exact_raw_maps_url_as_unverified_fallback():
    issues = []
    raw_url = "https://www.google.com/maps/search/?api=1&query=Haralur"
    raw = f"Property location {raw_url}"
    text = build_whatsapp_group_description(_row(), raw, maps_verified=False, issues=issues)
    assert raw_url in text
    assert "*📍 Landmark:*" in text
    assert "Location: *Haralur*" not in text
    assert "Private Society Name" not in text
    assert any("unverified fallback" in issue for issue in issues)


def test_group_raw_maps_fallback_does_not_require_unverified_locality():
    issues = []
    raw_url = "https://maps.app.goo.gl/AbCdEf123"
    row = _row(locality="")
    text = build_whatsapp_group_description(
        row, f"Property location {raw_url}", maps_verified=False, issues=issues
    )
    assert text.startswith("*👉Semi Furnished 2 BHK with 2 Bathrooms & 1 Balcony*")
    assert raw_url in text
    assert "Location:" not in text
    assert "*📍 Landmark:*" in text
    assert any("unverified fallback" in issue for issue in issues)


def test_group_gated_title_includes_supplied_bathroom_and_balcony_details():
    row = _row(
        furnish_type="Semi Furnished",
        BHK="3 BHK",
        internal_property_type="Gated Community",
        bathrooms=2,
        balconies=1,
    )
    raw = "2 bathrooms and 1 balcony. Pets allowed. https://maps.app.goo.gl/AbCdEf123"
    text = build_whatsapp_group_description(
        row, raw, verified_society_name="Sumo Sonet", maps_verified=True
    )
    assert text.startswith("*👉Semi Furnished 3 BHK with 2 Bathrooms & 1 Balcony*")
    assert "\nPets: Allowed\nGated Community\nLocation:" in text
    assert "*📍 Sumo Sonet:*" in text


def test_group_does_not_infer_attached_bathrooms_or_gated_status():
    row = _row(internal_property_type="Standalone")
    text = build_whatsapp_group_description(row, "2 bathrooms", maps_verified=False)
    assert "attached bathrooms" not in text
    assert "Gated Community" not in text
    assert "Semi Gated" not in text


def test_facebook_hides_society_and_uses_required_footer():
    text = build_facebook_marketplace_description(
        _row(), "Large balcony. Pets allowed. Available from: Immediately."
    )
    assert text.startswith("🏡 Semi Furnished 2 BHK with large balcony | Haralur")
    assert "Private Society Name" not in text
    assert "Rent: ₹45,000 + Maintenance" in text
    assert "Ready to Occupy" in text
    assert "Pet Friendly" in text
    assert "https://chat.whatsapp.com/FxOPO0xAOsD6lNwPcIDdFM" in text
    assert text.endswith("☎️ 91483 38801\nBrokerage applicable.")


def test_facebook_omits_unconfirmed_tenant_and_pet_lines():
    text = build_facebook_marketplace_description(
        _row(preferred_tenant_type="Family Only"), "No pet policy supplied."
    )
    assert "Family Only" not in text
    assert "Pet Friendly" not in text
