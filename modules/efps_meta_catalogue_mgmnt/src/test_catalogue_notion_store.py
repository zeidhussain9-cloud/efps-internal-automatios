

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


def test_listing_row_works_without_the_removed_collection_columns_and_never_reads_them():
    import catalogue_notion_store as cns
    page = {"id": "p1", "properties": {
        "listing_id": {"type": "rich_text", "rich_text": [{"plain_text": "EF-1"}]},
        "Availability": {"type": "select", "select": {"name": "Available"}},
        "Pipeline Status": {"type": "select", "select": {"name": "Ready To Post"}},
        # a stale formula value must be ignored: the row never carries it
        "meta_catalog_collection_id": {"type": "formula", "formula": {"string": "123"}},
    }}
    row = cns.listing_row(page)
    assert row["listing_id"] == "EF-1" and row["Availability"] == "Available"
    assert "meta_catalog_collection_id" not in row
