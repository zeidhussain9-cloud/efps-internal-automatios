import sys, pathlib
import pytest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import catalogue_notion_store as cns


class Sess:
    """Fake Notion: stores error_notes of one page."""
    def __init__(self, notes):
        self.notes = notes
        self.patches = []

    def request(self, method, url, **kw):
        outer = self
        class R:
            status_code, ok, content, text, headers = 200, True, b"x", "", {}
            def json(self_inner):
                if method == "GET":
                    return {"properties": {"error_notes": {"rich_text": [{"plain_text": outer.notes}] if outer.notes else []}}}
                outer.notes = kw["json"]["properties"]["error_notes"]["rich_text"][0]["text"]["content"]
                outer.patches.append(outer.notes)
                return {}
        return R()


def store(notes):
    s = Sess(notes)
    st = cns.NotionCatalogueStore("t", session=s)
    return st, s


OLD = "\n".join(f"[2026-11-0{i%9+1} 10:00:00Z] UPDATE EF-2611-{i:04d} product=p{i} OK patched title and price fields" for i in range(40))


def test_attempt_survives_long_existing_notes_and_later_lines():
    st, s = store(OLD)
    assert len(OLD) > 2000
    st.append_activity("p", "[t] CREATE EF-1 ATTEMPT STARTED about to call create_product")
    assert "ATTEMPT STARTED" in s.notes and len(s.notes) <= 2000
    for i in range(30):  # many later lines must not push the unsettled attempt out
        st.append_activity("p", f"[t] UPDATE EF-1 product=p{i} OK something long enough to fill the cell quickly, padding padding")
    assert "ATTEMPT STARTED" in s.notes and len(s.notes) <= 2000


def test_settlement_line_is_kept_and_unpins():
    st, s = store(OLD)
    st.append_activity("p", "[t] CREATE EF-1 ATTEMPT STARTED about")
    st.append_activity("p", "[t] CREATE EF-1 product=9 OK created and verified")
    assert s.notes.splitlines()[-1].endswith("created and verified")
    for i in range(40):
        st.append_activity("p", f"[t] UPDATE EF-1 product=p{i} OK padding padding padding padding padding padding")
    assert len(s.notes) <= 2000  # settled attempts may age out normally


def test_oversized_lines_are_cut_but_the_pending_attempt_is_always_kept():
    big = "[t] CREATE EF-1 ATTEMPT STARTED " + "x" * 3000
    st, s = store("")
    st.append_activity("p", big)
    for i in range(8):
        st.append_activity("p", "[t] UPDATE EF-1 OK " + "y" * 3000)
    assert "ATTEMPT STARTED" in s.notes and len(s.notes) <= 2000  # 600-char line cap: pin + newest always fit


def test_trim_raises_if_pin_and_newest_could_not_fit(monkeypatch):
    monkeypatch.setattr(cns, "_ERROR_NOTES_LIMIT", 100)
    with pytest.raises(cns.CatalogueStoreError):
        cns._trim_notes("[t] CREATE EF-1 ATTEMPT STARTED " + "a" * 80 + "\n[t] UPDATE EF-1 OK " + "b" * 80)
