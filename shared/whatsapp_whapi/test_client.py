from __future__ import annotations

import pytest

from .client import WhApiClient, WhApiCredentials, WhApiLiveTrafficBlocked


def test_api_is_disabled_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("EFPS_WHAPI_API_ENABLED", raising=False)
    monkeypatch.setenv("EFPS_WHAPI_LIVE", "1")
    client = WhApiClient(WhApiCredentials("test-token"), base_url="https://example.test")
    with pytest.raises(WhApiLiveTrafficBlocked, match="outside the catalogue-operation allowlist"):
        client.get("groups")


def test_catalogue_reads_are_gated_but_allowed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EFPS_WHAPI_API_ENABLED", "true")
    monkeypatch.setenv("EFPS_WHAPI_LIVE", "1")
    client = WhApiClient(WhApiCredentials("test-token"), base_url="https://example.test", transport=lambda req: {"products": []})
    assert client.get("/business/products") == {"products": []}
    assert client.get_product("p1") == {"products": []}
    monkeypatch.delenv("EFPS_WHAPI_LIVE", raising=False)
    with pytest.raises(WhApiLiveTrafficBlocked):
        client.get("/business/products")


def test_non_catalogue_whapi_operations_are_always_blocked(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EFPS_WHAPI_API_ENABLED", "true")
    monkeypatch.setenv("EFPS_WHAPI_LIVE", "1")
    client = WhApiClient(WhApiCredentials("test-token"), base_url="https://example.test")
    with pytest.raises(WhApiLiveTrafficBlocked, match="outside the catalogue-operation allowlist"):
        client.send_text({"to": "919999999999", "body": "test"})
    with pytest.raises(WhApiLiveTrafficBlocked, match="outside the catalogue-operation allowlist"):
        client.get("groups")


def test_catalogue_writes_require_the_write_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EFPS_WHAPI_API_ENABLED", "true")
    monkeypatch.setenv("EFPS_WHAPI_LIVE", "1")
    monkeypatch.delenv("EFPS_WHAPI_CATALOG_WRITE_ENABLED", raising=False)
    client = WhApiClient(WhApiCredentials("test-token"), base_url="https://example.test", transport=lambda req: {"ok": True})
    with pytest.raises(WhApiLiveTrafficBlocked, match="non-approved WhAPI operation"):
        client.edit_collection("c1", add_products=["p1"])
    with pytest.raises(WhApiLiveTrafficBlocked, match="non-approved WhAPI operation"):
        client.delete_product("p1")
    with pytest.raises(WhApiLiveTrafficBlocked, match="non-approved WhAPI operation"):
        client.update_product("p1", {"name": "x"})
    monkeypatch.setenv("EFPS_WHAPI_CATALOG_WRITE_ENABLED", "true")
    assert client.delete_product("p1") == {"ok": True}
    assert client.update_product("p1", {"name": "x"}) == {"ok": True}


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


def test_requests_send_a_browser_user_agent(monkeypatch: pytest.MonkeyPatch) -> None:
    # gate.whapi.cloud is behind Cloudflare, which rejects known bot UAs
    # (HTTP 403, error 1010). Regression guard: every request must carry the
    # real browser UA verified against the live gateway on 2026-11-21.
    monkeypatch.setenv("EFPS_WHAPI_API_ENABLED", "true")
    monkeypatch.setenv("EFPS_WHAPI_LIVE", "1")
    seen = {}

    def transport(req):
        seen["ua"] = req.headers.get("User-agent")
        return {"products": []}

    client = WhApiClient(WhApiCredentials("test-token"), base_url="https://example.test", transport=transport)
    client.get("/business/products")
    assert seen["ua"] is not None
    assert seen["ua"].startswith("Mozilla/5.0")
    assert "node-fetch" not in seen["ua"]
