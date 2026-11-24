

def test_notion_429_sleep_is_refused_when_the_invocation_has_no_time_left(monkeypatch):
    import catalogue_notion_store as cns

    class R:
        status_code, ok, content, text, headers = 429, False, b"x", "rate", {"Retry-After": "20"}
        def json(self): return {}

    class S:
        def request(self, *a, **k): return R()
    slept = []
    monkeypatch.setattr(cns.time, "sleep", slept.append)
    store = cns.NotionCatalogueStore("t", session=S())
    store.time_left = lambda: 40.0
    import pytest
    with pytest.raises(cns.CatalogueStoreError, match="not enough invocation time"):
        store.request("POST", "databases/x/query", payload={})
    assert slept == []
