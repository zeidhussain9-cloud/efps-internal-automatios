"""Locality normalization: raw Location text maps to the closest dropdown option."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from location_match import normalize_locality  # noqa: E402
from shared.ola_maps import OlaGeocodeResult  # noqa: E402

OPTIONS = ["Haralur", "HSR Layout", "Koramangala", "Electronic City", "Bellandur"]


class StubOla:
    def __init__(self, result):
        self.result = result
        self.queries = []

    def geocode(self, text):
        self.queries.append(text)
        return self.result


def test_exact_option_is_used_verbatim():
    result = normalize_locality("Haralur", OPTIONS, ola_client=None)
    assert result.canonical == "Haralur"
    assert result.source == "exact"
    assert result.note == ""


def test_case_difference_normalizes_to_canonical_spelling():
    result = normalize_locality("haralur", OPTIONS, ola_client=None)
    assert result.canonical == "Haralur"
    assert result.source == "exact"


def test_spelling_variant_maps_to_closest_option():
    result = normalize_locality("Harlur", OPTIONS, ola_client=None)
    assert result.canonical == "Haralur"
    assert result.source == "similarity"
    assert "Harlur" in result.note and "Haralur" in result.note


def test_ola_maps_resolves_layout_name_to_listed_locality():
    stub = StubOla(
        OlaGeocodeResult(
            formatted_address="Shubh Enclave, Haralur Road, Bengaluru, Karnataka 560102",
            candidates=("Haralur", "Haralur Road"),
            confidence="OK",
        )
    )
    result = normalize_locality("Shubh Enclave", OPTIONS, ola_client=stub)
    assert result.canonical == "Haralur"
    assert result.source == "ola_maps"
    assert "Shubh Enclave" in result.note and "Haralur" in result.note
    assert stub.queries == ["Shubh Enclave, Bengaluru"]


def test_ola_second_query_uses_landmark_context():
    stub = StubOla(OlaGeocodeResult(confidence="ZERO_RESULTS"))
    result = normalize_locality(
        "Shubh Enclave",
        OPTIONS,
        ola_client=stub,
        context=("Shubh Enclave Layout, Haralur Road", ""),
    )
    assert result.canonical == ""
    assert stub.queries == [
        "Shubh Enclave, Bengaluru",
        "Shubh Enclave Layout, Haralur Road, Shubh Enclave, Bengaluru",
    ]


def test_no_match_returns_empty_and_never_invents_a_locality():
    stub = StubOla(OlaGeocodeResult(confidence="ZERO_RESULTS"))
    result = normalize_locality("Timbuktu", OPTIONS, ola_client=stub)
    assert result.canonical == ""
    assert result.source == ""


def test_ola_unavailable_falls_back_to_no_match():
    stub = StubOla(OlaGeocodeResult(confidence="API_UNAVAILABLE"))
    result = normalize_locality("Shubh Enclave", OPTIONS, ola_client=stub)
    assert result.canonical == ""


def test_missing_key_never_raises():
    stub = StubOla(OlaGeocodeResult(confidence="NO_KEY"))
    result = normalize_locality("Shubh Enclave", OPTIONS, ola_client=stub)
    assert result.canonical == ""


def test_ola_exception_is_contained():
    class ExplodingOla:
        def geocode(self, text):
            raise RuntimeError("network down")

    result = normalize_locality("Shubh Enclave", OPTIONS, ola_client=ExplodingOla())
    assert result.canonical == ""


def test_empty_inputs_are_noop():
    assert normalize_locality("", OPTIONS, ola_client=None).canonical == ""
    assert normalize_locality("Haralur", [], ola_client=None).canonical == ""
