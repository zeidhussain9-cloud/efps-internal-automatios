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


def _paged_client(monkeypatch, total, ignore_offset=False):
    from urllib.parse import urlparse, parse_qs
    monkeypatch.setenv("EFPS_WHAPI_API_ENABLED", "true")
    monkeypatch.setenv("EFPS_WHAPI_LIVE", "1")
    calls = []

    def transport(req):
        q = parse_qs(urlparse(req.full_url).query)
        count, offset = int(q["count"][0]), int(q.get("offset", ["0"])[0])
        calls.append((count, offset))
        if ignore_offset:
            offset = 0
        return {"products": [{"id": f"p{i}"} for i in range(offset, min(offset + count, total))]}

    return WhApiClient(WhApiCredentials("t"), base_url="https://e.test", transport=transport), calls


def test_get_products_reads_every_page_with_documented_count_and_offset(monkeypatch):
    client, calls = _paged_client(monkeypatch, 250)
    products = client.get_products(count=10000)
    assert len(products) == 250 and len({p["id"] for p in products}) == 250
    assert calls == [(100, 0), (100, 100), (100, 200)]  # count within 1..500, offset-based


def test_get_products_exact_multiple_of_page_size(monkeypatch):
    client, calls = _paged_client(monkeypatch, 200)
    assert len(client.get_products(count=10000)) == 200


def test_get_products_refuses_a_repeating_page_instead_of_returning_a_partial_catalogue(monkeypatch):
    client, _ = _paged_client(monkeypatch, 250, ignore_offset=True)
    with pytest.raises(RuntimeError, match="repeated a page"):
        client.get_products(count=10000)


def test_collection_products_read_allows_only_exact_numeric_get(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EFPS_WHAPI_API_ENABLED", "true")
    monkeypatch.setenv("EFPS_WHAPI_LIVE", "1")
    monkeypatch.delenv("EFPS_WHAPI_CATALOG_WRITE_ENABLED", raising=False)
    seen = []
    client = WhApiClient(WhApiCredentials("t"), base_url="https://e.test", transport=lambda req: seen.append(req) or {"products": []})
    assert client.get_collection_products("2585336038575419") == {"products": []}
    assert "products_count=30" in seen[0].full_url
    assert len(seen) == 1
    for bad in ("/business/collections/abc/products", "/business/collections/123/products/extra",
                "/business/collections/123", "/business/collections/123/other",
                "/business/collections/../products", "/business/collections//products"):
        with pytest.raises(WhApiLiveTrafficBlocked, match="outside the catalogue-operation allowlist"):
            client.get(bad)
    for verb in ("post", "patch", "delete"):
        with pytest.raises(WhApiLiveTrafficBlocked):
            getattr(client, verb)("/business/collections/123/products", {}) if verb != "delete" else client._request("DELETE", "/business/collections/123/products")
    with pytest.raises(ValueError):
        client.get_collection_products("12/3")
    assert len(seen) == 1
