from __future__ import annotations

import hashlib
import hmac
import json
import uuid
from pathlib import Path

import pytest

from src import notion_intake as intake


TOKEN = "notion-test-webhook-key"
PAGE_ID = "12345678-1234-4234-8234-123456789abc"
EVENT_ID = "22345678-1234-4234-8234-123456789abc"
ROW_ID = "notion-webhook:event:" + EVENT_ID
ARN = "arn:aws:lambda:ap-southeast-2:123456789012:function:test"


def signed_event(payload):
    body = json.dumps(payload, separators=(",", ":"))
    signature = "sha256=" + hmac.new(TOKEN.encode(), body.encode(), hashlib.sha256).hexdigest()
    return body, signature


class FakeStore:
    def __init__(self, *, should_enqueue=True, status="received"):
        self.should_enqueue = should_enqueue
        self.status = status
        self.recorded = []
        self.transitions = []

    def record_webhook_event(self, **event):
        self.recorded.append(event)
        return {"id": ROW_ID, "should_enqueue": self.should_enqueue, "status": self.status, "duplicate": not self.should_enqueue}

    def update_webhook_event(self, event_row_id, status, **kwargs):
        self.transitions.append((event_row_id, status, kwargs))
        self.status = status
        return {"ok": True, "status": status, "started": status in {"accepted", "processing"}}


def install_webhook_auth(monkeypatch, store):
    class FakeSecrets:
        def get_secret_value(self, **kwargs):
            return {"SecretString": json.dumps({"api_token": "internal", "webhook_secret": TOKEN})}

    class FakeBoto3:
        @staticmethod
        def client(name):
            assert name == "secretsmanager"
            return FakeSecrets()

    monkeypatch.setenv("NOTION_SECRET_ARN", "arn:aws:secretsmanager:ap-southeast-2:123456789012:secret:test")
    monkeypatch.setattr("boto3.client", FakeBoto3.client, raising=False)
    monkeypatch.setattr(intake, "SupabaseIntakeStore", lambda: store)


def test_signed_event_is_durably_recorded_before_worker_enqueue(monkeypatch):
    store = FakeStore()
    install_webhook_auth(monkeypatch, store)
    payload = {
        "id": EVENT_ID, "type": "page.created", "timestamp": "2026-11-14T01:02:03Z",
        "attempt_number": 1, "workspace_id": "42345678-1234-4234-8234-123456789abc",
        "subscription_id": "52345678-1234-4234-8234-123456789abc",
        "integration_id": "62345678-1234-4234-8234-123456789abc",
        "entity": {"id": PAGE_ID, "type": "page"},
    }
    body, signature = signed_event(payload)
    calls = []
    monkeypatch.setattr(intake, "_enqueue_worker", lambda *args, **kwargs: calls.append("enqueue"))
    context = type("Context", (), {"invoked_function_arn": ARN, "aws_request_id": "aws-req-1"})()

    result = intake.lambda_handler({"headers": {"x-notion-signature": signature}, "body": body}, context)

    assert result["statusCode"] == 202
    assert store.recorded[0]["notion_event_id"] == EVENT_ID
    assert store.recorded[0]["page_id"] == PAGE_ID
    assert store.recorded[0]["attempt_number"] == 1
    assert store.recorded[0]["payload"]["entity"]["id"] == PAGE_ID
    assert calls == ["enqueue"]
    assert [transition[1] for transition in store.transitions] == ["queued"]


def test_duplicate_delivery_is_kept_in_history_and_not_enqueued_again(monkeypatch):
    store = FakeStore(should_enqueue=False, status="queued")
    install_webhook_auth(monkeypatch, store)
    body, signature = signed_event({"id": EVENT_ID, "type": "page.created", "attempt_number": 2, "entity": {"id": PAGE_ID, "type": "page"}})
    queued = []
    monkeypatch.setattr(intake, "_enqueue_worker", lambda *args, **kwargs: queued.append(True))
    context = type("Context", (), {"invoked_function_arn": ARN})()

    result = intake.lambda_handler({"headers": {"x-notion-signature": signature}, "body": body}, context)

    assert result["statusCode"] == 202
    assert json.loads(result["body"])["duplicate"] is True
    assert store.recorded[0]["attempt_number"] == 2
    assert not store.transitions
    assert queued == []


def test_failed_event_delivery_can_be_requeued_on_notion_retry(monkeypatch):
    store = FakeStore(should_enqueue=True, status="failed")
    install_webhook_auth(monkeypatch, store)
    body, signature = signed_event({"id": EVENT_ID, "type": "page.properties_updated", "attempt_number": 2, "entity": {"id": PAGE_ID, "type": "page"}})
    queued = []
    monkeypatch.setattr(intake, "_enqueue_worker", lambda *args, **kwargs: queued.append(kwargs["event_row_id"]))
    context = type("Context", (), {"invoked_function_arn": ARN})()

    result = intake.lambda_handler({"headers": {"x-notion-signature": signature}, "body": body}, context)

    assert result["statusCode"] == 202
    assert queued == [ROW_ID]
    assert [transition[1] for transition in store.transitions] == ["queued"]


def test_signed_malformed_json_is_persisted_as_rejected_without_raw_body(monkeypatch):
    store = FakeStore()
    install_webhook_auth(monkeypatch, store)
    body = "{ definitely not json"
    signature = "sha256=" + hmac.new(TOKEN.encode(), body.encode(), hashlib.sha256).hexdigest()

    result = intake.lambda_handler({"headers": {"x-notion-signature": signature}, "body": body}, None)

    assert result["statusCode"] == 202
    assert store.recorded[0]["payload"] == {
        "malformed_json": True,
        "raw_body_sha256": hashlib.sha256(body.encode()).hexdigest(),
        "raw_body_size": len(body.encode()),
    }
    assert [transition[1] for transition in store.transitions] == ["rejected"]


def test_unsupported_signed_event_is_persisted_and_acknowledged(monkeypatch):
    store = FakeStore()
    install_webhook_auth(monkeypatch, store)
    body, signature = signed_event({"id": EVENT_ID, "type": "comment.created", "entity": {"id": PAGE_ID, "type": "page"}})
    monkeypatch.setattr(intake, "_enqueue_worker", lambda *args, **kwargs: pytest.fail("unsupported event must not enqueue"))

    result = intake.lambda_handler({"headers": {"x-notion-signature": signature}, "body": body}, None)

    assert result["statusCode"] == 202
    assert [transition[1] for transition in store.transitions] == ["unsupported"]


def test_event_ledger_failure_is_not_acknowledged(monkeypatch):
    install_webhook_auth(monkeypatch, FakeStore())
    class BrokenStore:
        def record_webhook_event(self, **event):
            raise intake.IntakeError("database unavailable")
    monkeypatch.setattr(intake, "SupabaseIntakeStore", BrokenStore)
    body, signature = signed_event({"id": EVENT_ID, "type": "page.created", "entity": {"id": PAGE_ID, "type": "page"}})

    result = intake.lambda_handler({"headers": {"x-notion-signature": signature}, "body": body}, None)

    assert result["statusCode"] == 503
    assert json.loads(result["body"])["error"] == "event history is unavailable"


def test_secret_lookup_failure_is_recorded_without_acknowledging_delivery(monkeypatch):
    store = FakeStore()
    class BrokenSecrets:
        def get_secret_value(self, **kwargs):
            raise RuntimeError("secrets manager unavailable")
    monkeypatch.setenv("NOTION_SECRET_ARN", "arn:aws:secretsmanager:ap-southeast-2:123456789012:secret:test")
    monkeypatch.setattr("boto3.client", lambda name: BrokenSecrets(), raising=False)
    monkeypatch.setattr(intake, "SupabaseIntakeStore", lambda: store)
    body, _ = signed_event({"id": EVENT_ID, "type": "page.created", "entity": {"id": PAGE_ID, "type": "page"}})

    result = intake.lambda_handler({"headers": {}, "body": body}, None)

    assert result["statusCode"] == 503
    assert store.recorded[0]["payload"]["unverified_delivery"] is True
    assert store.transitions[0][1] == "rejected"


def test_invalid_signature_is_recorded_without_storing_untrusted_body(monkeypatch):
    store = FakeStore()
    install_webhook_auth(monkeypatch, store)
    body, _ = signed_event({"id": EVENT_ID, "type": "page.created", "entity": {"id": PAGE_ID, "type": "page"}})

    result = intake.lambda_handler({"headers": {"x-notion-signature": "sha256=invalid"}, "body": body}, None)

    assert result["statusCode"] == 401
    assert store.recorded[0]["payload"]["unverified_delivery"] is True
    assert "entity" not in store.recorded[0]["payload"]
    assert [transition[1] for transition in store.transitions] == ["rejected"]


def test_worker_persists_processing_and_final_inventory_correlation(monkeypatch):
    store = FakeStore()
    monkeypatch.setattr(intake, "SupabaseIntakeStore", lambda: store)
    monkeypatch.setattr(intake, "process_page", lambda page_id, **kwargs: {
        "status": "Needs Review", "listing_id": "EF-2026-ABCD", "listing_page_id": "72345678-1234-4234-8234-123456789abc", "issues": ["manual review"],
    })
    context = type("Context", (), {"aws_request_id": "aws-worker-9"})()

    result = intake.lambda_handler({
        "_efps_notion_worker": True, "page_id": PAGE_ID, "event_type": "page.created",
        "event_id": EVENT_ID, "event_row_id": ROW_ID,
    }, context)

    assert result["status"] == "Needs Review"
    assert [transition[1] for transition in store.transitions] == ["processing", "needs_review"]
    final = store.transitions[-1][2]
    assert final["listing_id"] == "EF-2026-ABCD"
    assert final["listing_page_id"] == "72345678-1234-4234-8234-123456789abc"
    assert final["outcome"]["status"] == "Needs Review"


def test_worker_preserves_ignored_terminal_outcome(monkeypatch):
    store = FakeStore()
    monkeypatch.setattr(intake, "SupabaseIntakeStore", lambda: store)
    monkeypatch.setattr(intake, "process_page", lambda *args, **kwargs: {"status": "ignored", "listing_id": ""})

    result = intake.lambda_handler({
        "_efps_notion_worker": True, "page_id": PAGE_ID, "event_type": "page.created", "event_row_id": ROW_ID,
    }, None)

    assert result["status"] == "ignored"
    assert [transition[1] for transition in store.transitions] == ["processing", "ignored"]


def test_worker_exception_is_recorded_failed_then_rethrown_for_lambda_retry(monkeypatch):
    store = FakeStore()
    monkeypatch.setattr(intake, "SupabaseIntakeStore", lambda: store)
    monkeypatch.setattr(intake, "process_page", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("temporary failure")))
    context = type("Context", (), {"aws_request_id": "aws-worker-fail"})()

    with pytest.raises(RuntimeError, match="temporary failure"):
        intake.lambda_handler({"_efps_notion_worker": True, "page_id": PAGE_ID, "event_row_id": ROW_ID}, context)

    assert [transition[1] for transition in store.transitions] == ["processing", "failed"]
    assert store.transitions[-1][2]["outcome"] == {"exception_type": "RuntimeError"}


def test_event_payload_redacts_credentials_and_fingerprints_raw_body():
    payload = {"id": EVENT_ID, "type": "page.created", "entity": {"id": PAGE_ID, "type": "page"}, "verification_token": "do-not-store"}
    body, _ = signed_event(payload)
    result = intake._event_record_input(payload, body)

    assert result["payload"]["verification_token"] == "[REDACTED]"
    assert result["payload_sha256"] == hashlib.sha256(body.encode()).hexdigest()


def test_migration_enforces_rls_service_role_only_and_event_history():
    migration = Path(__file__).parents[3] / "db" / "migrations" / "20261114100000_crm_notion_webhook_event_history.sql"
    sql = migration.read_text()

    assert "alter table public.crm_inventory_intake_events" in sql.lower()
    assert "create table public.crm_notion_webhook_events" not in sql.lower()
    assert "event_key text" in sql.lower()
    assert "enable row level security" not in sql.lower()
    assert "crm_inventory_intake_events_event_key_idx" in sql.lower()
    assert "processing_error_history" in sql
    assert "'ignored'" in sql
    assert "delivery_attempts" in sql
    assert "status_history" in sql
    assert "crm_webhook_events" not in sql


def test_supabase_event_operations_use_only_the_new_notion_rpcs():
    root = Path(__file__).parents[3]
    function = (root / "supabase" / "functions" / "notion-inventory-state" / "index.ts").read_text()
    response = (root / "supabase" / "functions" / "notion-inventory-state" / "response-contract.mjs").read_text()

    assert "x-efps-intake-auth" in function
    assert "crm_record_notion_webhook_event" in function
    assert "crm_update_notion_webhook_event" in function
    assert "record_webhook_event" in function and "update_webhook_event" in function
    assert "record_webhook_event" in response and "update_webhook_event" in response
