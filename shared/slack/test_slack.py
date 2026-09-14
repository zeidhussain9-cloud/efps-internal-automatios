import hashlib
import hmac

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
