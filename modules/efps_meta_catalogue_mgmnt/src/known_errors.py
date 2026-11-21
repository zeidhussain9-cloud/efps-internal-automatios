"""Bounded recoveries from recorded cases. Never retry catalogue mutations.

Case LOG_PAGE_UNSHARED: 21 Nov 2026 Decision Log entry. Notion connection
cannot see the log page. Preserve the exact intended entry in CloudWatch for
relay instead of retrying the operation or hiding the missing permission.
"""
KNOWN_ERRORS = {
    'LOG_PAGE_UNSHARED': {
        'operation': 'append_decision_log',
        'markers': ('object_not_found', '404'),
        'recovery': 'durable_log_fallback',
        'source': 'Decision Log, 21 Nov 2026, Tuesday scheduler rehearsal',
    },
}

def known_recovery(operation, error):
    text = str(error)
    for case_id, case in KNOWN_ERRORS.items():
        if operation == case['operation'] and any(m in text for m in case['markers']):
            return {'case_id': case_id, 'recovery': case['recovery'], 'source': case['source']}
    return None
