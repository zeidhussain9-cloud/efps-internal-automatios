"""Google Sheets transport wrapper with caching, batching, and 429 backoff."""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, TypeVar

from . import schema

SECRET_NAME = "efps-whapi-panel-sheet"
T = TypeVar("T")


class MissingGoogleSheetsCredentials(RuntimeError):
    """Raised when Google Sheets runtime credentials are unavailable."""


def _secret_from_keychain() -> dict[str, Any] | None:
    from shared.credentials import get_secret
    try:
        raw = get_secret(SECRET_NAME)
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
                raise MissingGoogleSheetsCredentials("GOOGLE_SERVICE_ACCOUNT_JSON is not valid JSON.") from exc

        secret = _secret_from_keychain()
        if secret:
            raw = secret.get("GOOGLE_SERVICE_ACCOUNT_JSON", secret.get("value", secret))
            if isinstance(raw, str):
                try:
                    raw = json.loads(raw)
                except json.JSONDecodeError as exc:
                    raise MissingGoogleSheetsCredentials(
                        f"Keychain secret '{SECRET_NAME}' does not contain valid service-account JSON."
                    ) from exc
            if isinstance(raw, dict) and raw.get("private_key"):
                return cls(raw)

        raise MissingGoogleSheetsCredentials(
            f"No Google service-account credential. Expected local Keychain secret '{SECRET_NAME}', "
            "GOOGLE_SERVICE_ACCOUNT_JSON, or GOOGLE_APPLICATION_CREDENTIALS."
        )


class GoogleSheetsClient:
    """Dependency-injected gspread wrapper with object reuse and quota-safe writes."""

    def __init__(
        self,
        credentials: GoogleSheetsCredentials | None = None,
        *,
        client: Any | None = None,
        max_retries: int = 5,
        backoff_base_seconds: float = 1.0,
    ) -> None:
        self.credentials = credentials or GoogleSheetsCredentials.from_environment()
        self._client = client
        self._spreadsheet_cache: dict[str, Any] = {}
        self._worksheet_cache: dict[tuple[str, str], Any] = {}
        self.max_retries = max(0, int(max_retries))
        self.backoff_base_seconds = max(0.0, float(backoff_base_seconds))

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
        if spreadsheet_id not in self._spreadsheet_cache:
            self._spreadsheet_cache[spreadsheet_id] = self.client.open_by_key(spreadsheet_id)
        return self._spreadsheet_cache[spreadsheet_id]

    def worksheet(self, spreadsheet_id: str, worksheet_name: str) -> Any:
        if not worksheet_name.strip():
            raise ValueError("worksheet_name must not be empty")
        key = (spreadsheet_id, worksheet_name)
        if key not in self._worksheet_cache:
            self._worksheet_cache[key] = self.open_spreadsheet(spreadsheet_id).worksheet(worksheet_name)
        return self._worksheet_cache[key]

    @staticmethod
    def _is_rate_limited(exc: Exception) -> bool:
        response = getattr(exc, "response", None) or getattr(exc, "resp", None)
        status = getattr(response, "status_code", None) or getattr(response, "status", None)
        if status == 429:
            return True
        text = str(exc).upper()
        return "429" in text or "RESOURCE_EXHAUSTED" in text or "RATE LIMIT" in text

    def _with_backoff(self, operation: Callable[[], T]) -> T:
        attempt = 0
        while True:
            try:
                return operation()
            except Exception as exc:
                if not self._is_rate_limited(exc) or attempt >= self.max_retries:
                    raise
                delay = self.backoff_base_seconds * (2 ** attempt)
                if delay:
                    time.sleep(delay)
                attempt += 1

    def read_range(self, spreadsheet_id: str, worksheet_name: str, range_name: str) -> list[list[Any]]:
        if not range_name.strip():
            raise ValueError("range_name must not be empty")
        return self._with_backoff(lambda: self.worksheet(spreadsheet_id, worksheet_name).get(range_name))

    def read_rows(self, spreadsheet_id: str, worksheet_name: str, range_name: str) -> list[tuple[Any, ...]]:
        rows = self.read_range(spreadsheet_id, worksheet_name, range_name)
        width = schema.GRID_WIDTH - len(schema.RESERVED_COLUMNS)
        normalized = [list(row) + [""] * len(schema.RESERVED_COLUMNS) if len(row) == width else row for row in rows]
        return [schema.validate_row(row) for row in normalized]

    def write_ranges(
        self,
        spreadsheet_id: str,
        worksheet_name: str,
        updates: list[tuple[str, list[list[Any]]]],
    ) -> Any:
        """Write many ranges through one gspread batch_update request."""
        if not updates:
            return None
        payload = [{"range": range_name, "values": values} for range_name, values in updates]
        return self._with_backoff(lambda: self.worksheet(spreadsheet_id, worksheet_name).batch_update(payload))

    def write_range(self, spreadsheet_id: str, worksheet_name: str, range_name: str, values: list[list[Any]]) -> Any:
        if not range_name.strip():
            raise ValueError("range_name must not be empty")
        return self.write_ranges(spreadsheet_id, worksheet_name, [(range_name, values)])

    @staticmethod
    def _writable_canonical_row(values: list[Any] | tuple[Any, ...]) -> list[Any]:
        row = schema.validate_row(values)
        for field in schema.RESERVED_COLUMNS:
            index = schema.NAMES.index(field)
            if str(row[index] or "").strip():
                raise PermissionError(f"reserved column {field} must remain blank")
        return list(row[: schema.GRID_WIDTH - len(schema.RESERVED_COLUMNS)])

    def write_row(self, spreadsheet_id: str, worksheet_name: str, row_number: int, values: list[Any] | tuple[Any, ...]) -> Any:
        if row_number < 1:
            raise ValueError("row_number must be >= 1")
        row = self._writable_canonical_row(values)
        return self.write_range(spreadsheet_id, worksheet_name, f"A{row_number}:AT{row_number}", [row])

    def append_rows(self, spreadsheet_id: str, worksheet_name: str, values: list[list[Any]]) -> Any:
        if not values:
            return None
        rows = [self._writable_canonical_row(row) for row in values]
        return self._with_backoff(
            lambda: self.worksheet(spreadsheet_id, worksheet_name).append_rows(
                rows, value_input_option="RAW"
            )
        )
