from __future__ import annotations

import pytest

from .client import WhApiClient, WhApiCredentials, WhApiLiveTrafficBlocked


def test_live_gate_blocks_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("EFPS_WHAPI_LIVE", raising=False)
    client = WhApiClient(WhApiCredentials("test-token"), base_url="https://example.test")
    with pytest.raises(WhApiLiveTrafficBlocked):
        client.get("groups")


def test_live_gate_allows_injected_transport(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EFPS_WHAPI_LIVE", "1")
    seen = {}

    def transport(req):
        seen["authorization"] = req.headers["Authorization"]
        seen["method"] = req.method
        return {"ok": True}

    client = WhApiClient(
        WhApiCredentials("test-token"),
        base_url="https://example.test",
        transport=transport,
    )
    assert client.get("groups") == {"ok": True}
    assert seen == {"authorization": "Bearer test-token", "method": "GET"}


def test_verified_endpoint_primitives_use_correct_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EFPS_WHAPI_LIVE", "1")
    seen: list[tuple[str, str]] = []

    def transport(req):
        seen.append((req.method, req.full_url))
        return {"ok": True}

    client = WhApiClient(WhApiCredentials("test-token"), base_url="https://example.test", transport=transport)
    client.health()
    client.settings()
    client.allowed_webhook_events()
    client.test_webhook({"type": "message", "url": "https://example.test/hook", "mode": "body"})
    client.send_text({"to": "919999999999", "body": "test"})

    assert [method for method, _ in seen] == ["GET", "GET", "GET", "POST", "POST"]
    assert seen[0][1].endswith("/health")
    assert seen[1][1].endswith("/settings")
    assert seen[2][1].endswith("/settings/events")
    assert seen[3][1].endswith("/settings/webhook_test")
    assert seen[4][1].endswith("/messages/text")


def test_get_products_paginates(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EFPS_WHAPI_LIVE", "1")
    call_num = 0

    def transport(req):
        nonlocal call_num
        call_num += 1
        if call_num == 1:
            return {
                "products": [{"id": "p1", "product_retailer_id": "A"}] * 100,
                "paging": {"cursors": {"after": "cursor_page2"}},
            }
        return {
            "products": [{"id": "p101", "product_retailer_id": "B"}],
        }

    client = WhApiClient(WhApiCredentials("t"), base_url="https://e.test", transport=transport)
    products = client.get_products(count=200)
    assert len(products) == 101
    assert call_num == 2


def test_find_product_by_retailer_id_beyond_first_page(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EFPS_WHAPI_LIVE", "1")
    call_num = 0

    def transport(req):
        nonlocal call_num
        call_num += 1
        if call_num == 1:
            return {
                "products": [{"id": f"p{i}", "product_retailer_id": f"R{i}"} for i in range(100)],
                "paging": {"cursors": {"after": "c2"}},
            }
        return {"products": [{"id": "p100", "product_retailer_id": "TARGET"}]}

    client = WhApiClient(WhApiCredentials("t"), base_url="https://e.test", transport=transport)
    found = client.find_product_by_retailer_id("TARGET")
    assert found is not None
    assert found["id"] == "p100"


def test_find_products_by_image_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EFPS_WHAPI_LIVE", "1")

    def transport(req):
        return {
            "products": [
                {"id": "p1", "product_retailer_id": "A", "images": [{"link": "https://cdn/img1"}]},
                {"id": "p2", "product_retailer_id": "B", "images": [{"link": "https://cdn/img2"}]},
                {"id": "p3", "product_retailer_id": "C", "images": [{"link": "https://cdn/img3"}]},
            ]
        }

    client = WhApiClient(WhApiCredentials("t"), base_url="https://e.test", transport=transport)
    matches = client.find_products_by_image_url(["https://cdn/img1", "https://cdn/img3"])
    assert len(matches) == 2
    assert {m["id"] for m in matches} == {"p1", "p3"}


def test_get_collections(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EFPS_WHAPI_LIVE", "1")

    def transport(req):
        assert req.method == "GET"
        assert req.full_url.endswith("/business/collections")
        return {"collections": [{"id": "c1", "name": "Test"}, {"id": "c2", "name": "Other"}]}

    client = WhApiClient(WhApiCredentials("t"), base_url="https://e.test", transport=transport)
    result = client.get_collections()
    assert len(result) == 2
    assert result[0]["id"] == "c1"


def test_edit_collection(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EFPS_WHAPI_LIVE", "1")
    seen: dict = {}

    def transport(req):
        import json as _json
        seen["method"] = req.method
        seen["url"] = req.full_url
        seen["body"] = _json.loads(req.data) if req.data else None
        return {"id": "c1", "status": "APPROVED"}

    client = WhApiClient(WhApiCredentials("t"), base_url="https://e.test", transport=transport)
    result = client.edit_collection("c1", add_products=["p1", "p2"])
    assert seen["method"] == "PATCH"
    assert seen["url"].endswith("/business/collections/c1")
    assert seen["body"] == {"add_products": ["p1", "p2"]}
    assert result["status"] == "APPROVED"
