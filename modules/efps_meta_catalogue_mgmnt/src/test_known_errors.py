from known_errors import known_recovery

def test_known_log_permission_failure_has_durable_fallback():
    assert known_recovery('append_decision_log', 'Notion 404 object_not_found')['recovery']=='durable_log_fallback'

def test_delete_errors_and_novel_errors_never_auto_recover():
    assert known_recovery('delete', 'HTTP 404') is None
    assert known_recovery('append_decision_log', 'HTTP 403 forbidden') is None
