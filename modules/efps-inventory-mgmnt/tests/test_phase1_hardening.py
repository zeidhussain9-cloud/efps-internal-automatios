from __future__ import annotations

from src import phase1
from src.pipeline import initial_row, deterministic
from src import validate
from shared.google_sheets import schema
from shared.google_sheets.client import GoogleSheetsClient, GoogleSheetsCredentials


def test_direct_property_type_wins_over_generic_wording():
    out = deterministic("Property Type: Semi Gated\nNote: gated community wording appears later\nRent: 40000")
    assert out["internal_property_type"] == "Semi Gated"


def test_missing_property_type_remains_unresolved():
    out = deterministic("2 BHK\nRent: 40000\nLocation: Harlur")
    assert out["internal_property_type"] == ""


def test_registry_is_consulted_without_fabricating_standalone():
    registry = deterministic("2 BHK\nRent: 40000\nSociety: Prima Hi-Life")
    unknown = deterministic("2 BHK\nRent: 40000\nSociety: Unknown Heights")
    assert registry["internal_property_type"] == "Gated Community"
    assert unknown["internal_property_type"] == ""


def test_coupled_property_type_parking_amenities_state():
    gated = deterministic("2 BHK\nRent: 40000\nProperty Type: Gated Community")
    semi = deterministic("2 BHK\nRent: 40000\nProperty Type: Semi Gated")
    standalone = deterministic("2 BHK\nRent: 40000\nProperty Type: Standalone")
    assert gated["covered_parking"] == "1"
    assert gated["open_parking"] == "-"
    assert gated["society_amenities"] == phase1.GATED_AMENITIES
    assert semi["covered_parking"] == "1"
    assert semi["open_parking"] == "-"
    assert semi["society_amenities"] == phase1.SEMI_GATED_AMENITIES
    assert standalone["covered_parking"] == ""
    assert standalone["open_parking"] == "-"
    assert standalone["society_amenities"] == "-"


def test_explicit_parking_counts_are_preserved():
    out = deterministic("2 BHK\nRent: 40000\nProperty Type: Gated Community\n2 covered parking")
    assert out["covered_parking"] == "2"


def test_landmark_uses_locality_final_fallback_and_never_maps_url():
    fallback = deterministic("2 BHK\nRent: 40000\nLocation: Harlur")
    maps_landmark = deterministic("2 BHK\nRent: 40000\nLocation: Harlur\nLandmark: https://maps.app.goo.gl/example")
    assert fallback["landmark"] == "Harlur"
    assert maps_landmark["landmark"] == "Harlur"
    assert maps_landmark["google_maps_url"] == "https://maps.app.goo.gl/example"


def test_society_fallback_is_reported_for_later_review():
    result = phase1.run_phase1("2 BHK\nRent: 40000\nProperty Type: Gated Community\nLocation: Harlur")
    assert result.row["society_name"] == "Harlur"
    assert "society_name_locality_fallback" in result.report["review_flags"]


def test_maps_url_extraction_is_deterministic_and_does_not_resolve_network():
    result = phase1.run_phase1(
        "2 BHK\nRent: 40000\nProperty Type: Gated Community\nLocation: Harlur\n"
        "https://share.google/AbC123"
    )
    assert result.row["google_maps_url"] == "https://share.google/AbC123"
    assert "google_maps_url" in result.report["trace"]["resolved"]


def test_phase1_status_transition_happens_at_boundary():
    row = initial_row("EF-TEST-PHASE1")
    result = phase1.run_phase1("2 BHK\nRent: 40000\nProperty Type: Gated Community\nLocation: Harlur", row=row)
    assert result.row["intake_status"] == "Processed"
    assert result.row["status"] == "Pending"


def test_phase1_invalid_canonical_type_fails_closed():
    row = initial_row("EF-TEST-PHASE1-INVALID")
    row["internal_property_type"] = "Something Else"
    out = deterministic("2 BHK\nRent: 40000\nLocation: Harlur", row=row)
    assert out["internal_property_type"] == ""
    phase = phase1.run_phase1("2 BHK\nRent: 40000\nLocation: Harlur", row=row)
    assert phase.row["status"] == "Needs Review"
    assert any("internal_property_type" in error for error in phase.issues)


def test_open_parking_dash_is_valid_contract_value():
    row = initial_row("EF-TEST-PARKING")
    row.update({
        "status": "Pending",
        "intake_status": "Processed",
        "monthly_rent": "40000",
        "internal_property_type": "Standalone",
        "open_parking": "-",
        "society_amenities": "-",
    })
    errors = validate.validate(row)
    assert not any("open_parking" in error for error in errors)


def test_github_sheets_client_reuses_spreadsheet_and_worksheet():
    class FakeWorksheet:
        def get(self, range_name):
            return [["ok"]]

        def batch_update(self, payload):
            return payload

    class FakeSpreadsheet:
        def __init__(self):
            self.calls = 0
            self.worksheet_obj = FakeWorksheet()

        def worksheet(self, name):
            self.calls += 1
            return self.worksheet_obj

    class FakeClient:
        def __init__(self, spreadsheet):
            self.spreadsheet = spreadsheet
            self.opens = 0

        def open_by_key(self, key):
            self.opens += 1
            return self.spreadsheet

    spreadsheet = FakeSpreadsheet()
    low = FakeClient(spreadsheet)
    client = GoogleSheetsClient(
        credentials=GoogleSheetsCredentials({"private_key": "test"}),
        client=low,
        max_retries=0,
    )
    client.read_range("sheet", "Housing_Listings", "A1:A1")
    client.write_ranges("sheet", "Housing_Listings", [("A1:A1", [["ok"]])])
    assert low.opens == 1
    assert spreadsheet.calls == 1


def test_phase1_report_exposes_populated_blank_unresolved_and_trace():
    result = phase1.run_phase1("2 BHK\nRent: 40000\nProperty Type: Gated Community\nLocation: Harlur")
    report = result.report
    assert "monthly_rent" in report["populated_fields"]
    assert "age_of_property_years" in report["blank_fields"]
    assert "source_segments" in report["trace"]
    assert "extracted_candidates" in report["trace"]


def test_phase1_output_is_exactly_48_fields():
    result = phase1.run_phase1("2 BHK\nRent: 40000\nProperty Type: Gated Community\nLocation: Harlur")
    assert tuple(result.row.keys()) == schema.NAMES
