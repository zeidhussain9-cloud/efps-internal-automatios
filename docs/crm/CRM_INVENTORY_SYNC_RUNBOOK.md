# EFPS CRM — Housing Inventory Sync Runbook

## Current verified production checkpoint — 2026-11-14

- Notion Housing Listings is canonical; crm_inventory_snapshot is the CRM projection.
- Active Notion-owned projection: 106 rows; business_status Pending on all 106.
- Supabase notion-inventory-state ACTIVE v11. Render deploy dep-dbs2qnqjnfac73bq84sg LIVE on 2727b38. AWS efps-notion-intake update successful.
- 12 Notion events observed: 5 processed, 4 ignored non-intake changes, 1 rejected unauthenticated probe, 2 needs-review outcomes. Delivery capture completeness not certified.
- The form schema includes Raw Property Data and Photos; two existing submissions have photos but no raw text and remain Needs Review.
- Maps API-unavailable fallback deployed. No database tables deleted.

# EFPS CRM — Housing Inventory Sync Runbook

> Historical Sheet scheduler repair revalidated 2026-11-12. Notion ownership and projection updated 2026-11-13.

## Canonical editor transition — 2026-11-13

- Notion Housing Listings is the canonical operator editing surface. Supabase `public.crm_inventory_snapshot` remains the dashboard projection under `source_kind='housing_notion'`.
- Supabase `notion-inventory-state` ACTIVE v9 (JWT verification enabled); isolated AWS Lambda `efps-notion-intake` Active; stack `efps-notion-property-intake` `UPDATE_COMPLETE`.
- Full live reconciliation: 104 active Notion pages / 104 active Supabase rows; 0 missing, orphaned, duplicate or semantic field mismatches. All 104 intake events are processed and have Listing IDs matching their snapshot rows.
- Reserved AU/AV fields: `source_group` and `inventory_locked` are blank across all 104 pages; 43 prior `inventory_locked` values were cleared.
- A 15-minute EventBridge reconciliation queues only changed/restored pages, repairs event Listing IDs, and soft-deletes projections missing from the complete Notion result. Empty Notion results fail closed.
- Recovery fallback tested: rented listing `EF-2609-09B5` was soft-deleted through the worker and reactivated by scheduled reconciliation. Actual `page.undeleted` webhook delivery is not independently observed, but missed restore delivery is recovered by the fallback.
- All eight Page events remain user-confirmed and unchanged. Sheet reconciliation cron is removed. Legacy Sheet producers and the old WhAPI `NEW` listener remain untouched pending separately agreed cleanup.

## Source and boundary

- Current source: Notion Housing Listings. Historical source: Google Sheet tab Housing_Listings. Legacy Sheet intake writes do not feed the dashboard.
- CRM reads operational columns A:AT only; reserved AU/AV are excluded and blank.
- Dashboard reads active Notion-owned rows only. Raw Property Intake photo/enrichment remains a separate compatibility path using the existing Sheet/Cloudinary/Maps runtime credentials; their validity was not changed or reverified in this repair.
- Supabase snapshot: `public.crm_inventory_snapshot`; intake ledger: `public.crm_inventory_intake_events`.
- Render service: `srv-darsv560tbcc73cu4ip0`; production branch: `crm-ui-dashboard`.
- Supabase cron `crm_inventory_sheet_reconcile_5m` was removed on 2026-11-13. EventBridge Notion reconciliation now runs every 15 minutes.

## Current verified state

- Supabase active snapshot: 104 — 87 Available / 17 Rented Out; 0 soft-deleted rows.
- Source media gap (not a sync failure): 99/104 listings have Cloudinary image URLs. Five Rented Out pages have no image URL in Notion: `EF-2609-608J`, `EF-2609-22H0`, `EF-2609-VDWH`, `EF-2609-7JGF`, `EF-2609-MECJ`. The CRM mirrors the blank source values; no substitute images were invented.
- Intake ledger: 104 processed, 104 with Listing IDs, 104/104 mapped to snapshot rows; 0 failed/needs-review/stale.
- Initial mapping repair updated all 104 event Listing IDs. Latest v9 scheduled run: 104 checked, 0 queued, 104 unchanged, 0 further mapping updates, 0 soft-deletes.
- Async failure policy: 2 retries, 1-hour maximum event age, then SQS failure queue (14-day retention). CloudWatch log retention: 30 days.

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
- Signed-in production UI verification is complete: the edited Notion test listing appeared in the dashboard, and after cleanup the dashboard returned to 104 properties. Supabase mirror checks alone were not used as a substitute for this browser evidence.
- Live archive/delete was observed through Notion and soft-deleted the Supabase row after about one minute. Actual `page.undeleted` webhook delivery remains unobserved; however, the 15-minute reconciler successfully restored a soft-deleted active rented listing. Missed restore delivery is therefore recovered automatically without changing the Notion webhook settings.


## Latest verified inventory checkpoint — 2026-11-14

The live Notion-owned projection contains 106 active rows, not the historical 104-row count in the earlier checkpoint. crm_inventory_snapshot.business_status is a first-class projection field populated from source_record.status; all 106 current rows report Pending. The dashboard changes to filter and display this field are local and not yet deployed. Supabase notion-inventory-state was ACTIVE v10 before the latest local Edge Function update, which is now ACTIVE v11. No tables were deleted. Raw Property Intake end-to-end acceptance remains pending a real operator submission.
