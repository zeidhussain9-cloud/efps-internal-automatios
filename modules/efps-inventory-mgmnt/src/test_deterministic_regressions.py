from __future__ import annotations

from . import pipeline
from shared.google_maps.client import MapsResolution


def test_direct_fields_accept_dash_separator_and_clean_markdown():
    raw = """2 BHK
Rent - 40000
Internal Property Type - Semi Gated
Society Name - *Green View*
Landmark - *Harlur Main Road*
Location - *Harlur*"""
    row = pipeline.deterministic(raw, pipeline.initial_row("EF-TEST-DIRECT-003"))
    assert row["internal_property_type"] == "Semi Gated"
    assert row["society_name"] == "Green View"
    assert row["landmark"] == "Harlur Main Road"
    assert row["locality"] == "Harlur"
    assert row["covered_parking"] == "1"
    assert row["society_amenities"] == "Security, Lift, CCTV, Power Backup"


def test_placeholder_society_and_landmark_use_location():
    raw = "2 BHK\nRent: 40000\nLocation: Harlur\nSociety Name: *\nLandmark: -"
    row = pipeline.deterministic(raw, pipeline.initial_row("EF-TEST-DIRECT-004"))
    assert row["society_name"] == "Harlur"
    assert row["landmark"] == "Harlur"


def test_partial_maps_does_not_create_needs_review():
    raw = "2 BHK\nRent: 40000\nLocation: Harlur\nGoogle Maps: https://maps.app.goo.gl/example"

    class PartialMaps:
        def extract_url(self, text):
            return "https://maps.app.goo.gl/example"

        def resolve(self, *, maps_url="", address=""):
            return MapsResolution(confidence="PARTIAL_MATCH")

    processed, issues = pipeline.process_closed_session(
        raw,
        row=pipeline.initial_row("EF-TEST-MAPS-PARTIAL"),
        maps_client=PartialMaps(),
        ai_llm=None,
    )
    assert processed["status"] == "Pending"
    assert processed["intake_status"] == "Processed"
    assert issues == ["Google Maps verification failed or is incomplete: PARTIAL_MATCH"]
