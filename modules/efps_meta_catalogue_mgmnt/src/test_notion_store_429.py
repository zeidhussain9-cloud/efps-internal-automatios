"""Notion 429 backoff: both Notion clients retry on rate limits instead of dying mid-run."""

from __future__ import annotations

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import catalogue_notion_store as store_mod  # noqa: E402


class FakeResponse:
    def __init__(self, status_code, body=None, retry_after=None):
        self.status_code = status_code
        self.ok = status_code < 400
        self._body = body or {}
        self.content = b"x"
        self.text = __import__("json").dumps(self._body)
        self.headers = {"Retry-After": str(retry_after)} if retry_after else {}

    def json(self):
        return self._body


class FlakySession:
    """429s a given number of times, then succeeds."""

    def __init__(self, failures, body=None):
        self.failures = failures
        self.body = body or {"ok": True}
        self.calls = 0

    def request(self, *a, **kw):
        self.calls += 1
        if self.calls <= self.failures:
            return FakeResponse(429, {"code": "rate_limited", "additional_data": {"retry_after": "0"}}, retry_after=0)
        return FakeResponse(200, self.body)


def test_store_retries_429_then_succeeds(monkeypatch):
    monkeypatch.setattr(store_mod.time, "sleep", lambda s: None)
    session = FlakySession(2)
    store = store_mod.NotionCatalogueStore("token", session=session)
    assert store.request("GET", "pages/x") == {"ok": True}
    assert session.calls == 3


def test_store_gives_up_after_five_attempts(monkeypatch):
    monkeypatch.setattr(store_mod.time, "sleep", lambda s: None)
    session = FlakySession(99)
    store = store_mod.NotionCatalogueStore("token", session=session)
    try:
        store.request("GET", "pages/x")
        assert False, "should raise"
    except store_mod.CatalogueStoreError as exc:
        assert "429" in str(exc)
    assert session.calls == 5
