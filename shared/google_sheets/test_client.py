from __future__ import annotations

import pytest

from . import schema
from . import client
from .client import GoogleSheetsClient, GoogleSheetsCredentials, MissingGoogleSheetsCredentials


def test_missing_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
    monkeypatch.delenv("GOOGLE_SERVICE_ACCOUNT_JSON", raising=False)
    monkeypatch.setattr(client, "_secret_from_keychain", lambda: None)
    with pytest.raises(MissingGoogleSheetsCredentials):
        GoogleSheetsCredentials.from_environment()


def test_read_write_and_append_contract_rows() -> None:
    class Worksheet:
        def __init__(self) -> None:
            self.updated = None
            self.appended = None

        def get(self, range_name: str):
            return [[range_name]]

        def update(self, range_name: str, values, raw: bool = True):
            self.updated = (range_name, values, raw)
            return {"ok": True}

        def append_rows(self, values, value_input_option: str):
            self.appended = (values, value_input_option)
            return {"values": values, "value_input_option": value_input_option}

    class Spreadsheet:
        def __init__(self, ws):
            self.ws = ws

        def worksheet(self, _name):
            return self.ws

    class FakeClient:
        def __init__(self):
            self.ws = Worksheet()

        def open_by_key(self, _key):
            return Spreadsheet(self.ws)

    fake = FakeClient()
    client = GoogleSheetsClient(
        GoogleSheetsCredentials({"type": "service_account"}),
        client=fake,
    )
    row = [f"v{i}" for i in range(schema.GRID_WIDTH)]
    row[schema.NAMES.index("source_group")] = ""
    row[schema.NAMES.index("inventory_locked")] = ""
    assert client.read_range("sheet", "tab", "A1:B2") == [["A1:B2"]]
    assert client.write_row("sheet", "tab", 2, row) == {"ok": True}
    assert fake.ws.updated == ("A2:AT2", [row[:46]], True)
    assert client.append_rows("sheet", "tab", [row]) == {
        "values": [row[:46]],
        "value_input_option": "RAW",
    }
    reserved_source = list(row)
    reserved_source[schema.NAMES.index("source_group")] = "historical-chat-id"
    with pytest.raises(PermissionError):
        client.write_row("sheet", "tab", 2, reserved_source)
    with pytest.raises(ValueError):
        client.write_row("sheet", "tab", 2, ["short"])


def test_housing_listings_reserved_ranges_are_rejected() -> None:
    client = GoogleSheetsClient(GoogleSheetsCredentials({"type": "service_account"}), client=object())
    with pytest.raises(PermissionError):
        client.read_range(schema.SHEET_ID, schema.WORKSHEET_NAME, "A2:AV")
    with pytest.raises(PermissionError):
        client.read_range(schema.SHEET_ID, schema.WORKSHEET_NAME, "AU2:AU10")
    with pytest.raises(PermissionError):
        client.write_range(schema.SHEET_ID, schema.WORKSHEET_NAME, "AV2", [["Yes"]])
    with pytest.raises(PermissionError):
        client.write_ranges(schema.SHEET_ID, schema.WORKSHEET_NAME, [("AT2:AV2", [["x", "y", "z"]])])
