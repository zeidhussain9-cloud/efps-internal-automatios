from pathlib import Path

ROOT = Path(__file__).resolve().parent


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_history_and_lost_actions_preserve_current_main_ui_contract():
    source = read("interactive_handler.py")
    assert 'if aid=="history::open"' in source
    assert "slack.post_message(LEADS_CHANNEL,history_line(item)" in source
    assert 'callback_id":"lead_history"' not in source
    assert 'callback_id":"lead_lost"' not in source
    assert 'if aid.startswith("stage::")' in source
    assert 'L.set_stage(phone,aid.split("::",1)[1])' in source


def test_digest_uses_slack_history_without_session_persistence_or_pinning():
    source = read("modules/efpd-lead-mgmnt/src/digest.py")
    assert "def _existing_dashboard" in source
    assert "slack.history(LEADS_CHANNEL, limit=100)" in source
    assert "DDB_SESSIONS" not in source
    assert "pins.add" not in source
    assert "_save_ts" not in source


def test_audit_description_uses_ist():
    source = read("modules/efpd-lead-mgmnt/src/audit.py")
    assert ".astimezone(L.IST)" in source


def test_webhook_authentication_precedes_live_gate():
    source = read("webhook_handler.py")
    auth = source.index("if not _authorised(event):")
    gate = source.index("if not whapi_config.live_enabled():")
    assert auth < gate
