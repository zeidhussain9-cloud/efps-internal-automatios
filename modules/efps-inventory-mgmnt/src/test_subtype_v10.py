from __future__ import annotations

import pytest

from . import pipeline
from shared.google_sheets import schema

AUTHORIZED = (
    "Apartment",
    "Villa",
    "Independent House",
    "Duplex",
    "Studio",
    "Independent Floor",
)


@pytest.mark.parametrize(
    ("wording", "expected"),
    [
        ("2 BHK apartment for rent", "Apartment"),
        ("3 BHK villa for rent", "Villa"),
        ("Independent House for rent", "Independent House"),
        ("Duplex for rent", "Duplex"),
        ("Studio for rent", "Studio"),
        ("1 RK for rent", "Studio"),
        ("Independent Floor for rent", "Independent Floor"),
    ],
)
def test_v10_authorized_subtype_wording_resolves_exactly(wording: str, expected: str):
    row = pipeline.deterministic(f"{wording}\nRent: 40000", pipeline.initial_row("EF-V10-0001"))
    assert row["property_subtype"] == expected
    assert row["property_subtype"] in AUTHORIZED
    assert row["property_subtype"] in schema.BY_NAME["property_subtype"].allowed_values


@pytest.mark.parametrize("wording", ["Penthouse for rent", "Farm House for rent"])
def test_unsupported_v10_subtype_is_unresolved_and_needs_review(wording: str):
    raw = f"{wording}\nRent: 40000"
    row = pipeline.deterministic(raw, pipeline.initial_row("EF-V10-0002"))
    assert row["property_subtype"] == ""
    processed = pipeline.process_phase1(raw, row=pipeline.initial_row("EF-V10-0003"))
    assert processed.row["property_subtype"] == ""
    assert processed.row["status"] == "Needs Review"
    assert "property_subtype unresolved" in processed.issues


def test_conflicting_specific_subtypes_are_unresolved_and_need_review():
    raw = "Apartment and Villa for rent\nRent: 40000"
    row = pipeline.deterministic(raw, pipeline.initial_row("EF-V10-0004"))
    assert row["property_subtype"] == ""
    processed = pipeline.process_phase1(raw, row=pipeline.initial_row("EF-V10-0005"))
    assert processed.row["property_subtype"] == ""
    assert processed.row["status"] == "Needs Review"


def test_non_authorizing_fields_do_not_determine_subtype():
    raw = """3 BHK
5th floor out of 10
Fully Furnished
2 covered parking
Club House, Lift, Gym
Rent: 60000
Gated Community
"""
    row = pipeline.deterministic(raw, pipeline.initial_row("EF-V10-0006"))
    assert row["property_subtype"] == "Apartment"


def test_v10_six_value_schema_has_no_legacy_extra_subtypes():
    assert schema.BY_NAME["property_subtype"].allowed_values == AUTHORIZED
    assert "Penthouse" not in schema.BY_NAME["property_subtype"].allowed_values
    assert "Farm House" not in schema.BY_NAME["property_subtype"].allowed_values
