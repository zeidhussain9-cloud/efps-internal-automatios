from __future__ import annotations

import os

import pytest

from client import WhApiClient, WhApiCredentials, WhApiLiveTrafficBlocked


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
        return {"ok": True}

    client = WhApiClient(
        WhApiCredentials("test-token"),
        base_url="https://example.test",
        transport=transport,
    )
    assert client.get("groups") == {"ok": True}
    assert seen["authorization"] == "Bearer test-token"
