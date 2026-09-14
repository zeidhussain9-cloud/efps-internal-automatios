"""WhAPI transport wrapper with an explicit live-traffic safety gate."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Mapping
from urllib import error, parse, request


class MissingWhApiCredentials(RuntimeError):
    """Raised when the WhAPI token is unavailable."""


class WhApiLiveTrafficBlocked(RuntimeError):
    """Raised when a live network operation is attempted without approval."""


@dataclass(frozen=True)
class WhApiCredentials:
    token: str

    @classmethod
    def from_environment(cls) -> "WhApiCredentials":
        token = os.environ.get("WHAPI_API_TOKEN", "").strip()
        if not token:
            raise MissingWhApiCredentials("WHAPI_API_TOKEN is not set.")
        return cls(token=token)


class WhApiClient:
    """Minimal dependency-free WhAPI HTTP client.

    Every network operation checks the explicit live gate first. The gate is
    intentionally environment-controlled and is never enabled by code.
    """

    LIVE_FLAG = "EFPS_WHAPI_LIVE"
    DEFAULT_BASE_URL = "https://gate.whapi.cloud"

    def __init__(
        self,
        credentials: WhApiCredentials | None = None,
        *,
        base_url: str | None = None,
        transport: Any | None = None,
    ) -> None:
        self.credentials = credentials or WhApiCredentials.from_environment()
        self.base_url = (base_url or os.environ.get("WHAPI_BASE_URL") or self.DEFAULT_BASE_URL).rstrip("/")
        self._transport = transport

    def live_enabled(self) -> bool:
        return os.environ.get(self.LIVE_FLAG) == "1"

    def assert_live_allowed(self, operation: str) -> None:
        if not self.live_enabled():
            raise WhApiLiveTrafficBlocked(
                f"BLOCKED: attempted whapi.cloud call ({operation}). "
                f"Set {self.LIVE_FLAG}=1 explicitly for the approved run."
            )

    def _request(self, method: str, path: str, payload: Mapping[str, Any] | None = None) -> Any:
        self.assert_live_allowed(f"{method} {path}")
        url = f"{self.base_url}/{path.lstrip('/')}"
        body = None
        headers = {
            "Authorization": f"Bearer {self.credentials.token}",
            "Accept": "application/json",
        }
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = request.Request(url, data=body, headers=headers, method=method.upper())
        if self._transport is not None:
            return self._transport(req)

        try:
            with request.urlopen(req, timeout=30) as response:
                raw = response.read().decode("utf-8")
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"WhAPI HTTP {exc.code}: {detail}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"WhAPI network error: {exc}") from exc

        if not raw:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw

    def get(self, path: str, query: Mapping[str, Any] | None = None) -> Any:
        if query:
            path = f"{path}?{parse.urlencode(query, doseq=True)}"
        return self._request("GET", path)

    def post(self, path: str, payload: Mapping[str, Any]) -> Any:
        return self._request("POST", path, payload)
