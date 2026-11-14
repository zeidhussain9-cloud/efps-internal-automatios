## Current verified Notion listing-state control (2026-11-14)

The canonical Notion Housing Listings data source now defines listing_state as a SELECT with exactly three options: Available (green), Rented Out (red), and On Hold (yellow). Existing values were preserved: 89 Available and 17 Rented Out at verification; no existing property rows were bulk-edited. This is a Notion schema-only change; no Google Sheets sync, new data flow, Supabase schema change, webhook change, or dashboard code change was introduced. Existing Notion page-property webhook → Lambda → notion-inventory-state → crm_inventory_snapshot → CRM dashboard path remains unchanged.
## Historical inventory reconciliation checkpoint — 2026-11-13 (superseded by 2026-11-14 state)

# EFPS CRM — Housing Inventory Sync Runbook

## Current verified release — 2026-11-15 (Maps fallback correction)

- Repository: `zeidhussain9-cloud/efps-internal-automatios`; `main` and `crm-ui-dashboard` both point to `bb52959f2cf89f8609b291e13382eab22ce1b23a`; tracked tree SHA `f701f44edb74c6edb30b047c1912a05ff69fc0b8` is identical in both local worktrees and both GitHub branch refs.
- AWS: isolated stack `efps-notion-property-intake` is `UPDATE_COMPLETE`; Lambda `efps-notion-intake` Active / LastUpdateStatus Successful, Python 3.12, last modified `2026-11-14T19:48:46Z`, CodeSha256 `oyn+czp4YEH/um4aBdIagC4S+U4RunBq/VHH6IzVnwU=`. The downloaded live Lambda archive hash matches the Lambda CodeSha256. The 15-minute EventBridge reconciliation rule remains ENABLED.
- Maps behavior: absent/unreadable/placeholder credentials, billing/quota/authorization denials, and request/transport exceptions preserve the supported original short Maps URL as not verified and do not independently create `Needs Review`. Unverified Maps results never supply locality, pincode, coordinates or place name. Partial/mismatched verification, unsupported links, missing required fields/locality, AI conflicts and photo-limit violations remain review conditions.
- Supabase `notion-inventory-state` remains ACTIVE v12 with JWT verification enabled; no database schema, rows, secrets, or Edge Function were changed by this release. Render CRM UI was not changed or redeployed.
- Verification: Inventory + shared Maps pytest 174/174; Node 146/146; browser 1/1; production build; Python compileall; SAM lint/validate/build; generated SAM template validation; `git diff --check` all passed.
- No new production intake row was created. The existing synthetic test listing `EF-2611-SF6F` remains excluded from operational inventory reporting.


## Historical production checkpoint — 2026-11-14 (superseded by 2026-11-15 release)

- Notion Housing Listings is canonical; crm_inventory_snapshot is the CRM projection.
- 107 active Notion-owned rows, 1 soft-deleted tombstone, 0 active blank locality/society rows.
- Supabase locality projection has recovered to 107/107 active rows populated; the earlier 104/107 blank report was transient during the enabled 15-minute EventBridge reconciliation. No manual repair was applied.
- Raw-intake schema compatibility is corrected and deployed: the Lambda now serializes string-valued fields according to the live Notion type. CodeSha256 `oyn+czp4YEH/um4aBdIagC4S+U4RunBq/VHH6IzVnwU=`. Fresh operator-submitted raw-intake end-to-end acceptance remains pending; no synthetic production property was created.
- Render CRM service srv-darsv560tbcc73cu4ip0 is LIVE; the exact deployment ID and commit are authoritative in Render and are not duplicated here.
- Two recent property submissions have Processed status, raw data, photos, Housing Listings relations and matching active Supabase snapshots: EF-2611-PAGH and EF-2611-Y5KC.
- Existing property update path: edit the Housing Listings page; its Notion page event is processed by Lambda and notion-inventory-state, which upserts the same Listing ID into crm_inventory_snapshot. Do not resubmit the intake form to edit an existing listing.
- New property path: Submit New Property → intake worker → Housing Listings page → Supabase snapshot. The compatibility Sheets write was not independently checked for the two latest submissions.
- Notion webhook ledger currently contains 96 observed rows: 64 synced, 2 already processed, 26 ignored outcomes, 3 Needs Review, and 1 with no outcome. The 26 ignored outcomes are still stored with processing_status=failed; this status/outcome mismatch is an open ledger issue. Complete webhook delivery capture is not certified.
- Processing Notes append each processing outcome as a new line in the existing Notion cell; previous content is retained.
- Google Sheets status boundary: the connected Housing_Listings tab has a column-E dropdown with Available and Rented Out only; it has zero conditional-format rules. The Sheet11 reference lists no listing_state options. No Google Sheets edit-to-Supabase sync is live; existing property edits sync from Notion Housing Listings page events. The separate Sheet 2 source must be identified before copying its full vocabulary or color rules.
- No database tables deleted. Historical 104-row checkpoints below remain dated evidence only.

# EFPS CRM — Housing Inventory Sync Runbook

> Historical Sheet scheduler repair revalidated 2026-11-12. Notion ownership and projection updated 2026-11-13.

## Historical canonical-editor transition checkpoint — 2026-11-13

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

## Historical verified state — 2026-11-13

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


## Latest verified inventory checkpoint — 2026-11-14 (live check)

The live Notion-owned projection contains 107 active rows and 1 soft-deleted tombstone. business_status remains separate from source intake and availability states. Supabase notion-inventory-state is ACTIVE v12. Two Property Intake submissions are Processed and reconciled. EF-2611-YA84 is reconciled with Needs Review due to Maps unavailability and photo count above the 10-image limit. Raw intake compatibility Sheet row writes were not independently checked. Processing Notes now append each attempt as a new line in the same Notion cell. No tables were deleted.
