> Maps-only cutover verified 2026-11-15 14:12 IST: both Sydney stacks UPDATE_COMPLETE; all three live Lambda archives and bindings checked, no paid Google Maps/Places transport remains in the checked pipeline; source/client Google links remain. Scope, verification limits and provider caveats: [migration record](modules/efps-inventory-mgmnt/OLA_MAPS_MIGRATION.md). Older deployment snapshots below remain dated history. AI extraction is not part of this release.

## Current verified Notion listing-state control (2026-11-14)

## Current state — 2026-11-15: Google Sheet inventory sync removed

The legacy Google Sheet inventory path is fully retired: the CRM `/api/internal/inventory/sync` endpoint, the Sheet-to-Supabase mirror (`src/inventory-sync.mjs`, `src/housing-sheet-adapter.mjs`, `scripts/sync-housing-inventory.mjs`), the WhAPI `NEW` inventory listener (`webhook_handler.py`), the Slack `/efps` inventory commands and events handlers, the scheduled Sheet batch worker (`handler.py`), the Sheet batch/phase1 runtime modules, and the `shared/google_sheets` Sheets client are removed. `shared/google_sheets/schema.py` is RETAINED as the canonical field/vocabulary rulebook consumed by the Notion intake; Notion Housing Listings is the source of truth and Supabase remains the CRM projection. The Google service-account secret now serves only optional Vertex/Gemini enrichment. Dated sections below remain historical evidence.


The canonical Notion Housing Listings data source now defines listing_state as a SELECT with exactly three options: Available (green), Rented Out (red), and On Hold (yellow). Existing values were preserved: 89 Available and 17 Rented Out at verification; no existing property rows were bulk-edited. This is a Notion schema-only change; no Google Sheets sync, new data flow, Supabase schema change, webhook change, or dashboard code change was introduced. Existing Notion page-property webhook → Lambda → notion-inventory-state → crm_inventory_snapshot → CRM dashboard path remains unchanged.
## Current verified production state — Maps fallback release (2026-11-15)

- Maps API verification is optional enrichment. Missing/unreadable Maps credentials, billing/quota/authorization denial, and request/transport errors preserve the supported original Maps URL as not verified and do not independently mark intake Needs Review. The original link does not supply verified locality, pincode, coordinates, or place-name data.
- Genuine review conditions remain independent: missing/invalid required property fields, missing source locality, partial/mismatched Maps results, unsupported link formats, AI conflicts, and photo-limit violations. `EF-2611-YA84` remains deliberately Needs Review for its 18 photos exceeding the 10-image catalogue limit; Maps API unavailability alone is not a reason to keep it in review.
- Regression coverage includes API-unavailable results, transport exceptions, missing Maps secret, and partial-match review behavior. Current release evidence is recorded in `docs/DEPLOYMENT.md` and `docs/NOTION_PROPERTY_INTAKE.md`.

## Historical verified production state — 2026-11-14 (superseded by the 2026-11-15 Maps fallback release above)

- Raw-intake schema compatibility is corrected and deployed: the Lambda now serializes every string-valued field from the live Notion property type (`rich_text`, Select, or Status), validates options, and preserves the `listing_id` rich-text identity contract. Lambda CodeSha256: `oyn+czp4YEH/um4aBdIagC4S+U4RunBq/VHH6IzVnwU=`. Inventory tests 126/126, Node tests 146/146, browser 1/1, SAM validate/build and production build pass. A fresh operator-submitted raw intake remains the final end-to-end acceptance; no synthetic intake was created.

- Branches main and crm-ui-dashboard are synchronized with identical tracked trees; GitHub advertises exactly these two branch refs.
- Render CRM service srv-darsv560tbcc73cu4ip0 is LIVE; the exact deployment ID and commit are authoritative in Render and are not duplicated here.
- Supabase notion-inventory-state ACTIVE v12 (JWT verification enabled); migration 20261114095316_crm_inventory_business_status is registered and applied.
- AWS efps-notion-intake Active; LastUpdateStatus Successful; Maps API-unavailable fallback is deployed.
- Inventory projection: 107 active Notion-owned rows, 1 soft-deleted tombstone, 0 active rows with blank locality and society name.
- EF-2611-PAGH and EF-2611-Y5KC are Processed and reconciled. EF-2611-YA84 now has a canonical Housing Listings page and active Supabase snapshot; it remains Needs Review because 18 photos exceed the 10-image limit; Maps API unavailability alone is not a review reason.
- Notion webhook ledger currently contains 96 observed rows: 64 synced, 2 already processed, 26 ignored outcomes, 3 Needs Review, and 1 with no outcome. The 26 ignored outcomes are still stored with processing_status=failed; this status/outcome mismatch is an open ledger issue. Complete webhook delivery capture is not certified.
- Processing Notes now append each processing outcome as a new line in the same Notion cell; previous notes are retained. The change is deployed in AWS Lambda and covered by the current 126-test Inventory suite.
- Google Sheets status boundary: the connected Housing_Listings tab has a column-E dropdown with Available and Rented Out only; it has zero conditional-format rules. The Sheet11 reference lists no listing_state options. No Google Sheets edit-to-Supabase sync is live; existing property edits sync from Notion Housing Listings page events. The separate Sheet 2 source must be identified before copying its full vocabulary or color rules.
- No database tables deleted. The two latest compatibility Sheet writes were not independently verified.

## Historical initial Notion Property Intake deployment — 2026-11-14 08:14 UTC (v10; superseded)

Task 3 webhook event history is deployed. The existing `crm_inventory_intake_events` ledger was extended; no parallel webhook table was created and WhatsApp `crm_webhook_events` remains untouched. Supabase `notion-inventory-state` is ACTIVE v10; AWS `efps-notion-intake` and its stack are Active/UPDATE_COMPLETE. The live Notion form exposes both Raw Property Data and Photos. Awaiting the first operator-submitted property for end-to-end acceptance across Sheets, Cloudinary, Housing Listings and the Supabase inventory projection. See `docs/NOTION_PROPERTY_INTAKE.md`.

## Historical checkpoint — 2026-11-13 (superseded by 2026-11-14 verified state)

- Notion Housing Listings is the canonical inventory editor. Supabase `crm_inventory_snapshot` remains the CRM projection; the dashboard reads active `housing_notion` rows only.
- Source-to-projection reconciliation: 104 active Notion pages, 104 active Supabase rows, 0 missing, 0 orphaned, 0 duplicate Listing IDs, and 0 semantic field mismatches after normalizing Notion rich-text formatting.
- Supabase `crm_inventory_intake_events`: 104/104 processed; all 104 now have Listing IDs and match their snapshot Listing IDs; 0 failed, 0 needs-review, 0 stale-processing.
- Reserved Notion fields are clean: `source_group` blank across all 104; 43 nonblank `inventory_locked` values were cleared and it is now blank across all 104.
- `notion-inventory-state` is ACTIVE v9 with JWT verification enabled. AWS stack `efps-notion-property-intake` is `UPDATE_COMPLETE`; Lambda `efps-notion-intake` is Active in account `294417174793`, region `ap-southeast-2`.
- Lambda now emits structured page/event/request correlation logs, retries empty Listing ID allocation up to three times, and sends exhausted async failures to a 14-day SQS failure queue. Async retry policy: 2 retries, 1-hour maximum event age. CloudWatch retention: 30 days.
- A 15-minute scheduled reconciliation scans active Notion pages, enqueues only changed/restored pages, repairs event-to-listing ID mappings, and soft-deletes snapshot rows absent from the complete Notion result. An empty Notion result fails closed rather than mass-deleting inventory.
- Initial mapping repair updated all 104 event Listing IDs. Latest v9 run: 104 checked, 0 queued, 104 unchanged, 0 further mapping updates, 0 missing-page tombstones.
- Restore fallback was exercised on rented listing `EF-2609-09B5`: its Supabase projection was soft-deleted through the worker and then reactivated by scheduled Notion reconciliation. This verifies recovery when a restore webhook is missed; actual Notion `page.undeleted` delivery itself was not independently observed. All eight Page event selections remain user-confirmed and unchanged.
- Production inventory remains 104 rows: 87 Available and 17 Rented Out. `/health` returned HTTP 200. No lead UI, classification, qualification, or WhatsApp behavior was changed.
- Source media gap (not a sync failure): 99/104 listings have Cloudinary image URLs. Five Rented Out pages have no image URL in Notion: `EF-2609-608J`, `EF-2609-22H0`, `EF-2609-VDWH`, `EF-2609-7JGF`, `EF-2609-MECJ`. The CRM mirrors the blank source values; no substitute images were invented.
- Google Sheets reconciliation remains disabled. Legacy Sheet writes and the old WhAPI `NEW` inventory listener remain compatibility/legacy paths by prior direction.
- Separate scope: raw Property Intake with photos still depends on the existing Sheets, Cloudinary, and Maps runtime credentials; those credentials were not changed or revalidated in this inventory-mirror repair.

## CRM production metrics snapshot — 2026-10-05 (historical; not reverified in this task)

- Production branch: `crm-ui-dashboard`
- Verified release candidate: `dd7ba3e94293181c620825433e5f2be8a71e91ff`
- Verified tree: `verified after the documentation release is reconciled into main`
- GitHub Actions: CRM Synthetic CI PASS; CRM UI Verification PASS on the same commit.
- Local MacBook checkout `/Users/zeidzakir/Projects/efps-internal-automatios-local/efps-internal-automatios` was reset to the verified `crm-ui-dashboard` remote branch for release verification.
- Production Render deployment: dep-db1b2svf3r2c73brd6m0 is LIVE from 1982c7ea0a158ee0edcb00fad43e021876c13b9d; /health returns HTTP 200.
- Historical production verification: 253 leads, 9,224 messages, 3,025 persisted webhook events, 277 AI runs, 214 drafts, 88 inventory rows (71 Available / 17 Rented Out).
- Scheduler state at that historical checkpoint: webhook reconciliation is active every minute; inventory reconciliation is active every 5 minutes; deterministic classification is active hourly; the AI scheduler is intentionally paused and has no active cron trigger.
- OOC hardening is implemented but not yet a production-live claim: only controlled out-of-coverage locations can auto-apply OOC; selective, mixed and unknown locations remain review-required.
- Independent encrypted backup/isolated restore and AWS least-privilege IAM rotation remain external infrastructure prerequisites; neither is marked complete without independent evidence.

Historical documents retain dated evidence. Current-state claims in CRM documentation must point to the latest verified release candidate or a later production audit; older counts must not be copied into current-status sections.
## AI scheduler — intentionally paused

- `crm_ai_scheduler_6h` is **paused** as of 2026-10-04.
- Its implementation and `crm_invoke_ai_scheduler()` function remain in the repository and database.
- The pg_cron trigger has been removed, so no recurring AI scheduler execution is currently scheduled.
- The deterministic classification scheduler remains active independently at `0 * * * *`.
- Reactivation requires an explicit operational decision and a new scheduler activation.


## Latest verified Notion inventory checkpoint — 2026-11-14

The CRM inventory projection currently contains 107 active Notion-owned rows and 1 soft-deleted tombstone. Review status is represented separately from intake processing and listing availability. Raw Property Intake is live: three real submissions have canonical pages and matching active snapshots; YA84 remains Needs Review for Maps/photo-limit reasons. No database tables were deleted.
