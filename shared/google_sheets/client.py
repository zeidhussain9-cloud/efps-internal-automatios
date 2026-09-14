"""Google Sheets transport wrapper.

Business meaning and spreadsheet ownership remain with calling modules.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class MissingGoogleSheetsCredentials(RuntimeError):
    """Raised when Google Sheets runtime credentials are unavailable."""


@dataclass(frozen=True)
class GoogleSheetsCredentials:
    service_account_info: dict[str, Any]

    @classmethod
    def from_environment(cls) -> "GoogleSheetsCredentials":
        raw_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
        credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "").strip()

        if raw_json:
            try:
                return cls(json.loads(raw_json))
            except json.JSONDecodeError as exc:
                raise MissingGoogleSheetsCredentials(
                    "GOOGLE_SERVICE_ACCOUNT_JSON is not valid JSON."
                ) from exc

        if credentials_path:
            path = Path(credentials_path)
            if path.exists():
                try:
                    return cls(json.loads(path.read_text()))
                except (OSError, json.JSONDecodeError) as exc:
                    raise MissingGoogleSheetsCredentials(
                        "GOOGLE_APPLICATION_CREDENTIALS could not be read as valid JSON."
                    ) from exc

        raise MissingGoogleSheetsCredentials(
            "Set GOOGLE_SERVICE_ACCOUNT_JSON or GOOGLE_APPLICATION_CREDENTIALS at runtime."
        )


class GoogleSheetsClient:
    """Small dependency-injected wrapper around gspread."""

    def __init__(
        self,
        credentials: GoogleSheetsCredentials | None = None,
        *,
        client: Any | None = None,
    ) -> None:
        self.credentials = credentials or GoogleSheetsCredentials.from_environment()
        self._client = client

    def _default_client(self) -> Any:
        try:
            import gspread
            from google.oauth2.service_account import Credentials
        except ImportError as exc:
            raise RuntimeError(
                "Install gspread and google-auth to use the live Google Sheets client."
            ) from exc

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.readonly",
        ]
        credentials = Credentials.from_service_account_info(
            self.credentials.service_account_info,
            scopes=scopes,
        )
        return gspread.authorize(credentials)

    @property
    def client(self) -> Any:
        if self._client is None:
            self._client = self._default_client()
        return self._client

    def open_spreadsheet(self, spreadsheet_id: str) -> Any:
        if not spreadsheet_id.strip():
            raise ValueError("spreadsheet_id must not be empty")
        return self.client.open_by_key(spreadsheet_id)

    def worksheet(self, spreadsheet_id: str, worksheet_name: str) -> Any:
        if not worksheet_name.strip():
            raise ValueError("worksheet_name must not be empty")
        return self.open_spreadsheet(spreadsheet_id).worksheet(worksheet_name)

    def read_range(
        self,
        spreadsheet_id: str,
        worksheet_name: str,
        range_name: str,
    ) -> list[list[Any]]:
        if not range_name.strip():
            raise ValueError("range_name must not be empty")
        return self.worksheet(spreadsheet_id, worksheet_name).get(range_name)

    def write_range(
        self,
        spreadsheet_id: str,
        worksheet_name: str,
        range_name: str,
        values: list[list[Any]],
    ) -> Any:
        if not range_name.strip():
            raise ValueError("range_name must not be empty")
        return self.worksheet(spreadsheet_id, worksheet_name).update(
            range_name,
            values,
            raw=True,
        )

    def append_rows(
        self,
        spreadsheet_id: str,
        worksheet_name: str,
        values: list[list[Any]],
    ) -> Any:
        if not values:
            return None
        return self.worksheet(spreadsheet_id, worksheet_name).append_rows(
            values,
            value_input_option="RAW",
        )
