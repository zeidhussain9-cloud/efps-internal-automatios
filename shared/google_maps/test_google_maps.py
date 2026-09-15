import os
from unittest.mock import patch

from shared.google_maps.client import GoogleMapsClient, MapsResolution


def test_maps_explicit_key_has_priority():
    with patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "env-key"}):
        with patch("shared.credentials.get_secret", return_value="keychain-key"):
            client = GoogleMapsClient(api_key="explicit-key")
            assert client.api_key == "explicit-key"


def test_maps_env_key_has_priority_over_keychain():
    with patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "env-key"}):
        with patch("shared.credentials.get_secret", return_value="keychain-key"):
            client = GoogleMapsClient()
            assert client.api_key == "env-key"


def test_maps_keychain_fallback():
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("GOOGLE_MAPS_API_KEY", None)
        with patch("shared.credentials.get_secret", return_value="keychain-key"):
            client = GoogleMapsClient()
            assert client.api_key == "keychain-key"


def test_maps_missing_key_is_unverified():
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("GOOGLE_MAPS_API_KEY", None)
        with patch("shared.credentials.get_secret", side_effect=Exception("missing")):
            client = GoogleMapsClient()
            assert client.api_key == ""


def test_maps_resolution_defaults_to_not_verified_without_input():
    client = GoogleMapsClient(api_key="test-key")
    result = client.resolve()
    assert isinstance(result, MapsResolution)
    assert result.confidence == "NOT_VERIFIED"


def test_maps_resolve_contract_is_keyword_only():
    import inspect

    signature = inspect.signature(GoogleMapsClient.resolve)
    assert signature.parameters["maps_url"].kind is inspect.Parameter.KEYWORD_ONLY
    assert signature.parameters["address"].kind is inspect.Parameter.KEYWORD_ONLY


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
