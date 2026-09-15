import os
from unittest.mock import patch

from shared.google_maps.client import GoogleMapsClient


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
