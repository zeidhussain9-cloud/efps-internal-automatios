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
# Per-BATCH sizes, not nightly totals: the scheduler chains batches until nothing
# is left. Create is 3 because every created product waits CREATE_ASSIGN_GAP_SECONDS
# (30s) plus several Whapi calls and one Lambda invocation lasts at most 180s.
# Deadline guard (create). Worst case of one row with NO Whapi retries (a 429 stops
# the row): adoption lookup 30s + create_product 30s + 30s gap + verify get_product
# 30s + 3 Notion calls x 25s = 195s, so a row only STARTS with >=210s left (needs
# Lambda Timeout 300s). CREATE_TAIL_SECONDS is re-checked immediately before the
# one irreversible step (create_product): after it, the remaining work is at most
# 30 + 30 + 75 = 135s, rounded up to 170s of margin.
CREATE_TAIL_SECONDS = 170
ROW_TIME_NEEDED_SECONDS = {"create": 210, "update": 60, "delete": 60, "assign": 60, "reconcile": 0}
CAPS = {"create": 3, "update": 10, "delete": 3, "assign": 20}
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


class RateLimited(RuntimeError):
    """Whapi answered 429. Per Whapi's soft-ban guidance the number must rest: no retry."""


class DeferredForTime(RuntimeError):
    """Not enough Lambda time left to finish a row safely; nothing was created."""


def _call_once(fn: Callable[[], Any]) -> Any:
    """Create-flow Whapi call: ONE attempt. A 429 stops the whole batch (no retry,
    no further writes) so the number is left to rest, as Whapi's 429 soft-ban page advises."""
    try:
        return fn()
    except Exception as exc:  # noqa: BLE001
        if _is_rate_limited(exc):
            raise RateLimited(f"Whapi 429 rate limit; stopped to let the number rest, no retry: {str(exc)[:120]}") from exc
        raise


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


# --- eligibility ---
# Locked 24 Nov 2026 (Zeid 3:32 PM, build approved): four-condition NEW
# creation selection. Rows with an old product ID are excluded (relisting is
# parked). Collection assignment is a separate flow and plays no part here.
def eligible_create(row: Mapping[str, Any]) -> bool:
    return (
        str(row.get("Pipeline Status") or "") == "Ready To Post"
        and str(row.get("Availability") or "") == "Available"
        and META_CHANNEL not in _live_at(row)
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
    # Locked 21 Nov (Zeid): ONLY Rented Out/On Hold arms deletion. A missing
    # Legacy "Post to Catalogue" tick never qualifies - legacy products
    # predate the retired tick system; unticked is the normal live state.
    return str(row.get("Availability") or "") in {"Rented Out", "On Hold"}


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
        self.time_left: Callable[[], float] | None = None
        self.stop = False
        self.catalogue_cache: list[dict] | None = None

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


def run_operation(operation: str, *, store: Any, whapi: Any, masters: Mapping[str, bool], now: datetime | None = None, sleeper: Callable[[float], None] = time.sleep, time_left: Callable[[], float] | None = None) -> dict[str, Any]:
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
    run.time_left = time_left
    if time_left is not None:
        try:
            store.time_left = time_left  # bounds the Notion store's own 429 sleeps
        except Exception:  # noqa: BLE001 - fakes without the attribute
            pass

    if operation != "reconcile":
        if not (states["EFPS_WHAPI_LIVE"] and states["EFPS_WHAPI_API_ENABLED"]):
            run.lines.append(log_line(operation, "-", "", "FAILED", "master kill switch off; nothing ran", now=now))
            run.counts["failed"] += 1
            return run.summary(states)
        if not states[SWITCH_BY_OPERATION[operation]]:
            run.lines.append(log_line(operation, "-", "", "SKIPPED", f"{SWITCH_BY_OPERATION[operation]} switch off; nothing ran", now=now))
            run.counts["skipped"] += 1
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
        if operation == "create":
            # Rows that can never be created this run (missing details) are
            # reported but must not take batch slots from creatable rows.
            creatable = []
            for row in eligible:
                problem, _images = create_precheck(row)
                if problem:
                    run.record(row, "", "SKIPPED", problem)
                else:
                    creatable.append(row)
            eligible = creatable
        for row in eligible[:cap]:
            # Deadline guard: one create row is at most ~30s gap + 3 Whapi calls of
            # up to 30s each, plus one 429 wait+retry per call. Never START a row
            # without that much Lambda time left; the chain resumes in a new
            # invocation (the row is untouched, re-read fresh, adoption-checked).
            if run.stop or (time_left is not None and time_left() < ROW_TIME_NEEDED_SECONDS[operation]):
                break
            _execute(operation, run, row)
        over_cap = eligible[cap:]
        if run.dry_run:
            for row in over_cap:
                run.record(row, str(row.get("meta_catalog_id") or ""), "SKIPPED", f"per-run cap {cap} reached; row waits for next run")
        else:
            # Permanent design (approved 21 Nov): real runs write notes only for rows
            # actually acted on. Over-cap rows are counted, and one summary line keeps
            # the audit trail without a per-row Notion write (which tripped Notion's 429).
            run.counts["skipped"] += len(over_cap)
            if over_cap:
                run.lines.append(log_line(operation, "-", "", "SKIPPED",
                                          f"{len(over_cap)} rows over per-run cap {cap}; wait for next run", now=now))

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
    except DeferredForTime as exc:
        run.stop = True
        run.record(row, "", "SKIPPED", str(exc)[:200])
    except RateLimited as exc:
        run.stop = True  # no further Whapi writes this batch; the scheduler also stops the chain (failed>0)
        run.record(row, str(row.get("meta_catalog_id") or ""), "FAILED", str(exc)[:200])
    except Exception as exc:  # noqa: BLE001 - any failure is logged, row stays for next run
        run.record(row, str(row.get("meta_catalog_id") or ""), "FAILED", str(exc)[:200])


def _adoption_catalogue(run: "_Run") -> list[dict]:
    """The catalogue for the duplicate check, read ONCE per batch (pages of 100, each
    page one attempt, no retry) and kept fresh by appending what this batch creates.
    Before every page the deadline must leave room for that page (30s) plus the
    create tail, otherwise the row is deferred with nothing created."""
    if run.catalogue_cache is None:
        def before_page() -> None:
            if run.time_left is not None and run.time_left() < 30 + CREATE_TAIL_SECONDS:
                raise DeferredForTime("not enough Lambda time left to read the catalogue safely; nothing created, next batch continues")
        try:
            run.catalogue_cache = list(_call_once(lambda: run.whapi.get_products(count=10000, before_page=before_page)) or [])
        except TypeError:  # test fakes that do not take the hook
            run.catalogue_cache = list(_call_once(lambda: run.whapi.get_products(count=10000)) or [])
    return run.catalogue_cache


_UNKNOWN = "OUTCOME UNKNOWN"


def _create_outcome_unknown(notes: str) -> bool:
    """True when the row's log shows a create whose result was never seen and no
    later OK/ADOPTED line settled it."""
    unknown = False
    for line in str(notes or "").splitlines():
        if " CREATE " not in line:
            continue
        if _UNKNOWN in line:
            unknown = True
        elif " OK " in line or " ADOPTED " in line:
            unknown = False
    return unknown


def create_precheck(row: Mapping[str, Any]) -> tuple[str, list[str]]:
    """Return (problem, images). problem is "" when the row can be created."""
    if not str(row.get("listing_id") or "").strip():
        return "listing_id blank; skipped", []
    if not str(row.get("catalog_title") or "").strip():
        return "catalog_title blank; skipped", []
    if not str(row.get("catalogue_description") or "").strip():
        return "catalogue_description blank; skipped", []
    try:
        rent = int(row.get("monthly_rent") or 0)
    except (TypeError, ValueError):
        rent = 0
    if rent <= 0:
        return "monthly_rent not a positive number; skipped", []
    images = [u for u in str(row.get("cloudinary_image_urls") or "").replace(",", " ").split() if u.strip()][:10]
    if not images:
        return "no photos; skipped", []
    return "", images


def _op_create_row(run: _Run, row: Mapping[str, Any]) -> None:
    # Pre-checks locked 24 Nov 2026: missing/invalid required details = skip
    # with the exact reason, no guessing. Collection ID is NOT required -
    # assignment is a separate flow (Zeid 3:04 PM).
    problem, images = create_precheck(row)
    title = str(row.get("catalog_title") or "").strip()
    description = str(row.get("catalogue_description") or "").strip()
    listing_id = str(row.get("listing_id") or "").strip()
    try:
        rent = int(row.get("monthly_rent") or 0)
    except (TypeError, ValueError):
        rent = 0
    if problem:
        run.record(row, "", "SKIPPED", problem)
        return
    if run.dry_run:
        run.record(row, "", "WOULD", f"create product '{title}' with {len(images)} photos")
        return

    # Re-read the row immediately before acting: Notion may have changed since the
    # batch snapshot. Anything no longer eligible is skipped, never created.
    fresh = run.store.read_listing(str(row.get("page_id") or ""))
    if not eligible_create(fresh) or str(fresh.get("listing_id") or "").strip() != listing_id:
        run.record(row, "", "SKIPPED", "no longer eligible when re-checked just before creation; skipped")
        return
    for field in ("catalog_title", "catalogue_description", "monthly_rent", "cloudinary_image_urls"):
        if str(fresh.get(field) or "").strip() != str(row.get(field) or "").strip():
            run.record(row, "", "SKIPPED", f"{field} changed since the batch read; skipped, next run re-evaluates")
            return

    # Adoption: never create a duplicate, and never adopt on existence alone:
    # the existing product must match the intended content before Notion is written.
    catalogue = _adoption_catalogue(run)
    matches = [p for p in catalogue if str(p.get("product_retailer_id") or "") == listing_id]
    if len(matches) > 1:
        ids = ", ".join(str(m.get("id")) for m in matches)
        raise RuntimeError(f"{len(matches)} catalogue products share listing_id {listing_id} ({ids}); row stopped for manual review, nothing adopted or created")
    existing = matches[0] if matches else None
    if existing:
        product_id = str(existing.get("id") or "")
        live = _call_once(lambda: run.whapi.get_product(product_id))
        mismatch = _content_mismatch(live, title, description, rent, images, str(row.get("google_maps_url") or ""))
        if mismatch:
            raise RuntimeError(f"existing product {product_id} does not match intended content ({mismatch}); not adopted, Notion untouched")
        _mark_posted(run, row, product_id)
        run.record(row, product_id, "ADOPTED", "product already existed on WhatsApp")
        return

    if run.time_left is not None and run.time_left() < CREATE_TAIL_SECONDS:
        raise DeferredForTime("not enough Lambda time left to create and verify safely; nothing created, next batch continues")
    if _create_outcome_unknown(str(row.get("error_notes") or "")):
        run.record(row, "", "SKIPPED", "an earlier create for this row has an unknown result and no matching product is visible in the catalogue; not creating again until checked in Meta")
        return
    try:
        result = _call_once(
            lambda: run.whapi.create_product(
                name=title, description=description, price=rent, currency="INR",
                images=images, url=str(row.get("google_maps_url") or ""), product_retailer_id=listing_id,
            ),
        )
    except RateLimited:
        raise  # Whapi answered 429: the request was refused, nothing was created
    except Exception as exc:  # noqa: BLE001 - the request may have reached Meta
        run.stop = True
        raise RuntimeError(f"create request failed with no readable answer ({str(exc)[:80]}); {_UNKNOWN}, product may exist; stopped, later runs will not re-create this row until checked") from exc
    if isinstance(result, str):
        run.stop = True
        raise RuntimeError(f"WhAPI error response ({result[:80]}); {_UNKNOWN}, product may exist; stopped")
    product_id = str((result or {}).get("id") or (result or {}).get("product_id") or "")
    if not product_id:
        run.stop = True
        raise RuntimeError(f"WhAPI returned no product ID ({str(result)[:80]}); {_UNKNOWN}, product may exist; stopped")
    # Verify before writeback (locked order, 24 Nov): read the product back and
    # confirm it exists with the intended name before touching Notion.
    run.sleeper(CREATE_ASSIGN_GAP_SECONDS)  # 30s spacing between catalogue requests
    live_product = _call_once(lambda: run.whapi.get_product(product_id))
    if not str((live_product or {}).get("name") or "").strip():
        raise RuntimeError(f"created product {product_id} not readable on verification; Notion untouched")
    mismatch = _content_mismatch(live_product, title, description, rent, images, str(row.get("google_maps_url") or ""))
    if mismatch:
        raise RuntimeError(f"created product {product_id} content mismatch ({mismatch}); Notion untouched")
    if run.catalogue_cache is not None:
        run.catalogue_cache.append({"id": product_id, "product_retailer_id": listing_id})
    _mark_posted(run, row, product_id)
    run.record(row, product_id, "OK", "created and verified")
    # Collection assignment is deliberately NOT chained here (Zeid 3:04 PM):
    # it runs as its own separately-gated flow.


def _content_mismatch(product: Mapping[str, Any] | None, title: str, description: str, rent: int,
                      images: list[str] | None = None, url: str = "") -> str:
    """Empty string when the live product matches intent; else which fields differ."""
    def norm(v: Any) -> str:
        return " ".join(str(v or "").split())
    p = product or {}
    bad = []
    if norm(p.get("name")) != norm(title):
        bad.append("name")
    if norm(p.get("description")) != norm(description):
        bad.append("description")
    try:
        if int(float(p.get("price"))) != int(rent):
            bad.append("price")
    except (TypeError, ValueError):
        bad.append("price")
    if images is not None:
        # Meta may re-host photo links, so compare the COUNT of photos, and exact
        # links only when the product returns links that look like our originals.
        live_images = [str(i.get("link") if isinstance(i, dict) else i) for i in (p.get("images") or [])]
        if len(live_images) != len(images):
            bad.append(f"photos ({len(live_images)} live vs {len(images)} intended)")
    if url and p.get("url") is not None and norm(p.get("url")) != norm(url):
        bad.append("link")
    return ", ".join(bad)


def _mark_posted(run: _Run, row: Mapping[str, Any], product_id: str) -> None:
    # Writeback locked 24 Nov 2026 (Zeid): product ID + Meta Catalogue in
    # live at + Pipeline Status -> Posted; the run record also appends the
    # audit line to error_notes. Posted = live on at least one platform.
    live = _live_at(row)
    if META_CHANNEL not in live:
        live = live + [META_CHANNEL]
    run.store.update_listing(str(row.get("page_id") or ""), {
        "meta_catalog_id": product_id,
        "live at": live,
        "Pipeline Status": "Posted",
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
    reason = f"Availability={row.get('Availability')}"
    if run.dry_run:
        run.record(row, product_id, "WOULD", f"delete product ({reason})")
        return
    try:
        _call_with_retry(lambda: run.whapi.delete_product(product_id), sleeper=run.sleeper)
        note = f"deleted ({reason})"
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
            if run.dry_run:
                run.lines.append(log_line("reconcile", retailer_id, str(product.get("id") or ""), "WOULD", "orphan on WhatsApp; would queue for review", now=run.now))
                continue
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
