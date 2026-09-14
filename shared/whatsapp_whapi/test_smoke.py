from __future__ import annotations

from client import WhApiClient, WhApiCredentials


def test_whapi_client_constructs_without_live_network_access() -> None:
    client = WhApiClient(WhApiCredentials("test-token"), base_url="https://example.test")
    assert client.live_enabled() is False
