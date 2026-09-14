from __future__ import annotations

import pytest

from . import schema
from .client import GoogleSheetsClient, GoogleSheetsCredentials, MissingGoogleSheetsCredentials


def test_missing_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
    monkeypatch.delenv("GOOGLE_SERVICE_ACCOUNT_JSON", raising=False)
    monkeypatch.setattr("shared.google_sheets.client._secret_from_keychain", lambda: None)
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
    assert client.read_range("sheet", "tab", "A1:B2") == [["A1:B2"]]
    assert client.write_row("sheet", "tab", 2, row) == {"ok": True}
    assert fake.ws.updated == ("A2:AV2", [row], True)
    assert client.append_rows("sheet", "tab", [row]) == {
        "values": [row],
        "value_input_option": "RAW",
    }
    with pytest.raises(ValueError):
        client.write_row("sheet", "tab", 2, ["short"])
