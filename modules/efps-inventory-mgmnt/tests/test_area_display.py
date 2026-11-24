from __future__ import annotations

from src import notion_intake as intake
from src import extract

BASE = {"google_maps_url": "https://www.google.com/maps/search/?api=1&query=x", "catalog_title": "Semi Furnished 2 BHK - Haralur",
        "furnish_type": "Semi Furnished", "BHK": "2 BHK", "monthly_rent": "30000", "security_deposit": "60000",
        "floor_number": "2", "total_floors": "4", "preferred_tenant_type": "Open For All", "bachelor_preference": "Open for both",
        "internal_property_type": "Gated Community", "locality": "Haralur", "bathrooms": "2", "society_name": "X Towers"}


def _sqft_line(raw, carpet, built):
    row = dict(BASE, carpet_area=carpet, built_up_area=built, raw_message_text=raw)
    d = intake.build_catalogue_description(row, raw, verified_society_name="X Towers")
    return [l for l in d.split("\n") if "sqft" in l][0]


def test_plain_sqft_shows_the_supplied_figure_not_built_up():
    assert _sqft_line("Sqft: 1200", "1200", "1290").startswith("📐 1200 sqft")


def test_carpet_only_label_shows_carpet():
    assert _sqft_line("Carpet area: 1000", "1000", "1090").startswith("📐 1000 sqft")


def test_built_up_only_label_shows_the_advertised_built_up():
    assert _sqft_line("Built-up area: 1100", "1010", "1100").startswith("📐 1100 sqft")


def test_both_labelled_shows_built_up_as_the_old_display_did():
    assert _sqft_line("Carpet area: 1000\nBuilt-up area: 1250", "1000", "1250").startswith("📐 1250 sqft")


def test_whatsapp_post_uses_the_same_figure():
    row = dict(BASE, carpet_area="1010", built_up_area="1100")
    post = intake.build_whatsapp_post(row, "Built-up area: 1100", maps_verified=True, verified_society_name="X Towers")
    assert "1100 sqft" in post and "1010 sqft" not in post


def test_super_built_up_is_not_read_as_an_area_and_needs_review():
    raw = "Super built-up area: 1500 sqft"
    assert "super built-up" in extract.unsupported_area_note(raw, {})
    assert extract.unsupported_area_note(raw, {"carpet_area": "1000"}) == ""
