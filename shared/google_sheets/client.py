"""Google Sheets transport wrapper with verified EFPS credential resolution."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import schema

SECRET_NAME = "efps-whapi-panel-sheet"


class MissingGoogleSheetsCredentials(RuntimeError):
    """Raised when Google Sheets runtime credentials are unavailable."""


def _secret_from_aws() -> dict[str, Any] | None:
    try:
        import boto3
        client = boto3.client("secretsmanager", region_name=os.environ.get("AWS_REGION", "us-east-1"))
        raw = client.get_secret_value(SecretId=SECRET_NAME).get("SecretString", "")
    except Exception:
        return None
    if not raw:
        return None
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return {"value": raw}
    return value if isinstance(value, dict) else {"value": value}


@dataclass(frozen=True)
class GoogleSheetsCredentials:
    service_account_info: dict[str, Any]

    @classmethod
    def from_environment(cls) -> "GoogleSheetsCredentials":
        credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
        if credentials_path:
            path = Path(credentials_path)
            if path.exists():
                try:
                    return cls(json.loads(path.read_text()))
                except (OSError, json.JSONDecodeError) as exc:
                    raise MissingGoogleSheetsCredentials(
                        "GOOGLE_APPLICATION_CREDENTIALS could not be read as valid JSON."
                    ) from exc

        raw_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
        if raw_json:
            try:
                return cls(json.loads(raw_json))
            except json.JSONDecodeError as exc:
                raise MissingGoogleSheetsCredentials(
                    "GOOGLE_SERVICE_ACCOUNT_JSON is not valid JSON."
                ) from exc

        secret = _secret_from_aws()
        if secret:
            raw = secret.get("GOOGLE_SERVICE_ACCOUNT_JSON", secret.get("value", secret))
            if isinstance(raw, str):
                try:
                    raw = json.loads(raw)
                except json.JSONDecodeError as exc:
                    raise MissingGoogleSheetsCredentials(
                        f"AWS secret '{SECRET_NAME}' does not contain valid service-account JSON."
                    ) from exc
            if isinstance(raw, dict) and raw.get("private_key"):
                return cls(raw)

        raise MissingGoogleSheetsCredentials(
            f"No Google service-account credential. Expected AWS secret '{SECRET_NAME}', "
            "GOOGLE_SERVICE_ACCOUNT_JSON, or GOOGLE_APPLICATION_CREDENTIALS."
        )


class GoogleSheetsClient:
    """Small dependency-injected wrapper around gspread.

    Technical access is separated from business workflow. Full-row operations
    enforce the canonical Housing_Listings contract; modules decide what rows
    mean and when to write them.
    """

    def __init__(self, credentials: GoogleSheetsCredentials | None = None, *, client: Any | None = None) -> None:
        self.credentials = credentials or GoogleSheetsCredentials.from_environment()
        self._client = client

    def _default_client(self) -> Any:
        try:
            import gspread
            from google.oauth2.service_account import Credentials
        except ImportError as exc:
            raise RuntimeError("Install gspread and google-auth to use the live Google Sheets client.") from exc
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.readonly",
        ]
        credentials = Credentials.from_service_account_info(self.credentials.service_account_info, scopes=scopes)
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

    def read_range(self, spreadsheet_id: str, worksheet_name: str, range_name: str) -> list[list[Any]]:
        if not range_name.strip():
            raise ValueError("range_name must not be empty")
        return self.worksheet(spreadsheet_id, worksheet_name).get(range_name)

    def read_rows(self, spreadsheet_id: str, worksheet_name: str, range_name: str) -> list[tuple[Any, ...]]:
        """Read full contract rows and reject schema-width drift."""
        rows = self.read_range(spreadsheet_id, worksheet_name, range_name)
        return [schema.validate_row(row) for row in rows]

    def write_range(self, spreadsheet_id: str, worksheet_name: str, range_name: str, values: list[list[Any]]) -> Any:
        if not range_name.strip():
            raise ValueError("range_name must not be empty")
        return self.worksheet(spreadsheet_id, worksheet_name).update(range_name, values, raw=True)

    def write_row(self, spreadsheet_id: str, worksheet_name: str, row_number: int, values: list[Any] | tuple[Any, ...]) -> Any:
        if row_number < 1:
            raise ValueError("row_number must be >= 1")
        row = schema.validate_row(values)
        return self.write_range(spreadsheet_id, worksheet_name, schema.full_range(row_number), [list(row)])

    def append_rows(self, spreadsheet_id: str, worksheet_name: str, values: list[list[Any]]) -> Any:
        if not values:
            return None
        rows = [schema.validate_row(row) for row in values]
        return self.worksheet(spreadsheet_id, worksheet_name).append_rows(
            [list(row) for row in rows], value_input_option="RAW"
        )
