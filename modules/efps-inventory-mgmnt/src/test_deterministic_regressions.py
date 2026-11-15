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


def test_partial_maps_requires_review_and_does_not_apply_candidate_location():
    raw = "2 BHK Apartment\nRent: 40000\nCommunity: Gated Community\nLocation: Harlur\nGoogle Maps: https://maps.app.goo.gl/example"

    class PartialMaps:
        def extract_url(self, text):
            return "https://maps.app.goo.gl/example"

        def resolve(self, *, maps_url="", address="", expected_locality=""):
            return MapsResolution(confidence="PARTIAL_MATCH", locality="Unverified Nearby", pincode="999999")

    processed, issues = pipeline.process_closed_session(
        raw,
        row=pipeline.initial_row("EF-TEST-MAPS-PARTIAL"),
        maps_client=PartialMaps(),
        ai_llm=None,
    )
    assert processed["status"] == "Needs Review"
    assert processed["intake_status"] == "Processed"
    assert processed["locality"] == "Harlur"
    assert processed["pincode"] == ""
    assert issues == ["Google Maps verification failed or is incomplete: PARTIAL_MATCH"]


def test_maps_api_unavailable_preserves_source_url_without_needs_review():
    raw = "2 BHK Apartment\nRent: 40000\nCommunity: Gated Community\nLocation: Harlur\nGoogle Maps: https://maps.app.goo.gl/example"

    class UnavailableMaps:
        def resolve(self, *, maps_url="", address="", expected_locality=""):
            return MapsResolution(canonical_url=maps_url, confidence="API_UNAVAILABLE")

    processed, issues = pipeline.process_closed_session(
        raw,
        row=pipeline.initial_row("EF-TEST-MAPS-API-UNAVAILABLE"),
        maps_client=UnavailableMaps(),
        ai_llm=None,
    )
    assert processed["status"] == "Pending"
    assert processed["intake_status"] == "Processed"
    assert processed["google_maps_url"] == "https://maps.app.goo.gl/example"
    assert any(issue.startswith("Background Maps check unavailable") for issue in issues)


def test_maps_missing_runtime_verification_is_treated_as_optional_enrichment():
    raw = "2 BHK Apartment\nRent: 40000\nCommunity: Gated Community\nLocation: Harlur\nGoogle Maps: https://maps.app.goo.gl/example"

    class MissingKeyMaps:
        def resolve(self, *, maps_url="", address="", expected_locality=""):
            return MapsResolution(canonical_url=maps_url, confidence="NEEDS_RUNTIME_VERIFICATION")

    processed, issues = pipeline.process_closed_session(
        raw,
        row=pipeline.initial_row("EF-TEST-MAPS-MISSING-KEY"),
        maps_client=MissingKeyMaps(),
        ai_llm=None,
    )
    assert processed["status"] == "Pending"
    assert processed["google_maps_url"] == "https://maps.app.goo.gl/example"
    assert any(issue.startswith("Background Maps check unavailable") for issue in issues)


def test_maps_transport_exception_does_not_block_intake_or_drop_source_url():
    raw = "2 BHK Apartment\nRent: 40000\nCommunity: Gated Community\nLocation: Harlur\nGoogle Maps: https://maps.app.goo.gl/example"

    class OfflineMaps:
        def resolve(self, *, maps_url="", address="", expected_locality=""):
            raise TimeoutError("Google Maps request timed out")

    processed, issues = pipeline.process_closed_session(
        raw,
        row=pipeline.initial_row("EF-TEST-MAPS-OFFLINE"),
        maps_client=OfflineMaps(),
        ai_llm=None,
    )
    assert processed["status"] == "Pending"
    assert processed["google_maps_url"] == "https://maps.app.goo.gl/example"
    assert any(issue.startswith("Background Maps check unavailable") for issue in issues)
