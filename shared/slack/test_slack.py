import hashlib
import hmac
import os
import pytest
from unittest.mock import patch

from shared.slack.client import SlackConfig, SlackError
from shared.credentials.keychain import MissingKeychainSecret
from shared.slack.safety import normalize_thread_control, safe_text
from shared.slack.security import verify_signature


def test_thread_controls_require_bare_word():
    assert normalize_thread_control("done") == "done"
    assert normalize_thread_control(" submit ") == "submit"
    assert normalize_thread_control("done, photos are attached") is None


def test_safe_text_blocks_slack_mentions():
    value = "Customer <@U123> and <!channel>"
    result = safe_text(value)
    assert "<@U123>" not in result
    assert "<!channel>" not in result


def test_signature_verification():
    secret = "test-secret"
    timestamp = "1700000000"
    body = b"command=/efps+status"
    base = b"v0:" + timestamp.encode() + b":" + body
    signature = "v0=" + hmac.new(secret.encode(), base, hashlib.sha256).hexdigest()
    assert verify_signature(body, timestamp, signature, now=1700000001, signing_secret=secret)
    assert not verify_signature(body, timestamp, signature, now=1700001000, signing_secret=secret)


class TestSlackConfig:
    @patch("shared.credentials.keychain.get_secret")
    @patch.dict(os.environ, {"SLACK_BOT_TOKEN": "env-var-token"})
    def test_from_env_uses_environment_variable_first(self, mock_get_secret):
        config = SlackConfig.from_env()
        assert config.bot_token == "env-var-token"
        mock_get_secret.assert_not_called()

    @patch("shared.credentials.keychain.get_secret", return_value="keychain-token")
    @patch.dict(os.environ, {}, clear=True)
    def test_from_env_falls_back_to_keychain(self, mock_get_secret):
        config = SlackConfig.from_env()
        assert config.bot_token == "keychain-token"
        mock_get_secret.assert_called_once_with("efps-whapi-panel-slack")

    @patch("shared.credentials.keychain.get_secret", side_effect=MissingKeychainSecret("Keychain unavailable"))
    @patch.dict(os.environ, {}, clear=True)
    def test_from_env_raises_error_if_no_credentials(self, mock_get_secret):
        with pytest.raises(SlackError, match="Slack bot token is not configured"):
            SlackConfig.from_env()
