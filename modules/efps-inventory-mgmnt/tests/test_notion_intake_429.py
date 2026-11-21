"""Notion 429 backoff on the intake client (webhook workers + listing writes)."""

from __future__ import annotations

import sys
import pathlib

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
import notion_intake  # noqa: E402


class FakeResponse:
    def __init__(self, status_code, body=None):
        self.status_code = status_code
        self.ok = status_code < 400
        self._body = body or {}
        self.content = b"x"
        import json
        self.text = json.dumps(self._body)
        self.headers = {}

    def json(self):
        return self._body


class FlakySession:
    def __init__(self, failures, body=None):
        self.failures = failures
        self.body = body or {"ok": True}
        self.calls = 0

    def request(self, *a, **kw):
        self.calls += 1
        if self.calls <= self.failures:
            return FakeResponse(429, {"code": "rate_limited", "additional_data": {"retry_after": "0"}})
        return FakeResponse(200, self.body)


def test_intake_retries_429_then_succeeds(monkeypatch):
    monkeypatch.setattr(notion_intake.time, "sleep", lambda s: None)
    session = FlakySession(3)
    client = notion_intake.NotionClient("token", session=session)
    assert client.request("GET", "pages/x") == {"ok": True}
    assert session.calls == 4


def test_intake_gives_up_after_five_attempts(monkeypatch):
    monkeypatch.setattr(notion_intake.time, "sleep", lambda s: None)
    session = FlakySession(99)
    client = notion_intake.NotionClient("token", session=session)
    with pytest.raises(notion_intake.IntakeError):
        client.request("GET", "pages/x")
    assert session.calls == 5
