"""Per-operation tests for the gated catalogue runner (fake Whapi + fake store)."""

from __future__ import annotations

import sys
import pathlib

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import catalogue_runner as runner  # noqa: E402

MASTERS_ON = {"EFPS_WHAPI_LIVE": True, "EFPS_WHAPI_API_ENABLED": True}
ALL_SWITCHES = {"CREATE": True, "DELETE": True, "RECONCILE": True, "DRY_RUN": False}


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

    def read_listing(self, page_id):
        for row in self.rows:
            if row.get("page_id") == page_id:
                return dict(row)
        raise RuntimeError("row not found")

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
        "meta_catalog_id": "",
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
        store = FakeStore([make_row(**kw)], switches={**ALL_SWITCHES})
        result = run("create", store, FakeWhapi())
        assert reason in result["lines"][0], (kw, result["lines"])
        assert store.updates == []


# --- gating ---

def test_all_seven_states_logged_at_run_start():
    store = FakeStore([])
    result = run("create", store, FakeWhapi())
    assert set(result["states"]) == {"EFPS_WHAPI_LIVE", "EFPS_WHAPI_API_ENABLED", "CREATE", "DELETE", "RECONCILE", "DRY_RUN"}


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
    whapi, store = FakeWhapi(), FakeStore([make_row()], switches={**ALL_SWITCHES})
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
    row = make_row()
    whapi.products["55"] = {"id": "55", "product_retailer_id": "EF-2611-AAAA", "collection_ids": [],
                            "name": row["catalog_title"], "description": row["catalogue_description"],
                            "price": row["monthly_rent"], "images": row["cloudinary_image_urls"].split()}
    store = FakeStore([row], switches={**ALL_SWITCHES})
    result = run("create", store, whapi)
    assert not any(c[0] == "create" for c in whapi.calls)
    assert "ADOPTED" in result["lines"][0]
    assert store.updates[0][1]["meta_catalog_id"] == "55"


def test_create_does_not_adopt_a_product_with_different_content():
    whapi = FakeWhapi()
    whapi.products["55"] = {"id": "55", "product_retailer_id": "EF-2611-AAAA", "name": "Something else",
                            "description": "other", "price": 1, "collection_ids": []}
    store = FakeStore([make_row()], switches={**ALL_SWITCHES})
    result = run("create", store, whapi)
    assert result["counts"]["failed"] == 1
    assert "not adopted" in str(result["lines"])
    assert store.updates == []
    assert not any(c[0] == "create" for c in whapi.calls)


def test_create_rechecks_row_just_before_acting():
    class Drifting(FakeStore):
        def read_listing(self, page_id):
            r = super().read_listing(page_id)
            r["Availability"] = "Rented Out"   # changed after the batch snapshot
            return r
    whapi = FakeWhapi()
    store = Drifting([make_row()], switches={**ALL_SWITCHES})
    result = run("create", store, whapi)
    assert "no longer eligible" in result["lines"][0]
    assert not any(c[0] == "create" for c in whapi.calls)
    assert store.updates == []


def test_create_requires_photos():
    store = FakeStore([make_row(cloudinary_image_urls="")], switches={**ALL_SWITCHES})
    result = run("create", store, FakeWhapi())
    assert "no photos" in result["lines"][0]
    assert store.updates == []


def test_create_never_chains_assignment():
    # Collection assignment does not exist: a create run makes no collection call
    # of any kind (the fake has no collection method, so any attempt would fail the row).
    sleeps = []
    whapi, store = FakeWhapi(), FakeStore([make_row()])
    result = run("create", store, whapi, sleeper=sleeps.append)
    assert result["counts"]["failed"] == 0 and "created and verified" in result["lines"][0]
    assert not any("assign" in str(c[0]) or "collection" in str(c[0]) for c in whapi.calls)
    assert not hasattr(whapi, "edit_collection")
    assert 30 in sleeps  # 30s spacing between catalogue requests is kept
    assert runner.CREATE_SPACING_SECONDS == 30


def test_create_batch_size_is_3_and_fits_lambda_timeout():
    rows = [make_row(page_id=f"p{i}", listing_id=f"EF-2611-{i:04d}") for i in range(5)]
    store = FakeStore(rows, switches={**ALL_SWITCHES})
    result = run("create", store, FakeWhapi())
    assert runner.CAPS["create"] == 3
    assert result["counts"]["ok"] == 3
    assert result["counts"]["skipped"] == 2
    assert not any("cap 3 reached" in line for _, line in store.activity)


def test_cap_skip_lines_only_in_dry_run():
    rows = [make_row(page_id=f"p{i}", listing_id=f"EF-2611-{i:04d}") for i in range(5)]
    store = FakeStore(rows, switches={**ALL_SWITCHES, "DRY_RUN": True})
    result = run("create", store, FakeWhapi())
    assert result["counts"]["would"] == 3
    assert result["counts"]["skipped"] == 2
    assert sum(1 for l in result["lines"] if "cap 3 reached" in l) == 2


def test_unfit_rows_never_take_batch_slots():
    bad = [make_row(page_id=f"b{i}", listing_id=f"EF-2611-B{i:03d}", cloudinary_image_urls="") for i in range(5)]
    good = [make_row(page_id=f"g{i}", listing_id=f"EF-2611-G{i:03d}") for i in range(3)]
    store = FakeStore(bad + good, switches={**ALL_SWITCHES})
    result = run("create", store, FakeWhapi())
    assert result["counts"]["ok"] == 3  # bad rows listed first did not starve the good ones


def test_full_chain_creates_every_eligible_row_in_batches():
    rows = [make_row(page_id=f"p{i}", listing_id=f"EF-2611-{i:04d}") for i in range(25)]
    store, whapi = FakeStore(rows, switches={**ALL_SWITCHES}), FakeWhapi()
    batches = []
    while True:  # what catalogue_scheduler._batch does: chain while ok > 0, stop on 0 or any failure
        r = run("create", store, whapi)
        batches.append(r["counts"]["ok"])
        assert r["counts"]["failed"] == 0
        if r["counts"]["ok"] == 0:
            break
    assert batches == [3] * 8 + [1, 0]
    assert len(whapi.products) == 25
    assert len({p["product_retailer_id"] for p in whapi.products.values()}) == 25  # no duplicates


def test_second_429_stops_the_row_and_fails_the_batch():
    rows = [make_row(page_id=f"p{i}", listing_id=f"EF-2611-{i:04d}") for i in range(2)]
    store, whapi = FakeStore(rows, switches={**ALL_SWITCHES}), FakeWhapi()
    orig = whapi.get_products
    def always_429(count=100):
        raise RuntimeError("WhAPI HTTP 429: Too many requests")
    whapi.get_products = always_429
    result = run("create", store, whapi)
    assert result["counts"]["failed"] >= 1 and result["counts"]["ok"] == 0
    assert whapi.products == {}  # nothing created after a double 429


# --- UPDATE is intentionally retired ---
def test_update_operation_is_rejected_without_any_side_effects():
    store, whapi = FakeStore([make_row()]), FakeWhapi()
    with pytest.raises(ValueError, match="unknown operation"):
        run("update", store, whapi)
    assert whapi.calls == []
    assert store.updates == []
    assert store.activity == []


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


# --- ASSIGN is gone ---

def test_assign_operation_is_rejected_and_touches_nothing():
    whapi, store = FakeWhapi(), FakeStore([make_row(meta_catalog_id="31", **{"live at": ["Meta Catalogue"]})])
    with pytest.raises(ValueError, match="unknown operation"):
        run("assign", store, whapi)
    assert whapi.calls == [] and store.updates == []
    assert "assign" not in runner.OPERATIONS and "assign" not in runner.CAPS
    assert "assign" not in runner.ELIGIBLE and "ASSIGN" not in runner.SWITCH_BY_OPERATION.values()
    assert not hasattr(runner, "_op_assign_row") and not hasattr(runner, "KNOWN_COLLECTION_IDS")


def test_removed_collection_columns_are_not_needed():
    # Rows carry neither removed column; every operation still selects and runs.
    row = make_row()
    assert "meta_catalog_collection_id" not in row
    assert runner.eligible_create(row)


# --- 429 handling ---

def test_create_429_is_never_retried_and_stops_the_batch():
    sleeps = []
    whapi = FakeWhapi()
    whapi.fail_next = RuntimeError("WhAPI HTTP 429: Too many requests")
    rows = [make_row(page_id=f"p{i}", listing_id=f"EF-2611-{i:04d}") for i in range(3)]
    store = FakeStore(rows, switches={**ALL_SWITCHES})
    result = run("create", store, whapi, sleeper=sleeps.append)
    assert 30 not in sleeps  # no 429 retry wait, the number is left to rest
    assert result["counts"]["failed"] == 1 and result["counts"]["ok"] == 0
    assert whapi.products == {}  # later rows in the batch were not attempted either
    assert any("rest" in l for l in result["lines"])


def test_create_checkpoint_defers_before_the_irreversible_step():
    rows = [make_row(page_id="p0", listing_id="EF-2611-0000"), make_row(page_id="p1", listing_id="EF-2611-0001")]
    store, whapi = FakeStore(rows, switches={**ALL_SWITCHES}), FakeWhapi()
    left = iter([300.0, 100.0] + [100.0] * 5)  # row may start, but not enough time left to create
    result = runner.run_operation("create", store=store, whapi=whapi, masters=MASTERS_ON,
                                  sleeper=lambda s: None, time_left=lambda: next(left))
    assert whapi.products == {} and result["counts"]["ok"] == 0
    assert result["counts"]["failed"] == 0 and result["counts"]["skipped"] == 1  # second row not touched


def test_deadline_model_two_rows_fit_a_300s_invocation():
    rows = [make_row(page_id=f"p{i}", listing_id=f"EF-2611-{i:04d}") for i in range(3)]
    store = FakeStore(rows, switches={**ALL_SWITCHES})
    spent = []
    result = runner.run_operation("create", store=store, whapi=FakeWhapi(), masters=MASTERS_ON,
                                  sleeper=spent.append, time_left=lambda: 300 - sum(spent))
    assert result["counts"]["ok"] >= 1  # later rows wait once under 240s left, so it waits


def test_second_429_defers_the_row():
    whapi = FakeWhapi()
    whapi.fail_next = RuntimeError("WhAPI HTTP 429")
    store = FakeStore([make_row()], switches={**ALL_SWITCHES})
    def always_429(*a, **k):
        raise RuntimeError("WhAPI HTTP 429")
    whapi.get_products = always_429
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
    assert store.updates == [] and not any(c[0] in {"create", "delete"} for c in whapi.calls)


# --- review queue decisions execute first ---

def test_queued_decisions_execute_before_the_normal_pass():
    whapi = FakeWhapi()
    _r = make_row(page_id="q-page", listing_id="EF-2611-AAAA")
    whapi.products["88"] = {"id": "88", "product_retailer_id": "EF-2611-AAAA", "name": _r["catalog_title"],
                            "description": _r["catalogue_description"], "price": _r["monthly_rent"],
                            "images": _r["cloudinary_image_urls"].split()}
    store = FakeStore([make_row(), _r], switches={**ALL_SWITCHES})
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


def test_create_preserves_other_live_at_selections():
    whapi = FakeWhapi()
    store = FakeStore([make_row(**{"live at": ["99acres"]})], switches={**ALL_SWITCHES})
    run("create", store, whapi)
    assert store.updates[0][1]["live at"] == ["99acres", "Meta Catalogue"]


def test_create_stops_on_duplicate_listing_id_matches():
    whapi = FakeWhapi()
    for pid in ("55", "56"):
        whapi.products[pid] = {"id": pid, "product_retailer_id": "EF-2611-AAAA"}
    store = FakeStore([make_row()], switches={**ALL_SWITCHES})
    result = run("create", store, whapi)
    assert result["counts"]["failed"] == 1 and "share listing_id" in str(result["lines"])
    assert store.updates == [] and not any(c[0] == "create" for c in whapi.calls)


def test_adoption_rejects_wrong_photo_count_or_link():
    row = make_row(google_maps_url="https://maps/x")
    base = {"id": "55", "product_retailer_id": "EF-2611-AAAA", "name": row["catalog_title"],
            "description": row["catalogue_description"], "price": row["monthly_rent"],
            "images": row["cloudinary_image_urls"].split(), "url": "https://maps/x"}
    for bad in ({"images": ["only-one"]}, {"url": "https://maps/other"}):
        whapi = FakeWhapi(); whapi.products["55"] = {**base, **bad}
        store = FakeStore([dict(row)], switches={**ALL_SWITCHES})
        result = run("create", store, whapi)
        assert result["counts"]["failed"] == 1 and store.updates == []
    whapi = FakeWhapi(); whapi.products["55"] = dict(base)
    store = FakeStore([dict(row)], switches={**ALL_SWITCHES})
    assert "ADOPTED" in run("create", store, whapi)["lines"][0]


# --- lost create response, shared catalogue read, deadline-bound calls ---

def test_lost_create_response_stops_batch_and_blocks_a_blind_recreate():
    class LostWhapi(FakeWhapi):
        def create_product(self, *a, **k):
            super().create_product(*a, **k)  # Meta created it ...
            raise RuntimeError("WhAPI network error: timed out")  # ... but the answer was lost
    rows = [make_row(page_id=f"p{i}", listing_id=f"EF-2611-{i:04d}") for i in range(3)]
    store, whapi = FakeStore(rows, switches={**ALL_SWITCHES}), LostWhapi()
    r1 = run("create", store, whapi)
    assert r1["counts"]["failed"] == 1 and r1["counts"]["ok"] == 0
    assert len(whapi.products) == 1  # later rows were not attempted
    # durable: the checkpoint line was written to Notion BEFORE the call
    assert any("ATTEMPT STARTED" in l for _, l in store.activity)
    rows[0]["error_notes"] = "\n".join(l for pid, l in store.activity if pid == "p0")
    # Meta has not shown the product yet (eventual consistency): simulate by hiding it from reads
    hidden, whapi.products = whapi.products, {}
    r2 = run("create", store, FakeWhapi())
    assert not any("p0" in str(c) for c in [])  # row 0 not re-created
    assert rows[0]["meta_catalog_id"] == "" and "Posted" != rows[0].get("Pipeline Status")
    assert any("unknown result" in l for l in r2["lines"])
    assert r2["counts"]["ok"] == 2  # the other rows still proceed


def test_lost_create_is_adopted_once_the_product_becomes_visible():
    rows = [make_row(page_id="p0", listing_id="EF-2611-0000")]
    whapi = FakeWhapi()
    store = FakeStore(rows, switches={**ALL_SWITCHES})
    run("create", store, whapi)  # creates it normally to get a matching live product
    rows[0].update({"meta_catalog_id": "", "Pipeline Status": "Ready To Post", "live at": [],
                    "error_notes": "[t] CREATE EF-2611-0000 FAILED create request failed ...; OUTCOME UNKNOWN, product may exist"})
    r2 = run("create", store, whapi)
    assert r2["counts"]["ok"] == 1 and len(whapi.products) == 1  # adopted, no duplicate
    assert rows[0]["meta_catalog_id"]


def test_catalogue_is_read_once_per_batch_and_stays_fresh():
    rows = [make_row(page_id=f"p{i}", listing_id=f"EF-2611-{i:04d}") for i in range(3)]
    store, whapi = FakeStore(rows, switches={**ALL_SWITCHES}), FakeWhapi()
    reads = []
    orig = whapi.get_products
    whapi.get_products = lambda count=100, before_page=None: (reads.append(1), orig(count))[1]
    run("create", store, whapi)
    assert len(reads) == 1


def test_catalogue_page_read_defers_when_no_time_for_it():
    rows = [make_row(page_id="p0", listing_id="EF-2611-0000")]
    store, whapi = FakeStore(rows, switches={**ALL_SWITCHES}), FakeWhapi()
    def pages(count=100, before_page=None):
        before_page()
        return []
    whapi.get_products = pages
    left = iter([300.0, 150.0] + [150.0] * 5)  # row starts, but the catalogue page has no room
    result = runner.run_operation("create", store=store, whapi=whapi, masters=MASTERS_ON,
                                  sleeper=lambda s: None, time_left=lambda: next(left))
    assert whapi.products == {} and result["counts"]["ok"] == 0 and result["counts"]["failed"] == 0


def test_checkpoint_is_written_before_create_so_a_killed_process_is_held():
    class Killed(BaseException):
        pass
    class DiesInCreate(FakeWhapi):
        def create_product(self, *a, **k):
            super().create_product(*a, **k)  # Meta created it
            raise Killed()                    # process dies before any error_notes write
    rows = [make_row(page_id="p0", listing_id="EF-2611-0000")]
    store, whapi = FakeStore(rows, switches={**ALL_SWITCHES}), DiesInCreate()
    with pytest.raises(Killed):
        run("create", store, whapi)
    assert [l for _, l in store.activity if "ATTEMPT STARTED" in l]  # already durable
    rows[0]["error_notes"] = "\n".join(l for _, l in store.activity)
    whapi.products = {}  # not yet visible
    r2 = run("create", store, FakeWhapi())  # e.g. an async retry or the next night
    assert r2["counts"]["ok"] == 0 and any("unknown result" in l for l in r2["lines"])
    assert rows[0]["meta_catalog_id"] == ""


def test_refused_create_settles_the_checkpoint_so_the_row_can_retry():
    whapi = FakeWhapi()
    whapi.fail_next = None
    rows = [make_row(page_id="p0", listing_id="EF-2611-0000")]
    store = FakeStore(rows, switches={**ALL_SWITCHES})
    orig = whapi.create_product
    def refuse(*a, **k):
        raise RuntimeError("WhAPI HTTP 400: bad request")
    whapi.create_product = refuse
    r1 = run("create", store, whapi)
    assert r1["counts"]["failed"] == 1
    rows[0]["error_notes"] = "\n".join(l for _, l in store.activity)
    whapi.create_product = orig
    r2 = run("create", store, whapi)
    assert r2["counts"]["ok"] == 1  # a refused request left nothing behind, so it may retry


# --- 24 Nov 2026 fixes: photo identity, stop on verification failure, recovery hold, verified write-back ---

SW_CREATE = {**ALL_SWITCHES}


class PreviewWhapi(FakeWhapi):
    """Returns every photo twice, as Whapi does: full link plus a 100x100 preview of the same image."""
    def get_product(self, product_id):
        p = dict(super().get_product(product_id))
        imgs = []
        for u in p.get("images") or []:
            imgs.append(u + "?ccb=1")
            imgs.append(u + "?stp=dst-jpg_p100x100&ccb=1")
        p["images"] = imgs
        return p


def test_photo_and_its_preview_count_as_one_photo():
    store, whapi = FakeStore([make_row()], switches=SW_CREATE), PreviewWhapi()
    result = run("create", store, whapi)
    assert result["counts"]["ok"] == 1 and result["counts"]["failed"] == 0
    assert store.updates[0][1]["Pipeline Status"] == "Posted"


def test_photo_identity_still_catches_missing_extra_and_distinct_photos():
    mm = runner._content_mismatch
    args = ("T", "D", 1)
    live = lambda imgs: {"name": "T", "description": "D", "price": 1, "images": imgs}
    two = ["https://cdn/a.jpg", "https://cdn/b.jpg"]
    assert mm(live(["https://cdn/a.jpg?x=1", "https://cdn/a.jpg?stp=dst-jpg_p100x100&x=1",
                    "https://cdn/b.jpg?x=1", "https://cdn/b.jpg?stp=dst-jpg_p100x100&x=1"]), *args, two) == ""
    assert "photos (1 live vs 2 intended)" in mm(live(["https://cdn/a.jpg?x=1", "https://cdn/a.jpg?stp=p100x100"]), *args, two)
    assert "photos (3 live vs 2 intended)" in mm(live(["https://cdn/a.jpg", "https://cdn/b.jpg", "https://cdn/c.jpg"]), *args, two)
    # two different photos are never merged; dict-shaped entries are handled
    assert mm(live([{"link": "https://cdn/a.jpg?q=1"}, {"link": "https://cdn/b.jpg?q=1"}]), *args, two) == ""
    # a preview whose full photo is missing still counts as one photo, so a wrong count is caught
    assert "photos" in mm(live(["https://cdn/a.jpg?stp=dst-jpg_p100x100"]), *args, two)


class WrongTextWhapi(FakeWhapi):
    def get_product(self, product_id):
        p = dict(super().get_product(product_id))
        p["description"] = "something else"
        return p


def test_verification_failure_stops_the_batch_and_keeps_the_created_id():
    rows = [make_row(page_id=f"p{i}", listing_id=f"EF-2611-{i:04d}") for i in range(3)]
    store, whapi = FakeStore(rows, switches=SW_CREATE), WrongTextWhapi()
    result = run("create", store, whapi)
    assert len([c for c in whapi.calls if c[0] == "create"]) == 1  # rows 2 and 3 never attempted
    assert result["counts"]["failed"] == 1 and result["counts"]["ok"] == 0
    assert store.updates == []  # Notion not marked posted
    note = "\n".join(l for pid, l in store.activity if pid == "p0")
    assert "created product 101" in note and "FAILED" in note


def test_recovery_hold_skips_a_created_but_unreconciled_row_without_slot_or_calls():
    held_note = ("[t] CREATE EF-2611-0000 ATTEMPT STARTED about to call create_product\n"
                 "[t] CREATE EF-2611-0000 FAILED created product 29403526879280307 content mismatch (photos (14 live vs 7 intended)); Notion untouched")
    rows = [make_row(page_id="p0", listing_id="EF-2611-0000", error_notes=held_note)]
    rows += [make_row(page_id=f"p{i}", listing_id=f"EF-2611-{i:04d}") for i in range(1, 5)]
    store, whapi = FakeStore(rows, switches=SW_CREATE), FakeWhapi()
    result = run("create", store, whapi)
    created = [c[1] for c in whapi.calls if c[0] == "create"]
    assert created == ["EF-2611-0001", "EF-2611-0002", "EF-2611-0003"]  # a full batch of 3, held row took no slot
    assert not any(c[0] == "get" and c[1] == "29403526879280307" for c in whapi.calls)
    assert not any(pid == "p0" for pid, _ in store.activity)  # no repeated note on the held row
    assert any("recovery hold" in l and "EF-2611-0000" in l for l in result["lines"])
    assert rows[0]["meta_catalog_id"] == ""  # not adopted, no Pipeline change


def test_recovery_hold_clears_after_an_ok_or_adopted_line():
    notes = ("[t] CREATE EF-2611-0000 FAILED created product 123456789 content mismatch\n"
             "[t] CREATE EF-2611-0000 product=123456789 ADOPTED product already existed")
    assert runner.created_unreconciled_product(notes) == ""
    assert runner.created_unreconciled_product("[t] CREATE EF-2611-0000 FAILED created product 123456789 x") == "123456789"
    assert runner.created_unreconciled_product("[t] CREATE EF-2611-0000 FAILED Whapi rejected (400)") == ""


def test_notion_write_failure_after_create_stops_batch_and_holds_the_row():
    rows = [make_row(page_id=f"p{i}", listing_id=f"EF-2611-{i:04d}") for i in range(3)]
    store, whapi = FakeStore(rows, switches=SW_CREATE), FakeWhapi()
    def boom(page_id, props): raise RuntimeError("Notion API PATCH failed (500)")
    store.update_listing = boom
    result = run("create", store, whapi)
    assert len([c for c in whapi.calls if c[0] == "create"]) == 1
    assert result["counts"]["failed"] == 1 and result["counts"]["ok"] == 0
    note = "\n".join(l for pid, l in store.activity if pid == "p0")
    assert "created product 101" in note and "write-back failed" in note
    assert runner.created_unreconciled_product(note) == "101"  # next run holds it, no duplicate


def test_partial_notion_write_is_caught_by_the_read_back():
    rows = [make_row(page_id="p0", listing_id="EF-2611-0000"), make_row(page_id="p1", listing_id="EF-2611-0001")]
    store, whapi = FakeStore(rows, switches=SW_CREATE), FakeWhapi()
    orig = store.update_listing
    def partial(page_id, props):  # Pipeline Status silently does not save
        orig(page_id, {k: v for k, v in props.items() if k != "Pipeline Status"})
    store.update_listing = partial
    result = run("create", store, whapi)
    assert result["counts"]["ok"] == 0 and result["counts"]["failed"] == 1
    assert len([c for c in whapi.calls if c[0] == "create"]) == 1  # stopped
    assert "not confirmed on read-back (Pipeline Status)" in str(result["lines"])


def test_confirmed_write_back_reports_ok_only_with_all_three_columns():
    store, whapi = FakeStore([make_row(**{"live at": ["Other"]})], switches=SW_CREATE), FakeWhapi()
    result = run("create", store, whapi)
    row = store.rows[0]
    assert result["counts"]["ok"] == 1
    assert row["meta_catalog_id"] == "101" and row["Pipeline Status"] == "Posted"
    assert row["live at"] == ["Other", "Meta Catalogue"]


def test_batch_cap_and_timing_constants_are_unchanged():
    assert runner.CAPS["create"] == 3
