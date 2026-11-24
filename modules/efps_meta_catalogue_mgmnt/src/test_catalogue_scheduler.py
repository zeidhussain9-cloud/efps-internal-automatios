"""Tests for the Tuesday scheduled cleanup orchestrator (approved 21 Nov)."""
from __future__ import annotations

import os
import sys
import unittest
from datetime import datetime, timezone
from unittest import mock

sys.path.insert(0, os.path.dirname(__file__))

import catalogue_scheduler as cs


class FakeLambda:
    def __init__(self, flag="false"):
        self.flag = flag
        self.invocations = []
        self.updates = []
        self.fail_update = False

    def get_function_configuration(self, FunctionName):
        return {"Environment": {"Variables": {cs.CATALOG_WRITE_FLAG: self.flag}},
                "LastUpdateStatus": "Successful"}

    def update_function_configuration(self, FunctionName, Environment):
        if self.fail_update:
            raise RuntimeError("iam denied")
        self.updates.append(Environment["Variables"][cs.CATALOG_WRITE_FLAG])
        self.flag = Environment["Variables"][cs.CATALOG_WRITE_FLAG]

    def invoke(self, FunctionName, InvocationType, Payload):
        import json
        self.invocations.append(json.loads(Payload.decode()))


class FakeStore:
    def __init__(self, dry_run=True):
        self.dry_run = dry_run
        self.log_entries = []
        self.requests = []
        self.create_on = False

    def _query_all(self, db):
        return [{"id": "dryrun-page", "properties": {"Name": {"title": [{"plain_text": "DRY_RUN"}]}}},
                {"id": "create-page", "properties": {"Name": {"title": [{"plain_text": "CREATE"}]}}}]

    def request(self, method, path, payload=None):
        self.requests.append((method, path, payload))
        if path == "pages/create-page":
            self.create_on = payload["properties"]["Enabled"]["checkbox"]
        elif path.startswith("pages/"):
            self.dry_run = payload["properties"]["Enabled"]["checkbox"]
        if path.startswith("blocks/"):
            self.log_entries.append(payload)
        return {}


class Ctx:
    invoked_function_arn = "arn:aws:lambda:ap-southeast-2:123:function:efps-notion-intake"


def run_delete_result(ok=0, failed=0, skipped=0, would=0, dry=False, lines=None):
    return {"counts": {"ok": ok, "failed": failed, "skipped": skipped, "would": would},
            "dry_run": dry, "lines": lines or []}


TUE_PM_IST = datetime(2026, 11, 24, 16, 0, tzinfo=timezone.utc)  # 9:30 PM IST, inside the creation window
TUE_AM_IST = datetime(2026, 11, 24, 3, 45, tzinfo=timezone.utc)  # Tuesday 9:15 IST
WED_AM_IST = datetime(2026, 11, 25, 4, 35, tzinfo=timezone.utc)  # Wednesday 10:05 IST


def base_env(flag):
    return mock.patch.dict(os.environ, {cs.CATALOG_WRITE_FLAG: flag})


class BeginTests(unittest.TestCase):
    def test_begin_flips_flags_and_chains_first_batch(self):
        lam, store = FakeLambda("false"), FakeStore()
        with base_env("false"):
            out = cs.handle_schedule({"step": "begin"}, Ctx(), notion_token="t",
                                     lam=lam, store=store, run_delete=lambda: {}, sleep=lambda s: None)
        self.assertEqual(out["status"], "started")
        self.assertEqual(lam.updates, ["true"])
        self.assertFalse(store.dry_run)
        self.assertEqual(lam.invocations[0]["step"], "batch")
        self.assertEqual(lam.invocations[0]["batch"], 1)
        self.assertTrue(lam.invocations[0]["run_id"].startswith("tue-"))

    def test_begin_aborts_if_gate_already_open(self):
        lam, store = FakeLambda("true"), FakeStore()
        with base_env("true"):
            out = cs.handle_schedule({"step": "begin"}, Ctx(), notion_token="t",
                                     lam=lam, store=store, run_delete=lambda: {}, sleep=lambda s: None)
        self.assertEqual(out["status"], "aborted")
        self.assertEqual(lam.updates, [])
        self.assertEqual(lam.invocations, [])
        self.assertTrue(store.dry_run)


class BatchTests(unittest.TestCase):
    def event(self, **kw):
        base = {"step": "batch", "run_id": "tue-x", "batch": 1,
                "totals": {"ok": 0, "failed": 0, "skipped": 0}, "deleted": [], "failures": []}
        base.update(kw)
        return base

    def test_ok_batch_chains_next_with_totals(self):
        lam, store = FakeLambda("true"), FakeStore(dry_run=False)
        res = run_delete_result(ok=3, skipped=57, lines=["[2026-11-24 03:30:00Z] DELETE EF-1 product=p1 OK deleted"])
        with base_env("true"):
            out = cs.handle_schedule(self.event(), Ctx(), notion_token="t",
                                     lam=lam, store=store, run_delete=lambda: res, sleep=lambda s: None)
        self.assertEqual(out["status"], "chained")
        nxt = lam.invocations[0]
        self.assertEqual(nxt["batch"], 2)
        self.assertEqual(nxt["totals"]["ok"], 3)
        self.assertEqual(nxt["totals"]["skipped"], 57)
        self.assertEqual(nxt["deleted"], ["EF-1"])

    def test_zero_eligible_finalizes_success_and_restores(self):
        lam, store = FakeLambda("true"), FakeStore(dry_run=False)
        res = run_delete_result(ok=0, lines=["[2026-11-24 03:30:00Z] DELETE - SKIPPED no eligible rows"])
        with base_env("true"):
            out = cs.handle_schedule(self.event(batch=2, totals={"ok": 3, "failed": 0, "skipped": 0},
                                                deleted=["EF-1"]), Ctx(), notion_token="t",
                                     lam=lam, store=store, run_delete=lambda: res, sleep=lambda s: None)
        self.assertEqual(out["status"], "completed")
        self.assertEqual(lam.updates, ["false"])
        self.assertTrue(store.dry_run)
        self.assertEqual(lam.invocations, [])
        self.assertTrue(store.log_entries, "decision log entry written")
        text = str(store.log_entries[0])
        self.assertIn("COMPLETED", text)
        self.assertIn("EF-1", text)

    def test_failed_batch_stops_safe_no_rerun(self):
        lam, store = FakeLambda("true"), FakeStore(dry_run=False)
        res = run_delete_result(ok=2, failed=1, lines=["[2026-11-24 03:30:00Z] DELETE EF-1 product=p1 OK deleted",
                                                       "[2026-11-24 03:30:00Z] DELETE EF-2 product=p2 FAILED boom"])
        with base_env("true"):
            out = cs.handle_schedule(self.event(), Ctx(), notion_token="t",
                                     lam=lam, store=store, run_delete=lambda: res, sleep=lambda s: None)
        self.assertEqual(out["status"], "failed")
        self.assertIn("no auto-rerun", out["error"])
        self.assertEqual(lam.invocations, [])
        self.assertEqual(lam.updates, ["false"])
        self.assertTrue(store.dry_run)
        self.assertIn("boom", str(store.log_entries[0]))

    def test_dry_run_still_on_aborts(self):
        lam, store = FakeLambda("true"), FakeStore(dry_run=False)
        res = run_delete_result(would=3, dry=True)
        with base_env("true"):
            out = cs.handle_schedule(self.event(), Ctx(), notion_token="t",
                                     lam=lam, store=store, run_delete=lambda: res, sleep=lambda s: None)
        self.assertEqual(out["status"], "failed")
        self.assertIn("DRY_RUN", out["error"])
        self.assertEqual(lam.invocations, [])

    def test_flag_off_midrun_stops_safe(self):
        lam, store = FakeLambda("false"), FakeStore()
        with base_env("false"):
            out = cs.handle_schedule(self.event(), Ctx(), notion_token="t",
                                     lam=lam, store=store, run_delete=lambda: 1 / 0, sleep=lambda s: None)
        self.assertEqual(out["status"], "failed")
        self.assertIn("OFF mid-run", out["error"])

    def test_raised_batch_stops_safe_no_rerun(self):
        lam, store = FakeLambda("true"), FakeStore(dry_run=False)
        def boom():
            raise RuntimeError("whapi exploded")
        with base_env("true"):
            out = cs.handle_schedule(self.event(), Ctx(), notion_token="t",
                                     lam=lam, store=store, run_delete=boom, sleep=lambda s: None)
        self.assertEqual(out["status"], "failed")
        self.assertIn("whapi exploded", out["error"])
        self.assertEqual(lam.invocations, [])
        self.assertEqual(lam.updates, ["false"])
        self.assertTrue(store.dry_run)

    def test_batch_cap_finalizes_with_error(self):
        lam, store = FakeLambda("true"), FakeStore(dry_run=False)
        res = run_delete_result(ok=3, lines=["[2026-11-24 03:30:00Z] DELETE EF-9 product=p9 OK deleted"])
        with base_env("true"):
            out = cs.handle_schedule(self.event(batch=cs.MAX_BATCHES), Ctx(), notion_token="t",
                                     lam=lam, store=store, run_delete=lambda: res, sleep=lambda s: None)
        self.assertEqual(out["status"], "failed")
        self.assertIn("batch cap", out["error"])
        self.assertEqual(lam.invocations, [])

    def test_finalize_restores_both_even_if_env_update_fails(self):
        lam, store = FakeLambda("true"), FakeStore(dry_run=False)
        lam.fail_update = True
        res = run_delete_result(ok=0)
        with base_env("true"):
            out = cs.handle_schedule(self.event(), Ctx(), notion_token="t",
                                     lam=lam, store=store, run_delete=lambda: res, sleep=lambda s: None)
        self.assertEqual(out["status"], "failed")
        self.assertTrue(out["restore_errors"])
        self.assertTrue(store.dry_run, "DRY_RUN restore still attempted after env failure")


class WatchdogTests(unittest.TestCase):
    def test_watchdog_restores_flag_on_outside_window(self):
        lam, store = FakeLambda("true"), FakeStore(dry_run=False)
        with base_env("true"):
            out = cs.handle_schedule({"step": "watchdog"}, Ctx(), notion_token="t",
                                     lam=lam, store=store, run_delete=lambda: {}, sleep=lambda s: None,
                                     now=lambda: WED_AM_IST)
        self.assertEqual(out["status"], "alarmed")
        self.assertEqual(lam.updates, ["false"])
        self.assertTrue(store.dry_run)
        self.assertIn("WATCHDOG ALARM", str(store.log_entries[0]))

    def test_watchdog_quiet_when_flag_off(self):
        lam, store = FakeLambda("false"), FakeStore()
        out = cs.handle_schedule({"step": "watchdog"}, Ctx(), notion_token="t",
                                 lam=lam, store=store, run_delete=lambda: {}, sleep=lambda s: None,
                                 now=lambda: WED_AM_IST)
        self.assertEqual(out["status"], "ok")
        self.assertEqual(lam.updates, [])
        self.assertEqual(store.log_entries, [])

    def test_watchdog_allows_flag_during_tuesday_window(self):
        lam, store = FakeLambda("true"), FakeStore(dry_run=False)
        out = cs.handle_schedule({"step": "watchdog"}, Ctx(), notion_token="t",
                                 lam=lam, store=store, run_delete=lambda: {}, sleep=lambda s: None,
                                 now=lambda: TUE_AM_IST)
        self.assertEqual(out["status"], "ok")
        self.assertEqual(lam.updates, [])

    def test_watchdog_leaves_a_live_creation_chain_alone_at_night(self):
        lam, store = FakeLambda("true"), FakeStore(dry_run=False)
        night = datetime(2026, 11, 24, 19, 35, tzinfo=timezone.utc)  # 1:05 AM IST Wednesday
        store.last_run_at = lambda op: datetime(2026, 11, 24, 19, 30, tzinfo=timezone.utc)  # batch finished 5 min ago
        with base_env("true"):
            out = cs.handle_schedule({"step": "watchdog"}, Ctx(), notion_token="t", lam=lam, store=store,
                                     run_delete=lambda: {}, sleep=lambda s: None, now=lambda: night)
        self.assertEqual(out["status"], "ok")
        self.assertEqual(lam.updates, [])

    def test_watchdog_restores_a_stale_creation_run_at_night(self):
        lam, store = FakeLambda("true"), FakeStore(dry_run=False)
        night = datetime(2026, 11, 24, 19, 35, tzinfo=timezone.utc)
        store.last_run_at = lambda op: datetime(2026, 11, 24, 19, 0, tzinfo=timezone.utc)  # 35 min ago: crashed
        with base_env("true"):
            out = cs.handle_schedule({"step": "watchdog"}, Ctx(), notion_token="t", lam=lam, store=store,
                                     run_delete=lambda: {}, sleep=lambda s: None, now=lambda: night)
        self.assertEqual(out["status"], "alarmed")
        self.assertEqual(lam.updates, ["false"])

    def test_watchdog_restores_when_heartbeat_unreadable_or_missing(self):
        for beat in (lambda op: None, lambda op: (_ for _ in ()).throw(RuntimeError("notion down"))):
            lam, store = FakeLambda("true"), FakeStore(dry_run=False)
            store.last_run_at = beat
            with base_env("true"):
                out = cs.handle_schedule({"step": "watchdog"}, Ctx(), notion_token="t", lam=lam, store=store,
                                         run_delete=lambda: {}, sleep=lambda s: None,
                                         now=lambda: datetime(2026, 11, 24, 19, 35, tzinfo=timezone.utc))
            self.assertEqual(out["status"], "alarmed")

    def test_unknown_step_raises(self):
        with self.assertRaises(cs.ScheduleError):
            cs.handle_schedule({"step": "nope"}, Ctx(), notion_token="t",
                               lam=FakeLambda(), store=FakeStore(), run_delete=lambda: {})


if __name__ == "__main__":
    unittest.main()


class CreateFlowTests(unittest.TestCase):
    def test_create_begin_opens_gate_and_chains_create_batch(self):
        lam, store = FakeLambda("false"), FakeStore()
        with base_env("false"):
            out = cs.handle_schedule({"step": "create_begin"}, Ctx(), notion_token="t",
                                     lam=lam, store=store, run_delete=lambda op="delete": {}, sleep=lambda s: None)
        self.assertEqual(out["status"], "started")
        self.assertTrue(store.create_on)
        self.assertFalse(store.dry_run)
        self.assertEqual(lam.invocations[0]["op"], "create")
        self.assertTrue(lam.invocations[0]["run_id"].startswith("create-"))

    def test_create_begin_aborts_on_open_gate(self):
        lam, store = FakeLambda("true"), FakeStore()
        with base_env("true"):
            out = cs.handle_schedule({"step": "create_begin"}, Ctx(), notion_token="t",
                                     lam=lam, store=store, run_delete=lambda op="delete": {}, sleep=lambda s: None)
        self.assertEqual(out["status"], "aborted")
        self.assertFalse(store.create_on)

    def test_zero_eligible_create_restores_all_and_reports(self):
        lam, store = FakeLambda("true"), FakeStore(dry_run=False)
        store.create_on = True
        seen = []
        def run(op="delete"):
            seen.append(op)
            return run_delete_result(ok=0, lines=["[t] CREATE - SKIPPED no eligible rows"])
        ev = {"step": "batch", "op": "create", "run_id": "create-x", "batch": 1, "totals": {}, "deleted": [], "failures": []}
        with base_env("true"):
            out = cs.handle_schedule(ev, Ctx(), notion_token="t", lam=lam, store=store,
                                     run_delete=run, sleep=lambda s: None, now=lambda: TUE_PM_IST)
        self.assertEqual(seen, ["create"])
        self.assertEqual(out["status"], "completed")
        self.assertEqual(lam.flag, "false")
        self.assertTrue(store.dry_run)
        self.assertFalse(store.create_on)
        self.assertEqual(len(store.log_entries), 1)
        self.assertIn("zero actions", str(store.log_entries[0]))

    def test_create_ok_chains_then_failure_stops_and_restores(self):
        lam, store = FakeLambda("true"), FakeStore(dry_run=False)
        store.create_on = True
        res = run_delete_result(ok=2, lines=["[t] CREATE EF-1 product=p1 OK created", "[t] CREATE EF-2 product=p2 OK created"])
        ev = {"step": "batch", "op": "create", "run_id": "create-x", "batch": 1, "totals": {}, "deleted": [], "failures": []}
        with base_env("true"):
            out = cs.handle_schedule(ev, Ctx(), notion_token="t", lam=lam, store=store,
                                     run_delete=lambda op="delete": res, sleep=lambda s: None, now=lambda: TUE_PM_IST)
        self.assertEqual(out["status"], "chained")
        self.assertEqual(lam.invocations[0]["op"], "create")
        self.assertEqual(lam.invocations[0]["deleted"], ["EF-1", "EF-2"])
        bad = run_delete_result(ok=0, failed=1, lines=["[t] CREATE EF-3 FAILED boom"])
        with base_env("true"):
            out = cs.handle_schedule(ev, Ctx(), notion_token="t", lam=lam, store=store,
                                     run_delete=lambda op="delete": bad, sleep=lambda s: None, now=lambda: TUE_PM_IST)
        self.assertEqual(out["status"], "failed")
        self.assertFalse(store.create_on)
        self.assertEqual(lam.flag, "false")

    def test_create_chain_keeps_going_after_11pm(self):
        lam, store = FakeLambda("true"), FakeStore(dry_run=False)
        res = run_delete_result(ok=3, lines=["[t] CREATE EF-9 product=p9 OK created"])
        ev = {"step": "batch", "op": "create", "run_id": "create-x", "batch": 5, "totals": {}, "deleted": [], "failures": []}
        late = datetime(2026, 11, 24, 18, 0, tzinfo=timezone.utc)  # 11:30 PM IST: no clock cutoff any more
        with base_env("true"):
            out = cs.handle_schedule(ev, Ctx(), notion_token="t", lam=lam, store=store,
                                     run_delete=lambda op="delete": res, sleep=lambda s: None, now=lambda: late)
        self.assertEqual(out["status"], "chained")

    def test_create_chain_stops_loudly_at_the_overnight_safety_stop(self):
        lam, store = FakeLambda("true"), FakeStore(dry_run=False)
        store.create_on = True
        seen = []
        ev = {"step": "batch", "op": "create", "run_id": "create-x", "batch": 50, "totals": {"ok": 30}, "deleted": ["EF-1"], "failures": []}
        morning = datetime(2026, 11, 25, 3, 5, tzinfo=timezone.utc)  # 8:35 AM IST
        with base_env("true"):
            out = cs.handle_schedule(ev, Ctx(), notion_token="t", lam=lam, store=store,
                                     run_delete=lambda op="delete": seen.append(op), sleep=lambda s: None, now=lambda: morning)
        self.assertEqual(seen, [])
        self.assertEqual(out["status"], "failed")  # never a silent normal completion
        self.assertIn("overnight safety stop", out["error"])
        self.assertIn("NOT created", out["error"])
        self.assertEqual(lam.flag, "false")
        self.assertFalse(store.create_on)

    def test_chain_ending_with_skipped_rows_reports_them_as_unfinished(self):
        lam, store = FakeLambda("true"), FakeStore(dry_run=False)
        store.create_on = True
        res = run_delete_result(ok=0, skipped=2, lines=["[t] CREATE EF-7 SKIPPED no photos; skipped",
                                                        "[t] CREATE EF-8 SKIPPED unknown result, not creating again until checked in Meta"])
        ev = {"step": "batch", "op": "create", "run_id": "create-x", "batch": 3, "totals": {}, "deleted": [], "failures": []}
        with base_env("true"):
            out = cs.handle_schedule(ev, Ctx(), notion_token="t", lam=lam, store=store,
                                     run_delete=lambda op="delete": res, sleep=lambda s: None, now=lambda: TUE_PM_IST)
        text = str(store.log_entries)
        self.assertIn("UNFINISHED: 2", text)
        self.assertIn("not because everything was done", text)

    def test_create_chain_is_not_limited_to_40_batches(self):
        lam, store = FakeLambda("true"), FakeStore(dry_run=False)
        res = run_delete_result(ok=3, lines=["[t] CREATE EF-9 product=p9 OK created"])
        ev = {"step": "batch", "op": "create", "run_id": "create-x", "batch": cs.MAX_BATCHES + 5, "totals": {}, "deleted": [], "failures": []}
        with base_env("true"):
            out = cs.handle_schedule(ev, Ctx(), notion_token="t", lam=lam, store=store,
                                     run_delete=lambda op="delete": res, sleep=lambda s: None, now=lambda: TUE_PM_IST)
        self.assertEqual(out["status"], "chained")

    def test_evening_window_counts_for_watchdog(self):
        self.assertTrue(cs._in_run_window(datetime(2026, 11, 25, 15, 45, tzinfo=timezone.utc)))  # 21:15 IST
