# EFPS CRM — Housing Inventory Sync Runbook

> Revalidated 2026-11-12 against production Supabase, Render, the deployed sync code and the recorded source audit.

## Source and boundary

- Canonical source: Google Sheet tab Housing_Listings.
- CRM reads operational columns A:AT only; reserved AU/AV are excluded.
- CRM sync is read-only against Google Sheets. Slack intake owns Sheet writes.
- Supabase snapshot: public.crm_inventory_snapshot.
- Change history: public.crm_inventory_sync_changes.
- Render service: srv-darsv560tbcc73cu4ip0; production branch: crm-ui-dashboard.
- Supabase cron crm_inventory_sheet_reconcile_5m invokes the HMAC-protected endpoint every five minutes.

## Current verified state

- Supabase active snapshot: 104 — 87 Available / 17 Rented Out.
- Latest successful run observed: 2026-11-12 09:55:01 UTC, 104 rows / 0 changed / 0 removed.
- The recovery audit recorded a direct source Sheet read of 104 rows. The Google Drive connector is disabled by admin in the current ChatGPT environment, so this follow-up verified the production mirror and sync-run evidence but did not repeat the independent Sheet read.
- The last observed 502 was at 09:10 UTC. Twelve HTTP 200 responses followed through 09:55 UTC; no later 502 was present in the queried response window.
- The five-minute cron remains active.

## Confirmed 502 cause and repair

The sync transaction inserted child rows in crm_inventory_sync_changes before inserting the parent crm_inventory_sync_runs row. The child run_id foreign key rejected the insert and rolled back the transaction. The code now inserts the parent row first and then its child change-history rows in the same transaction. A regression test asserts this ordering.

## Slack property batch — 12 November 2026

The intake bot confirmed 17 IDs. Sixteen are present in the current Supabase mirror:

- EF-2611-VN4A
- EF-2611-G5ZS
- EF-2611-JBVP
- EF-2611-ZEFZ
- EF-2611-6JYX
- EF-2611-97J4
- EF-2611-79F1
- EF-2611-98PS
- EF-2611-Q2GV
- EF-2611-WVP3
- EF-2611-9ZZJ
- EF-2611-XXHD
- EF-2611-5NZA
- EF-2611-KQ44
- EF-2611-3Q39
- EF-2611-B42K

EF-2611-NFHV is a duplicate/replaced intake represented by EF-2611-B42K; do not insert NFHV separately.

## Needs Review preservation

The eight original Slack warnings were for G5ZS, 6JYX, 97J4, WVP3, NFHV, 9ZZJ, XXHD and 5NZA. Seven surviving IDs now show internal_property_type=Semi Gated and empty error_notes; NFHV is replaced by B42K. The current mirror has no separate Needs Review marker, and no execution log proves how each warning was cleared. WVP3 still has an empty property_subtype, matching its original Slack warning. Keep WVP3 under review pending operator validation; do not silently mark it ready.

## Operating rules

- Empty Sheet snapshots are rejected to prevent mass tombstones.
- Snapshot upserts, parent sync-run creation, change-ledger inserts and activity logging are transactional and protected by an advisory lock.
- A failed run must be diagnosed from Render application logs and its net._http_response record; the public endpoint intentionally hides internal exception details.
- Never write to the canonical Sheet from the CRM sync path.
- Do not treat inventory history before crm_inventory_sync_changes existed as reconstructable.
- The authenticated inventory UI remains unverified in this follow-up; Supabase mirror presence alone does not prove a user-visible card rendered.