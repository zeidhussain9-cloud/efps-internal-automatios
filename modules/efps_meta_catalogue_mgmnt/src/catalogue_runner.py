"""Gated catalogue operations runner — owner-locked design, 21 Nov 2026.

The 5 operations (CREATE, UPDATE, DELETE, ASSIGN, RECONCILE) run ONLY when
explicitly triggered from the Catalogue Control Panel. Nothing auto-fires:
a ticked "Post to Catalogue" checkbox only marks a row eligible; a run
happens only when the operator triggers the operation.

Safety contract (locked):
- At every run start all 8 switch states are read and logged:
  2 template.yaml masters (EFPS_WHAPI_LIVE, EFPS_WHAPI_API_ENABLED) and
  6 Notion checkboxes (CREATE, UPDATE, DELETE, ASSIGN, RECONCILE, DRY_RUN).
  An unreadable switches table = everything off = the run does nothing
  (fail-closed).
- Strictly sequential calls, never parallel.
- 30s pause between a successful create and its assign.
- One 429 retry after 30s; a second 429 defers the row to the next run.
- Per-run caps: 10 creates, 10 updates, 3 deletes, 20 assigns.
- DELETE removes by the exact stored product ID, never by searching.
  After delete the product ID stays in meta_catalog_id for history and is
  rewritten in red; "Meta Catalogue" is removed from `live at`.
- CREATE writes "Meta Catalogue" into `live at` only after the product
  actually exists; the operator never sets it by hand (option B).
- RECONCILE is report-only: it compares and writes a summary + review-queue
  entries; it never calls the other operations and never touches WhatsApp.
- DRY_RUN: full read/compare/decide, every intended action logged as
  "WOULD ...", zero writes to WhatsApp and zero writes to Notion rows.

The store and client are dependency-injected; tests use fakes.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Callable, Mapping

OPERATIONS = ("create", "update", "delete", "assign", "reconcile")
SWITCH_BY_OPERATION = {
    "create": "CREATE",
    "update": "UPDATE",
    "delete": "DELETE",
    "assign": "ASSIGN",
    "reconcile": "RECONCILE",
}
CAPS = {"create": 10, "update": 10, "delete": 3, "assign": 20}
CREATE_ASSIGN_GAP_SECONDS = 30
RATE_LIMIT_RETRY_SECONDS = 30
KNOWN_COLLECTION_IDS = frozenset({
    "1076581028327869",
    "2280178899499736",
    "2370295543377765",
    "2585336038575419",
})
META_CHANNEL = "Meta Catalogue"


def _ts(now: datetime | None = None) -> str:
    return (now or datetime.now(timezone.utc)).strftime("%Y-%m-%d %H:%M:%SZ")


def log_line(op: str, listing_id: str, product_id: str, outcome: str, reason: str = "", *, now: datetime | None = None) -> str:
    product = f" product={product_id}" if product_id else ""
    suffix = f" {reason}" if reason else ""
    return f"[{_ts(now)}] {op.upper()} {listing_id}{product} {outcome}{suffix}"


def switch_states(switches: Mapping[str, bool], *, masters: Mapping[str, bool]) -> dict[str, bool]:
    """The 8 states logged at every run start."""
    states = {
        "EFPS_WHAPI_LIVE": bool(masters.get("EFPS_WHAPI_LIVE")),
        "EFPS_WHAPI_API_ENABLED": bool(masters.get("EFPS_WHAPI_API_ENABLED")),
        "DRY_RUN": bool(switches.get("DRY_RUN")),
    }
    for op in OPERATIONS:
        states[SWITCH_BY_OPERATION[op]] = bool(switches.get(SWITCH_BY_OPERATION[op]))
    return states


class CatalogueRunError(RuntimeError):
    pass


def _is_rate_limited(exc: BaseException) -> bool:
    text = str(exc)
    return "429" in text or "Rate-limited" in text or "Too many requests" in text


def _call_with_retry(fn: Callable[[], Any], *, sleeper: Callable[[float], None] = time.sleep) -> Any:
    """One 429 retry after 30s; a second 429 (or any other error) propagates."""
    try:
        return fn()
    except Exception as exc:  # noqa: BLE001 - classified below
        if not _is_rate_limited(exc):
            raise
        sleeper(RATE_LIMIT_RETRY_SECONDS)
        return fn()


def _live_at(row: Mapping[str, Any]) -> list[str]:
    value = row.get("live at") or []
    if isinstance(value, str):
        return [v.strip() for v in value.split(",") if v.strip()]
    return [str(v) for v in value]


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "on", "ticked", "checked"}


# --- eligibility (option B: "Post to Catalogue" checkbox is the operator trigger) ---

def eligible_create(row: Mapping[str, Any]) -> bool:
    return (
        _truthy(row.get("post_to_catalogue"))
        and str(row.get("Availability") or "") == "Available"
        and not str(row.get("meta_catalog_id") or "").strip()
    )


def eligible_update(row: Mapping[str, Any]) -> bool:
    # "Posted" state = Meta Catalogue membership in live at + a product ID.
    return META_CHANNEL in _live_at(row) and bool(str(row.get("meta_catalog_id") or "").strip())


def eligible_delete(row: Mapping[str, Any]) -> bool:
    if not str(row.get("meta_catalog_id") or "").strip():
        return False
    # Only a row still marked as live on Meta Catalogue can carry a live product.
    if META_CHANNEL not in _live_at(row):
        return False
    return (
        str(row.get("Availability") or "") in {"Rented Out", "On Hold"}
        or not _truthy(row.get("post_to_catalogue"))
    )


def eligible_assign(row: Mapping[str, Any]) -> bool:
    # An empty formula (unmapped BHK) stays eligible so the run logs the skip
    # instead of silently ignoring the row.
    return (
        bool(str(row.get("meta_catalog_id") or "").strip())
        and META_CHANNEL in _live_at(row)
    )


ELIGIBLE = {
    "create": eligible_create,
    "update": eligible_update,
    "delete": eligible_delete,
    "assign": eligible_assign,
}


class _Run:
    def __init__(self, operation: str, store: Any, whapi: Any, *, dry_run: bool, now: datetime | None = None, sleeper: Callable[[float], None] = time.sleep) -> None:
        self.operation = operation
        self.store = store
        self.whapi = whapi
        self.dry_run = dry_run
        self.now = now
        self.sleeper = sleeper
        self.lines: list[str] = []
        self.counts = {"ok": 0, "skipped": 0, "failed": 0, "would": 0}

    def record(self, row: Mapping[str, Any], product_id: str, outcome: str, reason: str = "") -> str:
        line = log_line(self.operation, str(row.get("listing_id") or "?"), product_id, outcome, reason, now=self.now)
        self.lines.append(line)
        if not self.dry_run:
            self.store.append_activity(str(row.get("page_id") or ""), line)
        key = {"OK": "ok", "ADOPTED": "ok", "WOULD": "would", "SKIPPED": "skipped"}.get(outcome.split()[0], "failed")
        self.counts[key] += 1
        return line

    def summary(self, states: Mapping[str, bool]) -> dict[str, Any]:
        return {
            "operation": self.operation,
            "dry_run": self.dry_run,
            "states": dict(states),
            "counts": dict(self.counts),
            "lines": list(self.lines),
        }


def run_operation(operation: str, *, store: Any, whapi: Any, masters: Mapping[str, bool], now: datetime | None = None, sleeper: Callable[[float], None] = time.sleep) -> dict[str, Any]:
    """Run one gated operation. `store`/`whapi` are injected (fakes in tests).

    masters: {"EFPS_WHAPI_LIVE": bool, "EFPS_WHAPI_API_ENABLED": bool} — the two
    template.yaml kill switches, resolved by the caller from the environment.
    """
    if operation not in OPERATIONS:
        raise ValueError(f"unknown operation {operation!r}")

    # Fail-closed: an unreadable switches table aborts the run with nothing done.
    try:
        switches = {str(k): _truthy(v) for k, v in (store.read_switches() or {}).items()}
    except Exception as exc:  # noqa: BLE001
        raise CatalogueRunError(f"switches table unreadable; everything is OFF, nothing ran: {exc}") from exc

    states = switch_states(switches, masters=masters)
    dry_run = states["DRY_RUN"]
    run = _Run(operation, store, whapi, dry_run=dry_run, now=now, sleeper=sleeper)

    if operation != "reconcile":
        if not (states["EFPS_WHAPI_LIVE"] and states["EFPS_WHAPI_API_ENABLED"]):
            run.lines.append(log_line(operation, "-", "", "FAILED", "master kill switch off; nothing ran", now=now))
            return run.summary(states)
        if not states[SWITCH_BY_OPERATION[operation]]:
            run.lines.append(log_line(operation, "-", "", "SKIPPED", f"{SWITCH_BY_OPERATION[operation]} switch off; nothing ran", now=now))
            return run.summary(states)

    # Queued review decisions for this operation execute FIRST, through the
    # same gated paths, before the normal pass.
    for entry in store.read_review_decisions(operation) or []:
        _execute_review_decision(run, entry)

    rows = store.query_listings() or []
    if operation == "reconcile":
        _op_reconcile(run, rows)
    else:
        eligible = [r for r in rows if ELIGIBLE[operation](r)]
        if not eligible:
            run.lines.append(log_line(operation, "-", "", "SKIPPED", "no eligible rows", now=now))
        cap = CAPS[operation]
        for row in eligible[:cap]:
            _execute(operation, run, row)
        for row in eligible[cap:]:
            run.record(row, str(row.get("meta_catalog_id") or ""), "SKIPPED", f"per-run cap {cap} reached; row waits for next run")

    result = run.summary(states)
    if not dry_run:
        store.write_panel_summary(operation, result)
    return result


def _execute(operation: str, run: _Run, row: Mapping[str, Any]) -> None:
    try:
        if operation == "create":
            _op_create_row(run, row)
        elif operation == "update":
            _op_update_row(run, row)
        elif operation == "delete":
            _op_delete_row(run, row)
        elif operation == "assign":
            _op_assign_row(run, row)
    except Exception as exc:  # noqa: BLE001 - any failure is logged, row stays for next run
        run.record(row, str(row.get("meta_catalog_id") or ""), "FAILED", str(exc)[:200])


def _op_create_row(run: _Run, row: Mapping[str, Any]) -> None:
    listing_id = str(row.get("listing_id") or "")
    images = [u for u in str(row.get("cloudinary_image_urls") or "").replace(",", " ").split() if u.strip()][:10]
    if not images:
        run.record(row, "", "FAILED", "no photos; skipped")
        return
    if run.dry_run:
        run.record(row, "", "WOULD", f"create product '{row.get('catalog_title')}' with {len(images)} photos")
        return

    # Adoption: never create a duplicate of a product that already exists.
    existing = _call_with_retry(lambda: run.whapi.find_product_by_retailer_id(listing_id), sleeper=run.sleeper)
    if existing:
        product_id = str(existing.get("id") or "")
        _mark_posted(run, row, product_id)
        run.record(row, product_id, "ADOPTED", "product already existed on WhatsApp")
        return

    title = str(row.get("catalog_title") or "").strip()
    description = str(row.get("whatsapp_post") or "").strip()
    try:
        rent = int(row.get("monthly_rent") or 0)
    except (TypeError, ValueError):
        rent = 0
    result = _call_with_retry(
        lambda: run.whapi.create_product(
            name=title, description=description, price=rent, currency="INR",
            images=images, url=str(row.get("google_maps_url") or ""), product_retailer_id=listing_id,
        ),
        sleeper=run.sleeper,
    )
    if isinstance(result, str):
        raise RuntimeError(f"WhAPI error response: {result}")
    product_id = str((result or {}).get("id") or (result or {}).get("product_id") or "")
    if not product_id:
        raise RuntimeError(f"WhAPI returned no product ID: {result}")
    _mark_posted(run, row, product_id)
    run.record(row, product_id, "OK", "created")
    # 30s create->assign spacing, then assign through its own gated path.
    run.sleeper(CREATE_ASSIGN_GAP_SECONDS)
    try:
        switches = run.store.read_switches() or {}
    except Exception:  # noqa: BLE001
        switches = {}
    if _truthy(switches.get("ASSIGN")):
        live = _live_at(row)
        if META_CHANNEL not in live:
            live = live + [META_CHANNEL]
        _op_assign_row(run, {**row, "meta_catalog_id": product_id, "live at": live})


def _mark_posted(run: _Run, row: Mapping[str, Any], product_id: str) -> None:
    live = _live_at(row)
    if META_CHANNEL not in live:
        live = live + [META_CHANNEL]
    run.store.update_listing(str(row.get("page_id") or ""), {
        "meta_catalog_id": product_id,
        "live at": live,
    })


def _op_update_row(run: _Run, row: Mapping[str, Any]) -> None:
    product_id = str(row.get("meta_catalog_id") or "").strip()
    if run.dry_run:
        run.record(row, product_id, "WOULD", "fetch live product, compare with current Notion fields, patch if different")
        return
    try:
        product = _call_with_retry(lambda: run.whapi.get_product(product_id), sleeper=run.sleeper)
    except Exception as exc:  # noqa: BLE001
        if "404" in str(exc):
            live = [c for c in _live_at(row) if c != META_CHANNEL]
            run.store.update_listing(str(row.get("page_id") or ""), {"live at": live})
            run.record(row, product_id, "OK", "product 404 on WhatsApp; removed Meta Catalogue from live at")
            return
        raise
    title = str(row.get("catalog_title") or "").strip()
    description = str(row.get("whatsapp_post") or "").strip()
    try:
        rent = int(row.get("monthly_rent") or 0)
    except (TypeError, ValueError):
        rent = 0
    images = [u for u in str(row.get("cloudinary_image_urls") or "").replace(",", " ").split() if u.strip()][:10]
    wanted = {"name": title, "description": description, "price": rent, "currency": "INR", "images": images}
    current = {
        "name": str((product or {}).get("name") or ""),
        "description": str((product or {}).get("description") or ""),
        "price": (product or {}).get("price"),
        "currency": str((product or {}).get("currency") or "INR"),
        "images": [str(i.get("link") if isinstance(i, dict) else i) for i in (product or {}).get("images") or []],
    }
    changed = {k for k in wanted if str(wanted[k]) != str(current.get(k)) and wanted[k] != current.get(k)}
    if not changed:
        run.record(row, product_id, "OK", "already in sync")
        return
    # WhAPI requires the full photo list on every update.
    _call_with_retry(lambda: run.whapi.update_product(product_id, wanted), sleeper=run.sleeper)
    run.record(row, product_id, "OK", f"updated: {', '.join(sorted(changed))}")


def _op_delete_row(run: _Run, row: Mapping[str, Any]) -> None:
    product_id = str(row.get("meta_catalog_id") or "").strip()
    reason = []
    if str(row.get("Availability") or "") in {"Rented Out", "On Hold"}:
        reason.append(f"Availability={row.get('Availability')}")
    if not _truthy(row.get("post_to_catalogue")):
        reason.append("Post to Catalogue unticked")
    if run.dry_run:
        run.record(row, product_id, "WOULD", f"delete product ({'; '.join(reason)})")
        return
    try:
        _call_with_retry(lambda: run.whapi.delete_product(product_id), sleeper=run.sleeper)
        note = f"deleted ({'; '.join(reason)})"
    except Exception as exc:  # noqa: BLE001
        if "404" in str(exc):
            note = "product already gone on WhatsApp (404); status corrected"
        else:
            raise
    live = [c for c in _live_at(row) if c != META_CHANNEL]
    run.store.update_listing(str(row.get("page_id") or ""), {
        "live at": live,
    })
    # The product ID stays in meta_catalog_id for history, rewritten in red.
    run.store.mark_product_id_removed(str(row.get("page_id") or ""), product_id)
    run.record(row, product_id, "OK", note)


def _op_assign_row(run: _Run, row: Mapping[str, Any]) -> None:
    product_id = str(row.get("meta_catalog_id") or "").strip()
    collection_id = str(row.get("meta_catalog_collection_id") or "").strip()
    if not collection_id:
        run.record(row, product_id, "SKIPPED", "unmapped BHK (formula empty); never guesses")
        return
    if collection_id not in KNOWN_COLLECTION_IDS:
        run.record(row, product_id, "FAILED", f"collection {collection_id} is not one of the 4 known IDs; hard stop for this row")
        return
    if run.dry_run:
        run.record(row, product_id, "WOULD", f"add to collection {collection_id} if not already a member")
        return
    product = _call_with_retry(lambda: run.whapi.get_product(product_id), sleeper=run.sleeper)
    memberships = {str(c) for c in (product or {}).get("collection_ids") or (product or {}).get("collections") or []}
    if collection_id in memberships:
        run.record(row, product_id, "OK", "already in collection")
        return
    _call_with_retry(lambda: run.whapi.edit_collection(collection_id, add_products=[product_id]), sleeper=run.sleeper)
    run.record(row, product_id, "OK", f"added to collection {collection_id}")


def _op_reconcile(run: _Run, rows: list[Mapping[str, Any]]) -> None:
    """REPORT ONLY: compare WhatsApp state with Notion expectations.

    Never calls the other operations, never writes to WhatsApp. Drift and
    orphans are reported; anything needing a human goes to the review queue.
    """
    products = _call_with_retry(lambda: run.whapi.get_products(count=10000), sleeper=run.sleeper)
    by_retailer = {str(p.get("product_retailer_id") or ""): p for p in products}
    expected = {str(r.get("listing_id") or ""): r for r in rows if META_CHANNEL in _live_at(r)}
    for listing_id, row in expected.items():
        product_id = str(row.get("meta_catalog_id") or "").strip()
        if listing_id not in by_retailer:
            run.record(row, product_id, "FAILED", f"drift: product missing on WhatsApp (CREATE fixes)")
        else:
            run.record(row, product_id, "OK", "present on WhatsApp")
    for row in rows:
        if str(row.get("Availability") or "") in {"Rented Out", "On Hold"} and META_CHANNEL in _live_at(row):
            if str(row.get("listing_id") or "") in by_retailer:
                run.record(row, str(row.get("meta_catalog_id") or ""), "FAILED", "drift: leftover product for a Rented Out/On Hold row (DELETE fixes)")
    known_listings = {str(r.get("listing_id") or "") for r in rows}
    for retailer_id, product in by_retailer.items():
        if retailer_id and retailer_id not in known_listings:
            run.store.add_review_entry({
                "type": "Orphan product",
                "listing_id": "",
                "product_id": str(product.get("id") or ""),
                "found": f"WhatsApp product retailer_id={retailer_id} matches no Notion listing",
                "propose": "Review: delete product or adopt into a listing",
            })
            run.lines.append(log_line("reconcile", retailer_id, str(product.get("id") or ""), "FAILED", "orphan on WhatsApp; queued for review", now=run.now))
    run.counts["ok"] = sum(1 for l in run.lines if l.endswith("present on WhatsApp"))


def _execute_review_decision(run: _Run, entry: Mapping[str, Any]) -> None:
    """Execute one queued YOUR DECISION through the normal gated code path."""
    decision = str(entry.get("decision") or "").strip().lower()
    entry_id = str(entry.get("id") or "")
    row = entry.get("row") or {}
    result = "no action"
    try:
        if decision in {"reprocess", "apply fix"} and run.operation in ELIGIBLE:
            merged = dict(row)
            if entry.get("value"):
                merged["BHK"] = str(entry["value"])
            _execute(run.operation, run, merged)
            result = "executed via " + run.operation
        elif decision in {"ignore", "leave for now"}:
            result = decision
        elif decision == "delete product" and run.operation == "delete" and not run.dry_run:
            product_id = str(entry.get("product_id") or "")
            _call_with_retry(lambda: run.whapi.delete_product(product_id), sleeper=run.sleeper)
            run.lines.append(log_line("delete", str(entry.get("listing_id") or "?"), product_id, "OK", "review-queue decision", now=run.now))
            result = "product deleted"
        else:
            result = f"decision {decision!r} not applicable to {run.operation}"
    except Exception as exc:  # noqa: BLE001
        result = f"FAILED: {str(exc)[:160]}"
    if not run.dry_run:
        run.store.mark_review_done(entry_id, result)
