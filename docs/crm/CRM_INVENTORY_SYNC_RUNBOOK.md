# EFPS CRM — Housing Inventory Sync Runbook

> Historical Sheet scheduler repair revalidated 2026-11-12. Notion ownership and projection updated 2026-11-13.

## Canonical editor transition — 2026-11-13

- Notion Housing Listings is the canonical operator editing surface. New Notion pages and edits are designed to write directly into the existing `public.crm_inventory_snapshot` projection under `source_kind='housing_notion'`.
- Supabase schema migration, `notion-inventory-state` Edge Function v4, and the isolated Notion Lambda are deployed. The existing Connection webhook and all eight Page event selections are user-confirmed.
- The one-time backfill accepted 104 Housing Listings pages; Supabase confirms 104 active `housing_notion` rows and 104 processed events.
- The five-minute Sheet reconciliation cron was unscheduled on 2026-11-13. Dashboard inventory now reads Notion-owned (`housing_notion`) rows only.
- Keep all eight Notion Page events selected: `page.content_updated`, `page.created`, `page.deleted`, `page.locked`, `page.moved`, `page.properties_updated`, `page.undeleted`, and `page.unlocked`.
- Existing AWS Secrets Manager records were not changed, duplicated, or rotated. The old WhAPI `NEW`-delimited listener remains untouched until final cleanup.

## Source and boundary

- Current source: Notion Housing Listings. Historical source: Google Sheet tab Housing_Listings. Legacy Sheet intake writes do not feed the dashboard.
- CRM reads operational columns A:AT only; reserved AU/AV are excluded.
- Dashboard sync reads only active Notion-owned rows. Sheet writes are still performed by the Slack operator intake and raw-intake compatibility flow, but those rows are excluded from the dashboard inventory. The old WhAPI NEW-delimited inventory listener is legacy and retained only until final cleanup; it is not the current Notion workflow. The direct Notion Housing Listings mirror is deployed and its 104-page backfill is verified. Raw Property Intake with photos remains separately dependent on the existing Sheet/Cloudinary/Maps runtime secrets.
- Supabase snapshot: public.crm_inventory_snapshot.
- Change history: public.crm_inventory_sync_changes.
- Render service: srv-darsv560tbcc73cu4ip0; production branch: crm-ui-dashboard.
- Supabase cron `crm_inventory_sheet_reconcile_5m` was removed on 2026-11-13; Notion page events update the projection directly.

## Current verified state

- Supabase active snapshot: 104 — 87 Available / 17 Rented Out.
- Current projection: 104 active Notion rows, 87 Available and 17 Rented; all 104 page intake events are processed. No Sheet-owned or test listings remain.
- The last observed 502 and twelve following HTTP 200 responses belong to the historical Sheet-reconciliation repair window (2026-11-12); that scheduler has since been removed.
- The old Sheet cron is disabled; verify future inventory changes through Notion page events and the Supabase projection.

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
- Never write to the compatibility Sheet from the CRM snapshot reconciliation path.
- Do not treat inventory history before crm_inventory_sync_changes existed as reconstructable.
- The authenticated inventory UI remains unverified in this follow-up; Supabase mirror presence alone does not prove a user-visible card rendered.
