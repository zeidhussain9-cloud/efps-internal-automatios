# EFPS CRM — Housing Inventory Sync Runbook

> Verified 2026-11-12 14:50 IST / 09:20 UTC against the canonical Sheet, Supabase, Render and the five-minute cron.

## Source and boundary

- Canonical source: Google Sheet tab `Housing_Listings`.
- CRM reads operational columns A:AT only. Reserved AU/AV are not read into the operational CRM projection.
- The CRM sync is read-only against Google Sheets. The Slack intake workflow owns Sheet writes.
- Supabase table: `public.crm_inventory_snapshot`.
- Change history: `public.crm_inventory_sync_changes`.
- Render service: `srv-darsv560tbcc73cu4ip0`; branch: `crm-ui-dashboard`.
- Sync endpoint: HMAC-protected; invoked by Supabase cron `crm_inventory_sheet_reconcile_5m` every five minutes.

## Current verified state

- Canonical Sheet rows: **104**.
- Supabase active snapshot: **104** — 87 Available / 17 Rented Out.
- Latest scheduled successful sync: **2026-11-12 09:20:01 UTC** — 104 rows / 0 changed / 0 removed, HTTP 200.
- First catch-up sync after release: **09:11:54 UTC** — 104 rows / 104 changed / 0 removed, HTTP 200.
- The catch-up ledger recorded 16 created listings and 123 field-level changes across existing rows; no rows were removed. The the 09:15 and 09:20 scheduled runs were stable at 0 changes.
- `crm_inventory_sheet_reconcile_5m` remains active at `*/5 * * * *`.

## Confirmed 502 cause and repair

The 502 was caused by transaction ordering in `src/inventory-sync.mjs`:

1. The sync generated `crm_inventory_sync_changes` rows referencing a `run_id`.
2. It inserted those child rows before inserting the parent `crm_inventory_sync_runs` row.
3. The `crm_inventory_sync_changes.run_id` foreign key rejected the child insert.
4. The transaction rolled back and the protected endpoint returned HTTP 502.

The code now inserts the parent sync-run row first, then its child change-history rows in the same transaction. A regression test asserts this ordering. The first catch-up and next scheduled run both returned HTTP 200.

## Slack property batch — 12 November 2026

The intake bot posted 17 listing confirmations. A direct read-only fetch of the canonical Sheet returned 104 rows and matched 16 unique IDs. Supabase contains the same 16 rows, all active and Available:

- `EF-2611-VN4A`
- `EF-2611-G5ZS`
- `EF-2611-JBVP`
- `EF-2611-ZEFZ`
- `EF-2611-6JYX`
- `EF-2611-97J4`
- `EF-2611-79F1`
- `EF-2611-98PS`
- `EF-2611-Q2GV`
- `EF-2611-WVP3`
- `EF-2611-9ZZJ`
- `EF-2611-XXHD`
- `EF-2611-5NZA`
- `EF-2611-KQ44`
- `EF-2611-3Q39`
- `EF-2611-B42K`

`EF-2611-NFHV` is not a separate current Sheet row. Its Bellandur 2-BHK / ₹40K / 2-of-5 floor / Nov 15 listing details are repeated in the later `EF-2611-B42K` entry, which adds the explicit `Semi Gated` property type and 10 photos. Do not insert NFHV again as a second property; treat it as a duplicate/replaced intake.

### Review-state preservation

Eight Slack confirmations initially reported `Needs Review`: `EF-2611-9ZZJ`, `EF-2611-6JYX`, `EF-2611-XXHD`, `EF-2611-5NZA`, `EF-2611-NFHV`, `EF-2611-WVP3`, `EF-2611-97J4`, and `EF-2611-G5ZS`.

The current canonical Sheet has no active `Needs Review` rows. The seven surviving IDs now have `status=Pending`, `internal_property_type=Semi Gated`, and empty `error_notes`; NFHV is the duplicate/replaced record. The CRM sync did not write to or change the Sheet. It mirrored the source values as found. Do not re-open those rows without a new validation finding.

## Verification and operating rules

- Empty Sheet snapshots are rejected to prevent mass tombstoning.
- Snapshot writes, parent sync-run creation, change-ledger inserts and activity logging are transactional and protected by an advisory lock.
- A failed run must be diagnosed from Render application logs and the corresponding `net._http_response` row; the endpoint's public error body intentionally does not expose internal exception details.
- Never write to the canonical Sheet from the CRM sync path.
- Do not treat inventory edit history before `crm_inventory_sync_changes` was introduced as reconstructable.
- Production UI root and health endpoint return HTTP 200. The inventory API requires an operator session; unauthenticated access correctly returns HTTP 401. The live Supabase snapshot is the UI's inventory source.