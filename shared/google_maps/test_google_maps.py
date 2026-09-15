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
