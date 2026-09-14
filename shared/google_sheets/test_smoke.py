from __future__ import annotations

from shared.google_sheets.client import GoogleSheetsClient, GoogleSheetsCredentials


def test_google_sheets_client_constructs_with_injected_client() -> None:
    fake = object()
    client = GoogleSheetsClient(GoogleSheetsCredentials({"type": "service_account"}), client=fake)
    assert client.client is fake
