"""WhAPI transport wrapper with explicit live-traffic safety controls."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Mapping
from urllib import error, parse, request

from . import config


class MissingWhApiCredentials(RuntimeError):
    """Raised when the WhAPI token is unavailable."""


class WhApiLiveTrafficBlocked(RuntimeError):
    """Raised when a live network operation is attempted without approval."""


def _secret_from_keychain() -> dict[str, Any] | None:
    """Read the canonical local Keychain secret without logging its value."""
    from shared.credentials import get_secret

    try:
        raw = get_secret(config.SECRET_NAME)
    except Exception:
        return None

    if not raw:
        return None

    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return {"value": raw}

    return value if isinstance(value, dict) else {"value": value}


def _resolve_token() -> str:
    """Resolve the canonical local Keychain secret without logging the value."""
    secret = _secret_from_keychain()
    if secret:
        for key in ("api_token", "token", "value", config.TOKEN_ENV):
            if secret.get(key):
                return str(secret[key]).strip()
    token = os.environ.get(config.TOKEN_ENV, "").strip()
    if token:
        return token
    raise MissingWhApiCredentials(
        f"No WhAPI token. Expected local Keychain secret '{config.SECRET_NAME}' "
        f"or environment variable {config.TOKEN_ENV}."
    )


@dataclass(frozen=True)
class WhApiCredentials:
    token: str

    @classmethod
    def from_environment(cls) -> "WhApiCredentials":
        return cls(token=_resolve_token())


class WhApiClient:
    """Small dependency-injected WhAPI HTTP client.

    The shared client provides transport/authentication and neutral endpoint
    primitives only. Modules own all inventory/lead business decisions.
    Every live network request passes the explicit EFPS_WHAPI_LIVE=1 gate.
    """

    LIVE_FLAG = config.LIVE_FLAG
    DEFAULT_BASE_URL = config.BASE_URL

    def __init__(
        self,
        credentials: WhApiCredentials | None = None,
        *,
        base_url: str | None = None,
        transport: Any | None = None,
    ) -> None:
        self.credentials = credentials or WhApiCredentials.from_environment()
        self.base_url = (
            base_url or os.environ.get("WHAPI_BASE_URL") or self.DEFAULT_BASE_URL
        ).rstrip("/")
        self._transport = transport

    def live_enabled(self) -> bool:
        return os.environ.get(self.LIVE_FLAG) == "1"

    def assert_live_allowed(self, operation: str) -> None:
        if not self.live_enabled():
            raise WhApiLiveTrafficBlocked(
                f"BLOCKED: attempted whapi.cloud call ({operation}). "
                f"Set {self.LIVE_FLAG}=1 explicitly for the approved run."
            )

    def _request(
        self, method: str, path: str, payload: Mapping[str, Any] | None = None
    ) -> Any:
        self.assert_live_allowed(f"{method} {path}")
        url = f"{self.base_url}/{path.lstrip('/')}"
        body = None
        headers = {
            "Authorization": f"Bearer {self.credentials.token}",
            "Accept": "application/json",
            "User-Agent": "node-fetch/1.0",
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

    def patch(self, path: str, payload: Mapping[str, Any]) -> Any:
        return self._request("PATCH", path, payload)

    # Neutral, currently documented endpoint primitives. These methods contain
    # no EFPS business routing or persistence logic.
    def health(self) -> Any:
        return self.get("/health")

    def settings(self) -> Any:
        return self.get("/settings")

    def allowed_webhook_events(self) -> Any:
        return self.get("/settings/events")

    def test_webhook(self, payload: Mapping[str, Any]) -> Any:
        return self.post("/settings/webhook_test", payload)

    def send_text(self, payload: Mapping[str, Any]) -> Any:
        return self.post("/messages/text", payload)

    def create_product(
        self,
        name: str,
        description: str,
        price: float,
        currency: str,
        images: list[str],
        url: str = "",
        product_retailer_id: str = "",
        is_hidden: bool = False,
        availability: str = "in stock",
    ) -> Any:
        payload = {
            "name": name,
            "description": description,
            "price": price,
            "currency": currency,
            "images": images,
        }
        if url:
            payload["url"] = url
        if product_retailer_id:
            payload["product_retailer_id"] = product_retailer_id
        payload["is_hidden"] = is_hidden
        payload["availability"] = availability
        return self.post("/business/products", payload)

    def get_products(self, count: int = 100) -> list[dict]:
        all_products: list[dict] = []
        params: dict[str, Any] = {"count": min(count, 100)}
        while True:
            result = self.get("/business/products", params)
            page = (result or {}).get("products", [])
            all_products.extend(page)
            if len(all_products) >= count or len(page) < params["count"]:
                break
            cursor = (result or {}).get("paging", {}).get("cursors", {}).get("after")
            if not cursor:
                break
            params["after"] = cursor
        return all_products

    def find_product_by_retailer_id(self, retailer_id: str) -> dict | None:
        for p in self.get_products(count=10000):
            if p.get("product_retailer_id") == retailer_id:
                return p
        return None

    def find_products_by_image_url(self, image_urls: list[str]) -> list[dict]:
        url_set = set(image_urls)
        matches = []
        for p in self.get_products(count=10000):
            p_images = [str(img.get("link") or img) for img in (p.get("images") or [])]
            if url_set & set(p_images):
                matches.append(p)
        return matches

    def get_collections(self) -> list[dict]:
        result = self.get("/business/collections")
        return (result or {}).get("collections", [])

    def edit_collection(
        self,
        collection_id: str,
        *,
        add_products: list[str] | None = None,
        remove_products: list[str] | None = None,
    ) -> dict:
        payload: dict[str, Any] = {}
        if add_products:
            payload["add_products"] = add_products
        if remove_products:
            payload["remove_products"] = remove_products
        return self.patch(f"/business/collections/{collection_id}", payload)
