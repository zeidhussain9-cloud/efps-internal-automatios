"""Weekly scheduled catalogue cleanup - "Tuesday catalogue cleanup".

Approved by Zeid 21 Nov 2026 (WhatsApp, 16:37 IST): every Tuesday 9:00 AM IST,
EventBridge fires step=begin. The flow:

  begin    -> catalog-write env flag ON (own function config), DRY_RUN off,
              then self-invoke the first batch.
  batch    -> runs ONE real delete run (cap 3, per-batch verification lives in
              the runner). ok>0 -> next batch; ok=0 -> finalize success;
              failed>0 / would>0 / exception -> finalize with error. No
              auto-rerun of real faults: stop safe, report, wait for Zeid.
  finalize -> guaranteed restore: catalog-write flag OFF + DRY_RUN ON, both
              attempted even if the other fails; Decision Log entry;
              structured CloudWatch completion/failure event (the scorecard).
  watchdog -> daily 10:05 IST: if the write flag is ON outside the Tuesday
              09:00-10:00 IST run window, force restore and raise the alarm.

A hard process crash breaks the self-invoke chain; the watchdog is the
guaranteed backstop that locks the gate afterwards.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

SCHEDULE_EVENT = "_efps_catalogue_schedule"
CATALOG_WRITE_FLAG = "EFPS_WHAPI_CATALOG_WRITE_ENABLED"
MAX_BATCHES_CREATE = 200  # runaway guard only; the real limit for create is the nightly window
MAX_BATCHES = 40  # 120 deletions per session is far beyond realistic; beyond that, stop and report.

# Decision Log (Notion): session entries go newest-first, right after the intro block.
DECISION_LOG_PAGE_ID = "419fedf9-b4e8-81d4-afea-e6c190f2106e"
DECISION_LOG_INTRO_BLOCK_ID = "419fedf9-b4e8-819d-88b0-e7d07403a1c1"

IST = timezone(timedelta(hours=5, minutes=30))
RUN_WINDOW_WEEKDAY = 1  # Tuesday
RUN_WINDOW_START_HOUR = 9  # 09:00 IST inclusive
RUN_WINDOW_END_HOUR = 10  # 10:00 IST exclusive
CREATE_WINDOW_START_HOUR = 21  # daily creation run, 9:00 PM IST (approved 24 Nov, build only)
CREATE_WINDOW_END_HOUR = 23  # run window 9-11 PM; the 11:05 PM watchdog closes any crash leftovers
OPS = ("delete", "create")


def _log(event: str, **fields: Any) -> None:
    print(json.dumps({"event": event, "service": "efps-notion-intake", **fields}, default=str))


def _truthy(value: Any) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _in_run_window(now_utc: datetime) -> bool:
    ist = now_utc.astimezone(IST)
    if CREATE_WINDOW_START_HOUR <= ist.hour < CREATE_WINDOW_END_HOUR:
        return True  # daily creation window, 9-10 PM IST
    return (
        ist.weekday() == RUN_WINDOW_WEEKDAY
        and RUN_WINDOW_START_HOUR <= ist.hour < RUN_WINDOW_END_HOUR
    )


class ScheduleError(RuntimeError):
    pass


# --- AWS side ------------------------------------------------------------

def _function_name(context: Any) -> str:
    arn = str(getattr(context, "invoked_function_arn", "") or "")
    if not arn:
        raise ScheduleError("invoked_function_arn missing; cannot locate own function")
    return arn


def _wait_for_update(lam: Any, fn: str, *, sleep, timeout_s: int = 120) -> None:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        cfg = lam.get_function_configuration(FunctionName=fn)
        if cfg.get("LastUpdateStatus") == "Successful":
            return
        sleep(2)
    raise ScheduleError("function configuration update did not settle in time")


def _set_catalog_write(lam: Any, fn: str, enabled: bool, *, sleep) -> None:
    cfg = lam.get_function_configuration(FunctionName=fn)
    env = dict(((cfg.get("Environment") or {}).get("Variables")) or {})
    env[CATALOG_WRITE_FLAG] = "true" if enabled else "false"
    lam.update_function_configuration(FunctionName=fn, Environment={"Variables": env})
    _wait_for_update(lam, fn, sleep=sleep)


def _self_invoke(lam: Any, fn: str, payload: Mapping[str, Any]) -> None:
    lam.invoke(
        FunctionName=fn,
        InvocationType="Event",
        Payload=json.dumps({SCHEDULE_EVENT: True, **payload}).encode("utf-8"),
    )


# --- Notion side ----------------------------------------------------------

def _set_switch(store: Any, name: str, enabled: bool) -> None:
    from catalogue_notion_store import SWITCHES_DATABASE_ID
    for page in store._query_all(SWITCHES_DATABASE_ID):
        props = page.get("properties") or {}
        title = "".join(t.get("plain_text", "") for t in ((props.get("Name") or {}).get("title")) or [])
        if title.strip() == name:
            store.request("PATCH", f"pages/{page['id']}",
                          payload={"properties": {"Enabled": {"checkbox": bool(enabled)}}})
            return
    raise ScheduleError(f"{name} switch page not found in the switches database")


def _set_dry_run(store: Any, enabled: bool) -> None:
    _set_switch(store, "DRY_RUN", enabled)


def _append_decision_log(store: Any, lines: list[str]) -> None:
    children = []
    for i, line in enumerate(lines):
        block_type = "heading_2" if i == 0 else "bulleted_list_item"
        children.append({
            "object": "block",
            "type": block_type,
            block_type: {"rich_text": [{"type": "text", "text": {"content": line[:1900]}}]},
        })
    store.request("PATCH", f"blocks/{DECISION_LOG_PAGE_ID}/children",
                  payload={"children": children, "after": DECISION_LOG_INTRO_BLOCK_ID})


# --- flow -----------------------------------------------------------------

def handle_schedule(event: Mapping[str, Any], context: Any, *, notion_token: str,
                    lam: Any = None, store: Any = None, run_delete: Any = None,
                    sleep=time.sleep, now=None) -> dict:
    """Dispatch one schedule step. All clients injectable for tests."""
    if lam is None:
        import boto3
        lam = boto3.client("lambda")
    if store is None:
        from catalogue_notion_store import NotionCatalogueStore
        store = NotionCatalogueStore(notion_token)
    if run_delete is None:
        def run_delete(op="delete"):
            import catalogue_trigger
            left = None
            if context is not None and hasattr(context, "get_remaining_time_in_millis"):
                left = lambda: context.get_remaining_time_in_millis() / 1000.0
            return catalogue_trigger.run_catalogue_operation(op, notion_token=notion_token, time_left=left)
    now = now or (lambda: datetime.now(timezone.utc))
    step = str(event.get("step") or "").strip().lower()

    if step == "watchdog":
        return _watchdog(lam, store, context, sleep=sleep, now=now)
    if step == "begin":
        return _begin(lam, store, context, sleep=sleep, now=now)
    if step == "create_begin":
        return _begin(lam, store, context, sleep=sleep, now=now, op="create")
    if step == "batch":
        return _batch(event, lam, store, context, run_delete=run_delete, sleep=sleep, now=now)
    if step == "finalize":
        return _finalize(event, lam, store, context, sleep=sleep, now=now)
    raise ScheduleError(f"unknown schedule step: {step!r}")


def _begin(lam, store, context, *, sleep, now, op="delete") -> dict:
    fn = _function_name(context)
    if _truthy(os.environ.get(CATALOG_WRITE_FLAG)):
        # The gate should be locked at start. Refuse to run on an open gate -
        # the watchdog owns restoring it, and this abort is the alarm.
        _log("catalogue_schedule_aborted", reason="catalog-write flag already ON at begin; not running")
        return {"status": "aborted", "reason": "flag already on"}
    prefix = "create-" if op == "create" else "tue-"
    run_id = now().astimezone(IST).strftime(prefix + "%Y-%m-%d-") + uuid.uuid4().hex[:6]
    try:
        _set_catalog_write(lam, fn, True, sleep=sleep)
        _set_dry_run(store, False)
        if op == "create":
            _set_switch(store, "CREATE", True)
    except Exception as exc:  # noqa: BLE001 - never leave a half-open gate
        return _finalize({"run_id": run_id, "op": op,
                          "error": f"begin failed: {type(exc).__name__}: {str(exc)[:200]}"},
                         lam, store, context, sleep=sleep, now=now)
    _log("catalogue_schedule_started", run_id=run_id, op=op)
    _self_invoke(lam, fn, {"step": "batch", "run_id": run_id, "op": op, "batch": 1,
                           "totals": {"ok": 0, "failed": 0, "skipped": 0},
                           "deleted": [], "failures": []})
    return {"status": "started", "run_id": run_id}


def _batch(event, lam, store, context, *, run_delete, sleep, now) -> dict:
    fn = _function_name(context)
    op = str(event.get("op") or "delete")
    if op not in OPS:
        return _finalize({**event, "error": f"unknown op {op!r}"}, lam, store, context, sleep=sleep, now=now)
    run_id = str(event.get("run_id") or "")
    batch = int(event.get("batch") or 1)
    totals = dict(event.get("totals") or {})
    deleted = list(event.get("deleted") or [])
    failures = list(event.get("failures") or [])

    if not _truthy(os.environ.get(CATALOG_WRITE_FLAG)):
        return _finalize({**event, "error": "catalog-write flag OFF mid-run; stopping safe"},
                         lam, store, context, sleep=sleep, now=now)
    if op == "create" and not _in_run_window(now()):
        return _finalize({**event, "error": "creation window (9-11 PM IST) closed; stopping safe, remaining rows continue at the next scheduled run"},
                         lam, store, context, sleep=sleep, now=now)
    try:
        result = (run_delete(op) if op == "create" else run_delete()) or {}
    except Exception as exc:  # real fault: stop safe, report, no auto-rerun
        return _finalize({**event, "error": f"batch {batch} raised {type(exc).__name__}: {str(exc)[:300]}"},
                         lam, store, context, sleep=sleep, now=now)

    counts = result.get("counts") or {}
    dry_run = bool(result.get("dry_run"))
    lines = [str(l) for l in (result.get("lines") or [])]
    ok, failed = int(counts.get("ok") or 0), int(counts.get("failed") or 0)
    would = int(counts.get("would") or 0)
    for key in ("ok", "failed", "skipped"):
        totals[key] = int(totals.get(key) or 0) + int(counts.get(key) or 0)
    for line in lines:
        # Format: "[<ts>] DELETE <listing_id> [product=<id>] OK|FAILED <reason>"
        # (the timestamp itself contains a space - anchor on the DELETE token)
        parts = line.split()
        if op.upper() not in parts:
            continue
        i = parts.index(op.upper())
        rest = parts[i + 1:]
        if len(rest) < 2:
            continue
        lid = rest[0]
        outcome = rest[2] if len(rest) >= 3 and rest[1].startswith("product=") else rest[1]
        if outcome.startswith("OK"):
            deleted.append(lid)
        elif outcome.startswith("FAILED"):
            failures.append(line[:300])
    _log("catalogue_schedule_batch", run_id=run_id, batch=batch,
         ok=ok, failed=failed, would=would, dry_run=dry_run)

    if dry_run or would > 0:
        return _finalize({**event, "totals": totals, "deleted": deleted, "failures": failures,
                          "error": "DRY_RUN still on during a scheduled real run; stopping safe"},
                         lam, store, context, sleep=sleep, now=now)
    if failed > 0:
        return _finalize({**event, "totals": totals, "deleted": deleted, "failures": failures,
                          "error": f"batch {batch} had {failed} failed deletion(s); no auto-rerun"},
                         lam, store, context, sleep=sleep, now=now)
    if ok > 0:
        if batch >= (MAX_BATCHES_CREATE if op == "create" else MAX_BATCHES):
            return _finalize({**event, "totals": totals, "deleted": deleted, "failures": failures,
                              "error": f"batch cap {MAX_BATCHES_CREATE if op == 'create' else MAX_BATCHES} reached; remaining rows wait for the next scheduled run"},
                             lam, store, context, sleep=sleep, now=now)
        _self_invoke(lam, fn, {"step": "batch", "run_id": run_id, "op": op, "batch": batch + 1,
                               "totals": totals, "deleted": deleted, "failures": failures})
        return {"status": "chained", "run_id": run_id, "next_batch": batch + 1}
    return _finalize({**event, "totals": totals, "deleted": deleted, "failures": failures},
                     lam, store, context, sleep=sleep, now=now)


def _finalize(event, lam, store, context, *, sleep, now) -> dict:
    fn = _function_name(context)
    run_id = str(event.get("run_id") or "")
    totals = dict(event.get("totals") or {})
    deleted = list(event.get("deleted") or [])
    failures = list(event.get("failures") or [])
    error = str(event.get("error") or "")
    op = str(event.get("op") or "delete")
    restore_errors = _restore(lam, store, fn, sleep=sleep, create=(op == "create"))

    status = "failed" if (error or restore_errors) else "completed"
    stamp = now().astimezone(IST).strftime("%d %b %Y, %I:%M %p IST")
    if op == "create":
        title = f"{stamp} - Scheduled catalogue creation ({run_id or 'manual'}): {status.upper()}"
        what = f"WHAT: daily 9 PM IST creation-only run ({run_id}); no update, delete or assign."
        verb = "created"
    else:
        title = f"{stamp} - Scheduled catalogue cleanup ({run_id or 'manual'}): {status.upper()}"
        what = f"WHAT: weekly Tuesday scheduled delete run ({run_id})."
        verb = "deleted"
    body = [
        what,
        f"RESULT: {verb} {len(deleted)} product(s){': ' + ', '.join(deleted) if deleted else ' (zero actions)'}.",
        f"TOTALS: ok={int(totals.get('ok') or 0)}, skipped={int(totals.get('skipped') or 0)}, failed={int(totals.get('failed') or 0)}.",
    ]
    if error:
        body.append(f"ERROR: {error} - gate restored, no auto-rerun; waits for Zeid's decision.")
    if failures:
        body.append("FAILURES: " + " | ".join(failures[:5]))
    body.append("SWITCHES RESTORED: catalog-write OFF, DRY_RUN ON" + (", CREATE OFF." if op == "create" else ".") +
                ("" if not restore_errors else f" RESTORE PROBLEM: {'; '.join(restore_errors)}"))
    try:
        _append_decision_log(store, [title] + body)
    except Exception as exc:  # never let logging block the restore outcome
        from known_errors import known_recovery
        recovery = known_recovery("append_decision_log", exc)
        _log("catalogue_schedule_log_unshared" if recovery else "catalogue_schedule_log_failed",
             run_id=run_id, error=str(exc)[:300], recovery=recovery,
             pending_decision_log=[title] + body)


    _log("catalogue_schedule_completed" if status == "completed" else "catalogue_schedule_failed",
         run_id=run_id, status=status, totals=totals, deleted=deleted,
         failures=failures, error=error, restore_errors=restore_errors)
    return {"status": status, "run_id": run_id, "totals": totals,
            "deleted": deleted, "failures": failures, "error": error,
            "restore_errors": restore_errors}


def _restore(lam, store, fn, *, sleep, create=True) -> list[str]:
    """Best-effort guaranteed restore; both steps attempted no matter what."""
    problems = []
    try:
        _set_catalog_write(lam, fn, False, sleep=sleep)
    except Exception as exc:  # noqa: BLE001
        problems.append(f"catalog-write restore failed: {type(exc).__name__} {str(exc)[:200]}")
    try:
        _set_dry_run(store, True)
    except Exception as exc:  # noqa: BLE001
        problems.append(f"DRY_RUN restore failed: {type(exc).__name__} {str(exc)[:200]}")
    if create:  # harmless when already OFF; never left ON after any run or alarm
        try:
            _set_switch(store, "CREATE", False)
        except Exception as exc:  # noqa: BLE001
            problems.append(f"CREATE restore failed: {type(exc).__name__} {str(exc)[:200]}")
    return problems


def _watchdog(lam, store, context, *, sleep, now) -> dict:
    fn = _function_name(context)
    cfg = lam.get_function_configuration(FunctionName=fn)
    live_flag = _truthy((((cfg.get("Environment") or {}).get("Variables")) or {}).get(CATALOG_WRITE_FLAG))
    if not live_flag:
        _log("catalogue_watchdog_ok", detail="catalog-write flag OFF as expected")
        return {"status": "ok"}
    if _in_run_window(now()):
        _log("catalogue_watchdog_ok", detail="flag ON inside the Tuesday run window")
        return {"status": "ok", "detail": "run window"}
    problems = _restore(lam, store, fn, sleep=sleep)
    _log("catalogue_watchdog_alarm",
         detail="catalog-write flag was ON outside the run window; forced restore",
         restore_errors=problems)
    stamp = now().astimezone(IST).strftime("%d %b %Y, %I:%M %p IST")
    try:
        _append_decision_log(store, [
            f"{stamp} - WATCHDOG ALARM: catalog-write flag found ON outside run window",
            "WHAT: daily watchdog found the AWS catalog-write switch ON outside Tuesday 9-10 AM IST.",
            "ACTION: forced restore - catalog-write OFF, DRY_RUN ON." +
            ("" if not problems else f" RESTORE PROBLEM: {'; '.join(problems)}"),
        ])
    except Exception as exc:  # noqa: BLE001
        _log("catalogue_watchdog_log_failed", error=str(exc)[:300])
    return {"status": "alarmed", "restore_errors": problems}
