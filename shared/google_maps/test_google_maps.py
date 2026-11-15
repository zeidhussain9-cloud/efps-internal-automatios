import os
from unittest.mock import patch

from shared.google_maps.client import GoogleMapsClient, MapsResolution


def test_compatibility_client_does_not_consume_google_credentials():
    from shared.ola_maps.client import OlaMapsClient
    with patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "obsolete"}):
        with patch("shared.credentials.get_secret", side_effect=AssertionError("No Google secret lookup")):
            client = GoogleMapsClient(api_key="obsolete", ola_client=OlaMapsClient(api_key="test-ola"))
    assert not hasattr(client, "api_key")
    assert client.resolve().confidence == "NOT_VERIFIED"


def test_extracts_google_share_short_link():
    raw = "📍 Landmark: https://share.google/AbCdEf123"
    assert GoogleMapsClient.extract_url(raw) == "https://share.google/AbCdEf123"


def test_extracts_supported_maps_urls_without_mutating_source_url():
    cases = (
        "https://maps.app.goo.gl/AzNBBPZrHBcTrnU3A?g_st=ic",
        "https://goo.gl/maps/Example123",
        "https://maps.google.com/?q=12.9716,77.5946",
        "https://www.google.com/maps/place/Bengaluru",
        "https://share.google/oo7aBEUjVMGWUQzPm",
    )
    for source_url in cases:
        raw = f"📍 Society Name:\n{source_url}\n"
        assert GoogleMapsClient.extract_url(raw) == source_url
        assert GoogleMapsClient.is_maps_url(source_url)


def test_extracts_maps_url_from_source_wrappers_and_terminal_punctuation():
    source_url = "https://share.google/AbCdEf123"
    raw = f"<*{source_url}*>)."
    assert GoogleMapsClient.extract_url(raw) == source_url
    assert GoogleMapsClient.is_maps_url(source_url)


def test_does_not_capture_adjacent_text_as_part_of_maps_url():
    source_url = "https://maps.app.goo.gl/Example123"
    raw = f"{source_url}\nNext field: Bengaluru"
    assert GoogleMapsClient.extract_url(raw) == source_url


def test_normalizes_slack_wrapped_maps_link():
    source_url = "https://maps.app.goo.gl/Example123"
    wrapped = f"<{source_url}|maps.app.goo.gl>"
    assert GoogleMapsClient.normalize_source_link(wrapped) == source_url
    assert GoogleMapsClient.extract_url(wrapped) == source_url
    assert GoogleMapsClient.is_maps_url(wrapped)


def test_no_legacy_google_transport_in_compatibility_client():
    from shared.ola_maps.client import OlaMapsClient
    from shared.ola_maps.source_link import LinkEvidence
    client = GoogleMapsClient(ola_client=OlaMapsClient(api_key="test"), link_inspector=lambda url: LinkEvidence(url, reachable=True))
    with patch("requests.get") as get:
        result = client.resolve(maps_url="https://maps.app.goo.gl/opaque")
    get.assert_not_called()
    assert result.confidence == "OLA_EVIDENCE"
    assert result.evidence["pin_status"] == "not_verified"
