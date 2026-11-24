"""Tests for the gated catalogue trigger surface."""
from __future__ import annotations

import hashlib
import hmac

import pytest

import catalogue_trigger
from catalogue_trigger import CatalogueTriggerError

SECRET = "t" * 40


def _headers(ts: str, secret: str = SECRET) -> dict:
    sig = hmac.new(secret.encode(), ts.encode(), hashlib.sha256).hexdigest()
    return {"X-EFPS-Inventory-Timestamp": ts, "X-EFPS-Inventory-Signature": sig}


def test_valid_signature_passes():
    assert catalogue_trigger.verify_signature(_headers("1000"), secret=SECRET, now=1000.0)


def test_signature_window_allows_five_minutes():
    assert catalogue_trigger.verify_signature(_headers("700"), secret=SECRET, now=1000.0)
    assert not catalogue_trigger.verify_signature(_headers("699"), secret=SECRET, now=1000.0)


def test_wrong_secret_missing_headers_and_bad_timestamp_fail_closed():
    assert not catalogue_trigger.verify_signature(_headers("1000", "x" * 40), secret=SECRET, now=1000.0)
    assert not catalogue_trigger.verify_signature({}, secret=SECRET, now=1000.0)
    assert not catalogue_trigger.verify_signature({"X-EFPS-Inventory-Timestamp": "abc", "X-EFPS-Inventory-Signature": "y"}, secret=SECRET, now=1000.0)
    assert not catalogue_trigger.verify_signature(_headers("1000"), secret="", now=1000.0)


def test_header_names_are_case_insensitive():
    ts = "1000"
    sig = hmac.new(SECRET.encode(), ts.encode(), hashlib.sha256).hexdigest()
    assert catalogue_trigger.verify_signature({"x-efps-inventory-timestamp": ts, "x-efps-inventory-signature": sig}, secret=SECRET, now=1000.0)


def test_parse_operation_accepts_the_five_operations_only():
    for op in catalogue_trigger.OPERATIONS:
        assert catalogue_trigger.parse_operation('{"operation": "%s"}' % op) == op
    assert catalogue_trigger.parse_operation('{"operation": " CREATE "}') == "create"
    with pytest.raises(CatalogueTriggerError):
        catalogue_trigger.parse_operation('{"operation": "drop everything"}')
    with pytest.raises(CatalogueTriggerError):
        catalogue_trigger.parse_operation("not json")


def test_run_catalogue_operation_uses_injected_store_and_whapi(monkeypatch):
    import catalogue_runner

    seen = {}

    def fake_run(operation, *, store, whapi, masters, time_left=None):
        seen.update(operation=operation, store=store, whapi=whapi, masters=masters)
        return {"counts": {"ok": 1}}

    monkeypatch.setattr(catalogue_runner, "run_operation", fake_run)
    store, whapi = object(), object()
    result = catalogue_trigger.run_catalogue_operation("reconcile", notion_token="x", store=store, whapi=whapi)
    assert result == {"counts": {"ok": 1}}
    assert seen["operation"] == "reconcile" and seen["store"] is store and seen["whapi"] is whapi
    assert seen["masters"] == {"EFPS_WHAPI_LIVE": False, "EFPS_WHAPI_API_ENABLED": False}


def test_run_catalogue_operation_rejects_unknown_operation():
    with pytest.raises(CatalogueTriggerError):
        catalogue_trigger.run_catalogue_operation("wipe", notion_token="x", store=object(), whapi=object())
