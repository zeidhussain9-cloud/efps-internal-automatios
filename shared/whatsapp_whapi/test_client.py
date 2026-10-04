from __future__ import annotations

import pytest

from .client import WhApiClient, WhApiCredentials, WhApiLiveTrafficBlocked


def test_api_is_disabled_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("EFPS_WHAPI_API_ENABLED", raising=False)
    monkeypatch.setenv("EFPS_WHAPI_LIVE", "1")
    client = WhApiClient(WhApiCredentials("test-token"), base_url="https://example.test")
    with pytest.raises(WhApiLiveTrafficBlocked, match="outside the catalog-creation allowlist"):
        client.get("groups")


def test_non_catalog_whapi_operations_are_always_blocked(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EFPS_WHAPI_API_ENABLED", "true")
    monkeypatch.setenv("EFPS_WHAPI_LIVE", "1")
    client = WhApiClient(WhApiCredentials("test-token"), base_url="https://example.test")
    with pytest.raises(WhApiLiveTrafficBlocked, match="outside the catalog-creation allowlist"):
        client.get("/business/products")
    with pytest.raises(WhApiLiveTrafficBlocked, match="outside the catalog-creation allowlist"):
        client.edit_collection("c1", add_products=["p1"])
    with pytest.raises(WhApiLiveTrafficBlocked, match="outside the catalog-creation allowlist"):
        client.send_text({"to": "919999999999", "body": "test"})


def test_catalog_creation_requires_both_explicit_flags(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EFPS_WHAPI_LIVE", "1")
    monkeypatch.setenv("EFPS_WHAPI_API_ENABLED", "true")
    monkeypatch.delenv("EFPS_WHAPI_CATALOG_WRITE_ENABLED", raising=False)
    client = WhApiClient(WhApiCredentials("t"), base_url="https://e.test", transport=lambda req: {"id": "p1"})
    with pytest.raises(WhApiLiveTrafficBlocked, match="non-approved WhAPI operation"):
        client.create_product("x", "d", 1, "INR", [])
    monkeypatch.setenv("EFPS_WHAPI_CATALOG_WRITE_ENABLED", "true")
    assert client.create_product("x", "d", 1, "INR", []) == {"id": "p1"}


def test_catalog_creation_remains_blocked_without_api_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EFPS_WHAPI_LIVE", "1")
    monkeypatch.delenv("EFPS_WHAPI_API_ENABLED", raising=False)
    monkeypatch.setenv("EFPS_WHAPI_CATALOG_WRITE_ENABLED", "true")
    client = WhApiClient(WhApiCredentials("t"), base_url="https://e.test", transport=lambda req: {"id": "p1"})
    with pytest.raises(WhApiLiveTrafficBlocked, match="API traffic is disabled"):
        client.create_product("x", "d", 1, "INR", [])


def test_webhook_flag_defaults_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    from . import config
    monkeypatch.delenv("EFPS_WHAPI_WEBHOOK_ENABLED", raising=False)
    assert config.webhook_enabled() is True
    monkeypatch.setenv("EFPS_WHAPI_WEBHOOK_ENABLED", "false")
    assert config.webhook_enabled() is False
