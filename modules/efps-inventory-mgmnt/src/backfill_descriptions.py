"""Safe, idempotent backfill for the three Housing Listings descriptions.

Default mode is read-only. Use --apply --expected-count 110 only after reviewing
the dry-run report. Existing non-empty new fields are never overwritten.
"""
from __future__ import annotations

import argparse
import json
import os
import re
from collections import Counter

try:
    from .notion_intake import (
        NotionClient,
        listing_snapshot,
        _rich,
        _short_mobile_maps_url,
        build_catalogue_description,
    )
    from .description_generators import (
        build_whatsapp_group_description,
        build_facebook_marketplace_description,
    )
except ImportError:
    from notion_intake import (
        NotionClient,
        listing_snapshot,
        _rich,
        _short_mobile_maps_url,
        build_catalogue_description,
    )
    from description_generators import (
        build_whatsapp_group_description,
        build_facebook_marketplace_description,
    )


NEW_FIELDS = (
    "whatsapp_group_description",
    "whatsapp_catalogue_description",
    "facebook_marketplace_description",
)


def _maps_verification_evidence(raw_text: str, existing_group: str):
    raw_urls = re.findall(r"https?://[^\s<>]+", str(raw_text or ""), flags=re.I)
    short_link = next(
        (
            url.rstrip(".,);]")
            for url in raw_urls
            if _short_mobile_maps_url(url.rstrip(".,);]"))
        ),
        "",
    )
    prior_label = re.search(
        r"\*📍\s*([^*]+):\*\s*\n(https://[^\s]+)",
        str(existing_group or ""),
    )
    verified = bool(short_link and prior_label)
    label = prior_label.group(1).strip() if verified else ""
    return verified, label


def generate_descriptions(page: dict) -> tuple[dict, list[str]]:
    """Generate outputs without writing to Notion or Supabase."""
    row = listing_snapshot(page)
    raw_text = str(row.get("raw_message_text") or "")
    existing_group = str(
        row.get("whatsapp_group_description") or row.get("whatsapp_post") or ""
    )
    maps_verified, verified_label = _maps_verification_evidence(raw_text, existing_group)
    if verified_label.casefold() == str(row.get("locality") or "").strip().casefold():
        verified_label = ""

    issues: list[str] = []
    group = build_whatsapp_group_description(
        row,
        raw_text,
        verified_society_name=verified_label,
        maps_verified=maps_verified,
        issues=issues,
    )

    # Catalogue formatter is approved unchanged. Existing Catalogue descriptions
    # are copied byte-for-byte; only rows without the old value are rebuilt.
    catalogue = str(row.get("catalogue_description") or "").strip()
    if not catalogue:
        catalogue = build_catalogue_description(row, raw_text)

    facebook = build_facebook_marketplace_description(row, raw_text)
    return {
        "whatsapp_group_description": group,
        "whatsapp_catalogue_description": catalogue,
        "facebook_marketplace_description": facebook,
    }, issues


def run_backfill(*, apply: bool = False, expected_count: int | None = None) -> dict:
    token = os.environ.get("NOTION_API_TOKEN", "").strip()
    notion = NotionClient(token)
    notion.validate_listing_schema()
    pages = notion.list_listings()

    if expected_count is not None and len(pages) != expected_count:
        raise RuntimeError(
            f"Expected {expected_count} Housing Listings rows, found {len(pages)}; no writes performed."
        )

    summary = Counter()
    review_rows = []
    failed_rows = []
    planned = []

    for page in pages:
        page_id = str(page.get("id") or "")
        row = listing_snapshot(page)
        listing_id = str(row.get("listing_id") or page_id)
        generated, issues = generate_descriptions(page)
        summary["rows"] += 1
        for field in NEW_FIELDS:
            if generated[field]:
                summary[f"{field}_generated"] += 1
            else:
                summary[f"{field}_missing"] += 1
        if issues:
            review_rows.append({"listing_id": listing_id, "issues": issues})

        props = page.get("properties") or {}
        write_payload = {}
        for field in NEW_FIELDS:
            existing = str(row.get(field) or "").strip()
            if existing:
                summary[f"{field}_already_populated"] += 1
                continue
            if generated[field]:
                write_payload[field] = _rich(generated[field])
        if len(write_payload) != len(NEW_FIELDS) and not all(
            str(row.get(field) or "").strip() or generated[field] for field in NEW_FIELDS
        ):
            failed_rows.append(listing_id)
        if write_payload:
            planned.append((page_id, listing_id, write_payload))

    summary["rows_with_review_notes"] = len(review_rows)
    summary["rows_missing_one_or_more_outputs"] = len(failed_rows)
    summary["rows_to_update"] = len(planned)

    if failed_rows:
        summary["apply_blocked"] = 1
    elif apply:
        for page_id, listing_id, payload in planned:
            notion.update_page(page_id, payload)
            saved = listing_snapshot(notion.get_page(page_id))
            mismatches = [
                field for field in payload
                if str(saved.get(field) or "") != "".join(
                    part.get("text", {}).get("content", "")
                    for part in payload[field].get("rich_text", [])
                )
            ]
            if mismatches:
                raise RuntimeError(
                    f"Read-back verification failed for {listing_id}: {', '.join(mismatches)}"
                )
            summary["rows_written_and_verified"] += 1
    else:
        summary["dry_run_only"] = 1

    result = {
        "summary": dict(summary),
        "review_rows": review_rows,
        "failed_rows": failed_rows,
        "apply": bool(apply),
    }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Write missing new fields to Notion.")
    parser.add_argument("--expected-count", type=int, help="Abort unless live row count matches.")
    args = parser.parse_args()
    if args.apply and args.expected_count is None:
        parser.error("--apply requires --expected-count as a row-count safety guard.")
    result = run_backfill(apply=args.apply, expected_count=args.expected_count)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["failed_rows"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
