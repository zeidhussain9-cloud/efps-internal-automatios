"""Notion-backed store for the gated catalogue runner.

Implements the store protocol that catalogue_runner.run_operation expects,
against the live Notion tables:

- Housing Listings DB: the listing rows (source of truth for catalogue state).
- Catalogue Switches DB: one row per master switch (Enabled checkbox).
- Catalogue Control Panel DB: one row per operation (Run checkbox + summary).
- Catalogue Review Queue DB: human-decision queue.

Runs inside the intake Lambda with the same Notion token. Every read/write
goes through the Notion API; nothing is cached across runs. Failures raise so
the runner's fail-closed behaviour applies.
"""

from __future__ import annotations

from datetime import datetime, timezone

import time

import requests

NOTION_VERSION = "2022-06-28"

LISTINGS_DATABASE_ID = "bccfd4f55e294b269daa093a928f873a"
SWITCHES_DATABASE_ID = "41ffedf9b4e88176ac8fd585f9cf1c01"
PANEL_DATABASE_ID = "41ffedf9b4e8815fb6cfd2ffe275110d"
QUEUE_DATABASE_ID = "41ffedf9b4e8817a979dd9176a795a0f"

META_CHANNEL = "Meta Catalogue"

_ERROR_NOTES_LIMIT = 1950


class CatalogueStoreError(RuntimeError):
    pass


def _plain(parts) -> str:
    return "".join(str(p.get("plain_text") or "") for p in (parts or []))


def _select_name(prop) -> str:
    select = (prop or {}).get("select") or {}
    return str(select.get("name") or "")


def listing_row(page: dict) -> dict:
    """Project a Housing Listings Notion page into the runner's row shape."""
    props = page.get("properties") or {}

    def text(name):
        return _plain((props.get(name) or {}).get("rich_text"))

    live = [
        str(o.get("name") or "")
        for o in ((props.get("live at") or {}).get("multi_select") or [])
        if o.get("name")
    ]
    return {
        "page_id": str(page.get("id") or ""),
        "listing_id": text("listing_id"),
        "Availability": _select_name(props.get("Availability")),
        "Pipeline Status": _select_name(props.get("Pipeline Status")),
        "BHK": text("BHK"),
        "catalog_title": text("catalog_title"),
        "whatsapp_catalogue_description": text("whatsapp_catalogue_description"),
        "monthly_rent": (props.get("monthly_rent") or {}).get("number") or 0,
        "cloudinary_image_urls": text("cloudinary_image_urls"),
        "google_maps_url": str((props.get("google_maps_url") or {}).get("url") or ""),
        "meta_catalog_id": text("meta_catalog_id"),
        "live at": live,
        "error_notes": text("error_notes"),
    }


def _retry_after_seconds(response) -> float:
    """Seconds Notion asks us to wait on a 429 (header or JSON body)."""
    try:
        header = float(response.headers.get("Retry-After") or 0)
    except (TypeError, ValueError):
        header = 0.0
    body = 0.0
    try:
        body = float((response.json().get("additional_data") or {}).get("retry_after") or 0)
    except (TypeError, ValueError):
        body = 0.0
    return max(header, body)


def _pinned_attempt_index(lines: list[str]) -> int | None:
    """Index of the newest CREATE line if it is an unsettled ATTEMPT STARTED (the
    duplicate-protection checkpoint); None when the latest create state is settled."""
    state = None
    for i, line in enumerate(lines):
        if " CREATE " not in line:
            continue
        if "ATTEMPT STARTED" in line or "OUTCOME UNKNOWN" in line:
            state = i
        elif " OK " in line or " ADOPTED " in line or " REFUSED" in line:
            state = None
    return state


def _trim_notes(combined: str) -> str:
    """Fit error_notes into Notion's 2000-char cell. Drop the OLDEST lines first, but
    never drop an unsettled ATTEMPT STARTED line (it is what stops a re-create). If the
    pinned line plus the newest line cannot fit, raise: fail closed, never lose it silently."""
    lines = combined.split("\n")
    pin = _pinned_attempt_index(lines)
    # any single line longer than the cell is cut, keeping its start
    lines = [l if len(l) <= 600 else l[:600] for l in lines]
    keep = list(range(len(lines)))
    while len("\n".join(lines[i] for i in keep)) > _ERROR_NOTES_LIMIT:
        drop = next((i for i in keep if i != pin and i != len(lines) - 1), None)
        if drop is None:
            raise CatalogueStoreError("error_notes cannot hold the pending create checkpoint and the new line; stopped rather than lose it")
        keep.remove(drop)
    return "\n".join(lines[i] for i in keep)


class NotionCatalogueStore:
    def __init__(self, token: str, *, session=None, now=None):
        if not token:
            raise CatalogueStoreError("Notion token is not configured")
        self.session = session or requests.Session()
        self.token = token
        self.time_left = None  # optional callable: seconds left in this Lambda invocation
        self._now = now or (lambda: datetime.now(timezone.utc))

    # --- low level ------------------------------------------------------

    def request(self, method: str, path: str, *, payload=None) -> dict:
        delay = 2.0
        for _attempt in range(5):
            response = self.session.request(
                method,
                "https://api.notion.com/v1/" + path.lstrip("/"),
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Notion-Version": NOTION_VERSION,
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=25,
            )
            if response.status_code != 429:
                break
            # Notion rate limit: honor retry-after, bounded exponential backoff.
            wait = min(max(_retry_after_seconds(response), delay), 30.0)
            if self.time_left is not None and self.time_left() < wait + 25 + 10:
                # Never sleep past the invocation: stop with a clear error instead.
                raise CatalogueStoreError(f"Notion API {method} {path} rate limited and not enough invocation time left to wait; stopped")
            time.sleep(wait)
            delay = min(delay * 2, 30.0)
        if not response.ok:
            raise CatalogueStoreError(
                f"Notion API {method} {path} failed ({response.status_code}): {response.text[:300]}"
            )
        return response.json() if response.content else {}

    def _query_all(self, database_id: str, *, filter_body=None) -> list[dict]:
        pages, cursor = [], None
        while True:
            payload = {"page_size": 100}
            if filter_body:
                payload["filter"] = filter_body
            if cursor:
                payload["start_cursor"] = cursor
            result = self.request("POST", f"databases/{database_id}/query", payload=payload)
            pages.extend(
                p for p in (result.get("results") or [])
                if not p.get("archived") and not p.get("in_trash")
            )
            if not result.get("has_more"):
                return pages
            cursor = result.get("next_cursor")
            if not cursor:
                raise CatalogueStoreError("Notion pagination returned no cursor")

    # --- runner protocol ------------------------------------------------

    def read_switches(self) -> dict:
        switches = {}
        for page in self._query_all(SWITCHES_DATABASE_ID):
            props = page.get("properties") or {}
            name = _plain((props.get("Name") or {}).get("title")).strip().upper()
            if name:
                switches[name] = bool((props.get("Enabled") or {}).get("checkbox"))
        return switches

    def query_listings(self) -> list[dict]:
        return [listing_row(p) for p in self._query_all(LISTINGS_DATABASE_ID)]

    def read_listing(self, page_id: str) -> dict:
        """Fresh single-row read, used to re-check eligibility right before a write."""
        return listing_row(self.request("GET", f"pages/{page_id}"))

    def update_listing(self, page_id: str, updates: dict) -> None:
        properties = {}
        if "meta_catalog_id" in updates:
            properties["meta_catalog_id"] = {
                "rich_text": [{"type": "text", "text": {"content": str(updates["meta_catalog_id"])}}]
            }
        if "live at" in updates:
            properties["live at"] = {
                "multi_select": [{"name": str(name)} for name in (updates["live at"] or [])]
            }
        if "Pipeline Status" in updates:
            properties["Pipeline Status"] = {"select": {"name": str(updates["Pipeline Status"])}}
        if not properties:
            return
        self.request("PATCH", f"pages/{page_id}", payload={"properties": properties})

    def append_activity(self, page_id: str, line: str) -> None:
        if not page_id:
            return
        page = self.request("GET", f"pages/{page_id}")
        current = _plain(((page.get("properties") or {}).get("error_notes") or {}).get("rich_text"))
        combined = (current + "\n" + str(line)).strip() if current else str(line)
        if len(combined) > _ERROR_NOTES_LIMIT:
            combined = _trim_notes(combined)
        self.request(
            "PATCH",
            f"pages/{page_id}",
            payload={"properties": {"error_notes": {"rich_text": [{"type": "text", "text": {"content": combined}}]}}},
        )

    def mark_product_id_removed(self, page_id: str, product_id: str) -> None:
        # The deleted product ID stays in meta_catalog_id for history, in red.
        self.request(
            "PATCH",
            f"pages/{page_id}",
            payload={
                "properties": {
                    "meta_catalog_id": {
                        "rich_text": [{
                            "type": "text",
                            "text": {"content": str(product_id)},
                            "annotations": {"color": "red"},
                        }]
                    }
                }
            },
        )

    def write_panel_summary(self, operation: str, result: dict) -> None:
        row = self._panel_row(operation)
        if not row:
            return
        counts = (result or {}).get("counts") or {}
        lines = (result or {}).get("lines") or []
        summary = (
            f"{'DRY RUN - ' if (result or {}).get('dry_run') else ''}"
            f"ok={counts.get('ok', 0)} failed={counts.get('failed', 0)} skipped={counts.get('skipped', 0)}"
        )
        if lines:
            summary += " | " + " ; ".join(str(l)[:80] for l in lines[:3])
        self.request(
            "PATCH",
            f"pages/{row['id']}",
            payload={
                "properties": {
                    "Run": {"checkbox": False},
                    "Last Run Summary": {"rich_text": [{"type": "text", "text": {"content": summary[:1900]}}]},
                    "Last Run At": {"date": {"start": self._now().isoformat()}},
                }
            },
        )

    def last_run_at(self, operation: str):
        """When the control-panel row's Last Run At was last written (a batch finished); None if never."""
        row = self._panel_row(operation)
        start = (((row or {}).get("properties") or {}).get("Last Run At") or {}).get("date") or {}
        value = start.get("start")
        if not value:
            return None
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)

    def _panel_row(self, operation: str) -> dict | None:
        for page in self._query_all(PANEL_DATABASE_ID):
            props = page.get("properties") or {}
            name = _plain((props.get("Name") or {}).get("title")).strip().lower()
            if name == str(operation).strip().lower():
                return page
        return None

    def read_review_decisions(self, operation: str) -> list[dict]:
        entries = []
        pages = self._query_all(
            QUEUE_DATABASE_ID,
            filter_body={"property": "Status", "select": {"equals": "Open"}},
        )
        rows_by_listing = None
        for page in pages:
            props = page.get("properties") or {}
            decision = _select_name(props.get("YOUR DECISION"))
            if not decision:
                continue
            listing_id = _plain((props.get("Listing ID") or {}).get("rich_text"))
            row = {}
            if listing_id:
                if rows_by_listing is None:
                    rows_by_listing = {r["listing_id"]: r for r in self.query_listings()}
                row = rows_by_listing.get(listing_id) or {}
            entries.append({
                "id": str(page.get("id") or ""),
                "decision": decision,
                "value": _plain((props.get("YOUR VALUE") or {}).get("rich_text")),
                "listing_id": listing_id,
                "product_id": _plain((props.get("Product ID") or {}).get("rich_text")),
                "row": row,
            })
        return entries

    def mark_review_done(self, entry_id: str, result: str) -> None:
        if not entry_id:
            return
        self.request(
            "PATCH",
            f"pages/{entry_id}",
            payload={
                "properties": {
                    "Status": {"select": {"name": "Done"}},
                    "Result": {"rich_text": [{"type": "text", "text": {"content": str(result)[:1900]}}]},
                }
            },
        )

    def add_review_entry(self, entry: dict) -> None:
        self.request(
            "POST",
            "pages",
            payload={
                "parent": {"database_id": QUEUE_DATABASE_ID},
                "properties": {
                    "Name": {"title": [{"type": "text", "text": {"content": str(entry.get("found") or "?")[:1900]}}]},
                    "Type": {"select": {"name": str(entry.get("type") or "Needs decision")}},
                    "Listing ID": {"rich_text": [{"type": "text", "text": {"content": str(entry.get("listing_id") or "")}}]},
                    "Product ID": {"rich_text": [{"type": "text", "text": {"content": str(entry.get("product_id") or "")}}]},
                    "What we propose": {"rich_text": [{"type": "text", "text": {"content": str(entry.get("propose") or "")[:1900]}}]},
                    "Status": {"select": {"name": "Open"}},
                },
            },
        )
