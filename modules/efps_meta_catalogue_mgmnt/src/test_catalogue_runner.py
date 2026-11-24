"""Per-operation tests for the gated catalogue runner (fake Whapi + fake store)."""

from __future__ import annotations

import sys
import pathlib

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import catalogue_runner as runner  # noqa: E402

MASTERS_ON = {"EFPS_WHAPI_LIVE": True, "EFPS_WHAPI_API_ENABLED": True}
ALL_SWITCHES = {"CREATE": True, "UPDATE": True, "DELETE": True, "ASSIGN": True, "RECONCILE": True, "DRY_RUN": False}
COLLECTION = "2370295543377765"


class FakeWhapi:
    def __init__(self):
        self.products = {}  # id -> product dict
        self.next_id = 100
        self.calls = []
        self.fail_next = None

    def _maybe_fail(self):
        if self.fail_next:
            exc, self.fail_next = self.fail_next, None
            raise exc

    def find_product_by_retailer_id(self, retailer_id):
        self._maybe_fail()
        self.calls.append(("find", retailer_id))
        for p in self.products.values():
            if p.get("product_retailer_id") == retailer_id:
                return p
        return None

    def create_product(self, name, description, price, currency, images, url="", product_retailer_id="", **kw):
        self._maybe_fail()
        self.calls.append(("create", product_retailer_id))
        self.next_id += 1
        pid = str(self.next_id)
        self.products[pid] = {"id": pid, "name": name, "description": description, "price": price,
                              "currency": currency, "images": images, "product_retailer_id": product_retailer_id,
                              "collection_ids": []}
        return {"id": pid}

    def get_product(self, product_id):
        self._maybe_fail()
        self.calls.append(("get", product_id))
        if product_id not in self.products:
            raise RuntimeError("WhAPI HTTP 404: not found")
        return self.products[product_id]

    def update_product(self, product_id, payload):
        self._maybe_fail()
        self.calls.append(("update", product_id))
        self.products[product_id].update(payload)
        return {"ok": True}

    def delete_product(self, product_id):
        self._maybe_fail()
        self.calls.append(("delete", product_id))
        if product_id not in self.products:
            raise RuntimeError("WhAPI HTTP 404: not found")
        del self.products[product_id]
        return {"ok": True}

    def edit_collection(self, collection_id, *, add_products=None, remove_products=None):
        self._maybe_fail()
        self.calls.append(("assign", collection_id, tuple(add_products or ())))
        for pid in add_products or []:
            self.products[pid].setdefault("collection_ids", []).append(collection_id)
        return {"ok": True}

    def get_products(self, count=100):
        self._maybe_fail()
        return list(self.products.values())


class FakeStore:
    def __init__(self, rows, switches=None):
        self.rows = rows
        self.switches = ALL_SWITCHES if switches is None else switches
        self.updates = []        # (page_id, props)
        self.activity = []       # (page_id, line)
        self.red_marks = []      # (page_id, product_id)
        self.panel = []          # (op, summary)
        self.review_entries = []
        self.review_done = []
        self.decisions = []

    def read_switches(self):
        return dict(self.switches)

    def query_listings(self):
        return list(self.rows)

    def update_listing(self, page_id, props):
        self.updates.append((page_id, props))
        for row in self.rows:
            if row.get("page_id") == page_id:
                row.update(props)

    def append_activity(self, page_id, line):
        self.activity.append((page_id, line))

    def mark_product_id_removed(self, page_id, product_id):
        self.red_marks.append((page_id, product_id))

    def write_panel_summary(self, op, summary):
        self.panel.append((op, summary))

    def read_review_decisions(self, op):
        return [d for d in self.decisions if d.get("operation") == op]

    def mark_review_done(self, entry_id, result):
        self.review_done.append((entry_id, result))

    def add_review_entry(self, entry):
        self.review_entries.append(entry)


def make_row(**kw):
    row = {
        "page_id": "page-1", "listing_id": "EF-2611-AAAA",
        "Availability": "Available", "Pipeline Status": "Ready To Post", "live at": [],
        "meta_catalog_id": "", "meta_catalog_collection_id": "",
        "cloudinary_image_urls": "https://img/1.jpg https://img/2.jpg",
        "monthly_rent": "40000", "catalog_title": "Semi Furnished 2 BHK - Haralur",
        "catalogue_description": "desc text",
        "whatsapp_post": "post text", "google_maps_url": "https://www.google.com/maps/search/?api=1&query=x",
        "BHK": "2 BHK",
    }
    row.update(kw)
    return row


def run(op, store, whapi, sleeper=lambda s: None):
    return runner.run_operation(op, store=store, whapi=whapi, masters=MASTERS_ON, sleeper=sleeper)


# --- create selection: the four locked conditions (24 Nov 2026) ---

def test_create_selection_requires_all_four_conditions():
    assert runner.eligible_create(make_row())
    assert not runner.eligible_create(make_row(**{"Pipeline Status": "New"}))
    assert not runner.eligible_create(make_row(**{"Pipeline Status": ""}))
    assert not runner.eligible_create(make_row(Availability="On Hold"))
    assert not runner.eligible_create(make_row(Availability="Rented Out"))
    assert not runner.eligible_create(make_row(**{"live at": ["Meta Catalogue"]}))
    assert runner.eligible_create(make_row(**{"live at": ["WhatsApp Groups"]}))
    assert not runner.eligible_create(make_row(meta_catalog_id="77"))


def test_create_prechecks_skip_with_reason():
    for kw, reason in [
        ({"listing_id": ""}, "listing_id blank"),
        ({"catalog_title": ""}, "catalog_title blank"),
        ({"catalogue_description": ""}, "catalogue_description blank"),
        ({"monthly_rent": "0"}, "monthly_rent"),
        ({"cloudinary_image_urls": ""}, "no photos"),
    ]:
        store = FakeStore([make_row(**kw)], switches={**ALL_SWITCHES, "ASSIGN": False})
        result = run("create", store, FakeWhapi())
        assert reason in result["lines"][0], (kw, result["lines"])
        assert store.updates == []


# --- gating ---

def test_all_eight_states_logged_at_run_start():
    store = FakeStore([])
    result = run("create", store, FakeWhapi())
    assert set(result["states"]) == {"EFPS_WHAPI_LIVE", "EFPS_WHAPI_API_ENABLED", "CREATE", "UPDATE", "DELETE", "ASSIGN", "RECONCILE", "DRY_RUN"}


def test_unreadable_switches_table_aborts_everything():
    class BrokenStore(FakeStore):
        def read_switches(self):
            raise RuntimeError("notion down")
    with pytest.raises(runner.CatalogueRunError, match="everything is OFF"):
        run("create", BrokenStore([]), FakeWhapi())


def test_master_kill_switch_stops_the_run():
    store = FakeStore([make_row()])
    result = runner.run_operation("create", store=store, whapi=FakeWhapi(),
                                  masters={"EFPS_WHAPI_LIVE": False, "EFPS_WHAPI_API_ENABLED": True}, sleeper=lambda s: None)
    assert "master kill switch off" in result["lines"][0]
    assert store.updates == []


def test_operation_switch_off_means_nothing_runs():
    store = FakeStore([make_row()], switches={**ALL_SWITCHES, "CREATE": False})
    result = run("create", store, FakeWhapi())
    assert "CREATE switch off" in result["lines"][0]
    assert store.updates == []


# --- CREATE ---

def test_create_writes_product_id_and_meta_channel_only_after_success():
    whapi, store = FakeWhapi(), FakeStore([make_row()], switches={**ALL_SWITCHES, "ASSIGN": False})
    result = run("create", store, whapi)
    assert result["counts"]["ok"] == 1
    page_id, props = store.updates[0]
    assert page_id == "page-1"
    assert "meta_catalog_status" not in props
    assert props["meta_catalog_id"] == "101"
    assert props["live at"] == ["Meta Catalogue"]
    assert props["Pipeline Status"] == "Posted"
    assert any("CREATE EF-2611-AAAA product=101 OK" in line for _, line in store.activity)
    created = whapi.products["101"]
    assert created["name"] == "Semi Furnished 2 BHK - Haralur"
    assert created["description"] == "desc text"  # catalogue_description, never whatsapp_post


def test_create_adopts_existing_product_instead_of_duplicating():
    whapi = FakeWhapi()
    whapi.products["55"] = {"id": "55", "product_retailer_id": "EF-2611-AAAA", "collection_ids": []}
    store = FakeStore([make_row()], switches={**ALL_SWITCHES, "ASSIGN": False})
    result = run("create", store, whapi)
    assert not any(c[0] == "create" for c in whapi.calls)
    assert "ADOPTED" in result["lines"][0]
    assert store.updates[0][1]["meta_catalog_id"] == "55"


def test_create_requires_photos():
    store = FakeStore([make_row(cloudinary_image_urls="")], switches={**ALL_SWITCHES, "ASSIGN": False})
    result = run("create", store, FakeWhapi())
    assert "no photos" in result["lines"][0]
    assert store.updates == []


def test_create_never_chains_assignment():
    # Zeid 24 Nov 3:04 PM: collection assignment is a separate flow; a create
    # run must not assign, even when ASSIGN is on and a collection is mapped.
    sleeps = []
    whapi, store = FakeWhapi(), FakeStore([make_row(meta_catalog_collection_id=COLLECTION)])
    run("create", store, whapi, sleeper=sleeps.append)
    assert not any(c[0] == "assign" for c in whapi.calls)
    assert 30 in sleeps  # 30s spacing between catalogue requests is kept


def test_create_cap_is_10():
    rows = [make_row(page_id=f"p{i}", listing_id=f"EF-2611-{i:04d}") for i in range(12)]
    store = FakeStore(rows, switches={**ALL_SWITCHES, "ASSIGN": False})
    result = run("create", store, FakeWhapi())
    assert result["counts"]["ok"] == 10
    # Real runs: no per-row skip notes (approved 21 Nov, Notion 429 fix), count still tracked.
    assert result["counts"]["skipped"] == 2
    assert sum(1 for l in result["lines"] if "cap 10 reached" in l) == 0
    assert not any("cap 10 reached" in line for _, line in store.activity)


def test_cap_skip_lines_only_in_dry_run():
    rows = [make_row(page_id=f"p{i}", listing_id=f"EF-2611-{i:04d}") for i in range(12)]
    store = FakeStore(rows, switches={**ALL_SWITCHES, "ASSIGN": False, "DRY_RUN": True})
    result = run("create", store, FakeWhapi())
    assert result["counts"]["would"] == 10
    assert result["counts"]["skipped"] == 2
    assert sum(1 for l in result["lines"] if "cap 10 reached" in l) == 2


# --- UPDATE ---

def test_update_patches_only_when_content_differs():
    whapi = FakeWhapi()
    whapi.products["9"] = {"id": "9", "product_retailer_id": "EF-2611-AAAA", "name": "old title",
                           "description": "post text", "price": 40000, "currency": "INR", "images": []}
    row = make_row(**{"live at": ["Meta Catalogue"]}, meta_catalog_id="9")
    result = run("update", FakeStore([row]), whapi)
    assert ("update", "9") in whapi.calls
    assert "updated:" in result["lines"][-1] and "name" in result["lines"][-1]


def test_update_in_sync_logs_and_skips_patch():
    whapi = FakeWhapi()
    whapi.products["9"] = {"id": "9", "product_retailer_id": "EF-2611-AAAA", "name": "Semi Furnished 2 BHK - Haralur",
                           "description": "post text", "price": 40000, "currency": "INR",
                           "images": ["https://img/1.jpg", "https://img/2.jpg"]}
    row = make_row(**{"live at": ["Meta Catalogue"]}, meta_catalog_id="9")
    result = run("update", FakeStore([row]), whapi)
    assert "already in sync" in result["lines"][0]
    assert not any(c[0] == "update" for c in whapi.calls)


def test_update_404_corrects_status():
    whapi = FakeWhapi()
    row = make_row(**{"live at": ["Meta Catalogue"]}, meta_catalog_id="ghost")
    store = FakeStore([row])
    result = run("update", store, whapi)
    assert "removed Meta Catalogue from live at" in result["lines"][0]
    assert store.rows[0]["live at"] == []


# --- DELETE ---

def test_delete_by_exact_id_keeps_red_id_and_clears_channel():
    whapi = FakeWhapi()
    whapi.products["77"] = {"id": "77", "product_retailer_id": "EF-2611-AAAA"}
    row = make_row(Availability="Rented Out", **{"live at": ["Meta Catalogue", "WhatsApp Group"]},
                   meta_catalog_id="77")
    store = FakeStore([row])
    result = run("delete", store, whapi)
    assert ("delete", "77") in whapi.calls
    assert store.rows[0]["live at"] == ["WhatsApp Group"]
    assert store.red_marks == [("page-1", "77")]
    assert any("DELETE EF-2611-AAAA product=77 OK" in line for _, line in store.activity)


def test_delete_triggers_only_on_rented_out_or_on_hold():
    for kw in ({"Availability": "Rented Out"}, {"Availability": "On Hold"}):
        row = make_row(meta_catalog_id="77", **{"live at": ["Meta Catalogue"]}, **kw)
        assert runner.eligible_delete(row), kw
    # A missing tick alone never arms deletion (legacy products predate the tick).
    assert not runner.eligible_delete(make_row(meta_catalog_id="77", post_to_catalogue=False,
                                               **{"live at": ["Meta Catalogue"]}))
    # Available + ticked stays live; no Meta Catalogue channel means nothing to delete.
    assert not runner.eligible_delete(make_row(meta_catalog_id="77"))
    assert not runner.eligible_delete(make_row(meta_catalog_id="77", Availability="Rented Out"))


def test_delete_cap_is_3():
    whapi = FakeWhapi()
    rows = []
    for i in range(5):
        pid = str(500 + i)
        whapi.products[pid] = {"id": pid}
        rows.append(make_row(page_id=f"p{i}", listing_id=f"EF-2611-{i:04d}", Availability="Rented Out",
                             meta_catalog_id=pid, **{"live at": ["Meta Catalogue"]}))
    store = FakeStore(rows)
    result = run("delete", store, whapi)
    assert result["counts"]["ok"] == 3
    # Real runs: no per-row skip notes (approved 21 Nov, Notion 429 fix), count still tracked.
    assert result["counts"]["skipped"] == 2
    assert sum(1 for l in result["lines"] if "cap 3 reached" in l) == 0
    assert not any("cap 3 reached" in line for _, line in store.activity)
    assert len(whapi.products) == 2


def test_delete_cap_skip_lines_only_in_dry_run():
    whapi = FakeWhapi()
    rows = []
    for i in range(5):
        pid = str(500 + i)
        whapi.products[pid] = {"id": pid}
        rows.append(make_row(page_id=f"p{i}", listing_id=f"EF-2611-{i:04d}", Availability="Rented Out",
                             meta_catalog_id=pid, **{"live at": ["Meta Catalogue"]}))
    result = run("delete", FakeStore(rows, switches={**ALL_SWITCHES, "DRY_RUN": True}), whapi)
    assert result["counts"]["would"] == 3
    assert result["counts"]["skipped"] == 2
    assert sum(1 for l in result["lines"] if "cap 3 reached" in l) == 2
    assert len(whapi.products) == 5


def test_delete_404_is_a_correction_not_a_failure():
    row = make_row(Availability="Rented Out", meta_catalog_id="gone", **{"live at": ["Meta Catalogue"]})
    result = run("delete", FakeStore([row]), FakeWhapi())
    assert "404" in result["lines"][0]
    assert result["counts"]["failed"] == 0


# --- ASSIGN ---

def test_assign_uses_formula_id_and_checks_membership_live():
    whapi = FakeWhapi()
    whapi.products["31"] = {"id": "31", "collection_ids": [COLLECTION]}
    row = make_row(meta_catalog_id="31", meta_catalog_collection_id=COLLECTION, **{"live at": ["Meta Catalogue"]})
    result = run("assign", FakeStore([row]), whapi)
    assert "already in collection" in result["lines"][0]
    assert not any(c[0] == "assign" for c in whapi.calls)


def test_assign_hard_stops_on_unknown_collection_id():
    whapi = FakeWhapi()
    whapi.products["31"] = {"id": "31", "collection_ids": []}
    row = make_row(meta_catalog_id="31", meta_catalog_collection_id="999999", **{"live at": ["Meta Catalogue"]})
    result = run("assign", FakeStore([row]), whapi)
    assert "not one of the 4 known IDs" in result["lines"][0]
    assert not any(c[0] == "assign" for c in whapi.calls)


def test_assign_skips_unmapped_bhk_without_guessing():
    row = make_row(meta_catalog_id="31", meta_catalog_collection_id="", **{"live at": ["Meta Catalogue"]})
    result = run("assign", FakeStore([row]), FakeWhapi())
    assert "unmapped BHK" in result["lines"][0]


# --- 429 handling ---

def test_one_429_retries_once_then_succeeds():
    sleeps = []
    whapi = FakeWhapi()
    whapi.fail_next = RuntimeError("WhAPI HTTP 429: Too many requests")
    store = FakeStore([make_row()], switches={**ALL_SWITCHES, "ASSIGN": False})
    result = run("create", store, whapi, sleeper=sleeps.append)
    assert 30 in sleeps
    assert result["counts"]["ok"] == 1


def test_second_429_defers_the_row():
    whapi = FakeWhapi()
    whapi.fail_next = RuntimeError("WhAPI HTTP 429")
    store = FakeStore([make_row()], switches={**ALL_SWITCHES, "ASSIGN": False})
    def always_429(*a, **k):
        raise RuntimeError("WhAPI HTTP 429")
    whapi.find_product_by_retailer_id = always_429
    result = run("create", store, whapi, sleeper=lambda s: None)
    assert result["counts"]["failed"] == 1
    assert "429" in result["lines"][0]
    assert store.updates == []  # row stays eligible for the next run


# --- DRY RUN ---

def test_dry_run_decides_everything_and_writes_nothing():
    whapi = FakeWhapi()
    whapi.products["77"] = {"id": "77"}
    rows = [
        make_row(page_id="c1", listing_id="EF-CREATE"),
        make_row(page_id="d1", listing_id="EF-DELETE", Availability="Rented Out", meta_catalog_id="77", **{"live at": ["Meta Catalogue"]}),
    ]
    store = FakeStore(rows, switches={**ALL_SWITCHES, "DRY_RUN": True})
    create = run("create", store, whapi)
    delete = run("delete", store, whapi)
    assert any("WOULD" in l for l in create["lines"])
    assert any("WOULD" in l for l in delete["lines"])
    assert store.updates == [] and store.activity == [] and store.red_marks == [] and store.panel == []
    assert "77" in whapi.products  # nothing deleted


# --- RECONCILE (report only) ---

def test_reconcile_reports_drift_and_orphans_without_touching_anything():
    whapi = FakeWhapi()
    whapi.products["1"] = {"id": "1", "product_retailer_id": "EF-ORPHAN"}
    rows = [
        make_row(listing_id="EF-MISSING", **{"live at": ["Meta Catalogue"]}, meta_catalog_id="x"),
        make_row(page_id="r1", listing_id="EF-LEFTOVER", Availability="Rented Out", meta_catalog_id="1x", **{"live at": ["Meta Catalogue"]}),
    ]
    whapi.products["1x"] = {"id": "1x", "product_retailer_id": "EF-LEFTOVER"}
    store = FakeStore(rows)
    result = run("reconcile", store, whapi)
    text = "\n".join(result["lines"])
    assert "product missing on WhatsApp" in text
    assert "leftover product for a Rented Out/On Hold row" in text
    assert "orphan on WhatsApp" in text
    assert store.review_entries and store.review_entries[0]["type"] == "Orphan product"
    assert store.updates == [] and not any(c[0] in {"create", "delete", "update", "assign"} for c in whapi.calls)


# --- review queue decisions execute first ---

def test_queued_decisions_execute_before_the_normal_pass():
    whapi = FakeWhapi()
    whapi.products["88"] = {"id": "88", "product_retailer_id": "EF-2611-AAAA"}
    store = FakeStore([make_row()], switches={**ALL_SWITCHES, "ASSIGN": False})
    store.decisions = [{"id": "q1", "operation": "create", "decision": "Reprocess",
                        "row": make_row(page_id="q-page", listing_id="EF-2611-AAAA")}]
    result = run("create", store, whapi)
    assert store.review_done == [("q1", "executed via create")]
    assert any("ADOPTED" in l for l in result["lines"])


def test_reconcile_dry_run_queues_nothing():
    whapi = FakeWhapi()
    whapi.products["9"] = {"id": "9", "product_retailer_id": "EF-ORPHAN"}
    store = FakeStore([make_row()], switches={**ALL_SWITCHES, "DRY_RUN": True})
    result = run("reconcile", store, whapi)
    assert any("would queue for review" in l for l in result["lines"])
    assert store.review_entries == [] and store.updates == [] and store.activity == [] and store.panel == []
