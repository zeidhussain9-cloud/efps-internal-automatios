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
