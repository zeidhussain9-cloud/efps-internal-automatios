## Legacy cleanup checklist (parked, NOT approved to execute) - 2026-11-25

- Collection assignment was removed from the current repo, the efps-notion-intake Lambda, Notion and Supabase on 2026-11-25 (user decision: collection assignment is never automated).
- Remaining by design: the Nov 15 deployed packages of the older Lambdas EFPSInteractive and EFPSLeadWorker still contain old copies of `modules/efps_meta_catalogue_mgmnt/src/generator.py` (assign_to_collection, publish_and_assign), its `__init__` export and an older Whapi client with edit_collection. Their handlers do not import them (static check, 2026-11-25).
- Cleanup, only when the user approves and when those Lambdas are next redeployed for another reason: redeploy them from the current repo so the dormant copies disappear, then verify.
- The live Slack app configuration (usage hint for `assign`) was not inspected; the repo manifest and docs no longer list it. Check the live Slack app settings separately.

## Current Maps fallback correction

Maps API verification is optional for raw property intake. Missing/unreadable credentials, billing/quota/authorization denials, and request/transport failures preserve the submitted supported short Maps URL as not verified and do not independently create a `Needs Review` state. Source-derived locality remains authoritative; unverified Maps results never enrich location fields. Partial/mismatched results, unsupported links, and genuine property validation issues remain review conditions. See `docs/DEPLOYMENT.md` and `docs/NOTION_PROPERTY_INTAKE.md` for the deployed release evidence.

## Historical Task 3 deployment checkpoint — 2026-11-14 08:14 UTC (superseded by v12)

## Historical open pointers — 2026-11-14 (superseded by 2026-11-15 release)

- Raw-intake locality schema compatibility is corrected and deployed in Lambda CodeSha256 `oyn+czp4YEH/um4aBdIagC4S+U4RunBq/VHH6IzVnwU=`. Inventory tests 126/126 and SAM validation/build passed. A fresh operator-submitted raw-intake record remains the final end-to-end acceptance; no synthetic production record was created. `EF-2611-YA84` remains Needs Review because 18 photos exceed the 10-image catalogue limit; Maps API unavailability alone is not a review reason.

- Notion Housing Listings listing_state dropdown is complete: exactly Available (green), Rented Out (red), and On Hold (yellow). Schema verified after update. Existing page-event synchronization remains the only property update path; no Google Sheets synchronization was added.
- Notion webhook coverage: 26 event rows are observed (5 processed, 18 ignored, 2 needs review, 1 rejected); complete delivery capture is not certified.
- Raw-intake Sheets compatibility: all three current submissions have Raw Property Data, Housing Listings relations and matching Supabase snapshots. The two earlier records have Photos; YA84 has 18 source photos but no Cloudinary URLs because it exceeds the 10-image limit. Compatibility Sheet writes were not independently verified.
- Restore event: actual Notion page.undeleted webhook delivery remains unobserved; the scheduled 15-minute reconciliation fallback remains the recovery path.
- No database tables deleted. Workspace cleanup and CRM review-status visibility are out of scope for this pass.

# EFPS CRM — Open Pointers

## Current verified release — 2026-11-15 (Maps fallback correction)

- Repository: zeidhussain9-cloud/efps-internal-automatios; main and crm-ui-dashboard are fast-forward synchronized, with identical GitHub branch heads and clean local worktrees. The deployed Lambda code is from source commit bb52959; later commits in this release only reconcile documentation.
- AWS: isolated stack `efps-notion-property-intake` is `UPDATE_COMPLETE`; Lambda `efps-notion-intake` Active / LastUpdateStatus Successful, Python 3.12, last modified `2026-11-14T19:48:46Z`, CodeSha256 `oyn+czp4YEH/um4aBdIagC4S+U4RunBq/VHH6IzVnwU=`. The downloaded live Lambda archive hash matches the Lambda CodeSha256. The 15-minute EventBridge reconciliation rule remains ENABLED.
- Maps behavior: absent/unreadable/placeholder credentials, billing/quota/authorization denials, and request/transport exceptions preserve the supported original short Maps URL as not verified and do not independently create `Needs Review`. Unverified Maps results never supply locality, pincode, coordinates or place name. Partial/mismatched verification, unsupported links, missing required fields/locality, AI conflicts and photo-limit violations remain review conditions.
- Supabase `notion-inventory-state` remains ACTIVE v12 with JWT verification enabled; no database schema, rows, secrets, or Edge Function were changed by this release. Render CRM UI was not changed or redeployed.
- Verification: Inventory + shared Maps pytest 174/174; Node 146/146; browser 1/1; production build; Python compileall; SAM lint/validate/build; generated SAM template validation; `git diff --check` all passed.
- No new production intake row was created. The existing synthetic test listing `EF-2611-SF6F` remains excluded from operational inventory reporting.


> Operational pointers updated 2026-11-14. Historical snapshots below remain dated evidence, not current state.

## Historical Task 3 initial deployment checkpoint — 2026-11-14 08:14 UTC (superseded by v12)

- Commit `ca05141bec073b87c8617c59bf79a40cd16534f9` is pushed to `crm-ui-dashboard`; Render deployment `dep-dbs1f0m417fc73f0cmig` is LIVE.
- Supabase migration `crm_notion_webhook_event_history` is applied. It extends existing `crm_inventory_intake_events`; no new table was created and `crm_webhook_events` / WhatsApp processing were not changed.
- Supabase `notion-inventory-state` ACTIVE v10 (JWT verification on). AWS stack `efps-notion-property-intake` UPDATE_COMPLETE; Lambda `efps-notion-intake` Active and update successful.
- SAM validate/build, Deno type-check, local SQL lifecycle/security checks, Python 106/106, Node 145/145, Edge contract 6/6 and browser 1/1 passed. Docker was not used.
- Live Notion form view `Submit New Property` has both `Raw Property Data` and `Photos` questions. Its data-source description was updated to reflect the deployed workflow.
- **Pending:** operator's first real property submission and evidence-backed end-to-end reconciliation across webhook ledger, Lambda, Sheets, Cloudinary, Housing Listings, and Supabase snapshot. No synthetic production property has been inserted.

## Historical remaining inventory intake follow-ups — reassess against the current live check

- The first real raw-details-and-photos submissions have now been processed and reconciled to Housing Listings and Supabase. Exact compatibility Sheet row writes remain unverified.
- Do not expose or rotate credentials. Cloudinary image URLs and Maps fallback are observed in the current records; the compatibility Sheet write remains the unverified sub-step.
- Reconcile the 44 historical long Google Maps URLs across Sheets, Notion and Supabase together; do not update only one platform.
- Independently observe a real `page.undeleted` webhook delivery; scheduled 15-minute reconciliation already provides the tested recovery fallback.
- Resolve the five existing listings with missing Cloudinary image URLs only from source media, not substitute imagery.

## Historical Notion inventory recovery checkpoint — 2026-11-13

## Historical Notion inventory recovery checkpoint — 2026-11-13

- AWS `efps-notion-intake` is Active in account `294417174793`, region `ap-southeast-2`; stack `efps-notion-property-intake` is `UPDATE_COMPLETE`. Supabase `notion-inventory-state` is ACTIVE v9 with JWT verification enabled.
- Notion Housing Listings remains canonical. The CRM projection has 104 active rows (87 Available / 17 Rented Out), matching all 104 active Notion pages. There are 0 missing, orphaned, duplicate or semantically mismatched records.
- All 104 intake events are processed and have Listing IDs matching their snapshot rows. `source_group` and `inventory_locked` are blank across all 104 Notion pages; 43 prior `inventory_locked` values were cleared.
- EventBridge reconciliation runs every 15 minutes, queues only changed/restored pages, reconciles event Listing IDs, and soft-deletes rows absent from the full Notion result. Empty Notion results fail closed. A soft-deleted active rented listing was reactivated by this fallback.
- Actual Notion `page.undeleted` webhook delivery remains unobserved, but missed restores are now recovered automatically within the 15-minute reconciliation interval. The eight Page event selections remain user-confirmed and unchanged.
- Source media gap (not a sync failure): five Rented Out listings have no Cloudinary image URL in Notion (`EF-2609-608J`, `EF-2609-22H0`, `EF-2609-VDWH`, `EF-2609-7JGF`, `EF-2609-MECJ`). The CRM correctly shows 99/104 listings with photos; source media is required to close this gap.
- Lambda async failures retry twice and then enter the 14-day SQS failure queue; structured logs include page/event/request correlation and retain 30 days.
- Sheet reconciliation cron is removed. Legacy Sheet writes and the old WhAPI `NEW` listener remain untouched pending separately agreed cleanup.

## Remaining scoped follow-up

- Raw Property Intake with photos is a separate compatibility pipeline that still depends on the existing Sheets, Cloudinary and Maps runtime credentials. Those credential values were not changed or revalidated during the Housing Listings mirror repair. Do not rotate or overwrite them without a separately approved credential operation.

## External infrastructure prerequisites

- Independent encrypted backup artifact and isolated restore proof: repository backup/restore tooling and tests exist, but a separate durable backup destination and isolated restore target still require authorized infrastructure.
- AWS least-privilege IAM rotation: requires authorized AWS IAM administration and production secret rotation; no IAM-management connection is available through the current project tools.

## Closed in repository and production

- Deterministic OOC policy with controlled vocabulary and review gates.
- Group Message classification for WhatsApp @g.us chats, including schema constraint, webhook rules, UI option, audit trail and production backfill.
- D08 visual/operational handoff documentation.
- Current CRM documentation normalization for the verified audit snapshot.
- Deterministic CRM classification engine, hourly scheduler, evidence audit trail, and AUTO QUALIFIED provenance.

## Deferred product work

- Incremental/delta AI analysis.
- Field-level AI proposal editing.

Do not reopen historical pre-production/import gates without new regression evidence.

## Scheduler Reconcile Audit — current contract

Points **40 Requirement field correctness**, **41 Property-matching inputs**, and **42 Property-matching results** are governed by the single canonical contract in `crm-source-audit-scheduler/AUDIT_CONTRACT.md` and the shared implementation in `src/crm-requirement-match-audit.mjs`. The scheduled runner fails closed unless the combined requirement/matching audit is complete. Do not duplicate or redefine these rules in this document.

Historical live population snapshot verified 2026-10-05: **253 promoted qualified leads**, **253 normalized requirement profiles**, **0 missing profiles**, and **71 active canonical inventory listings**. Requirement evidence remains a separate provenance layer and is not fabricated by this audit.


## Latest verified open pointers — 2026-11-14 (live check)

- Raw-intake schema compatibility is corrected and deployed in Lambda CodeSha256 `oyn+czp4YEH/um4aBdIagC4S+U4RunBq/VHH6IzVnwU=`. Inventory tests 126/126 and SAM validation/build passed. A fresh operator-submitted raw-intake record remains the final end-to-end acceptance; no synthetic production record was created.
- Supabase inventory projection has 107 active Notion-owned rows with 107 populated locality values; the earlier 104/107 blank alert recovered through the 15-minute reconciliation without manual repair.
- Notion webhook ledger currently contains 96 observed rows: 64 synced, 2 already processed, 26 ignored outcomes, 3 Needs Review, and 1 with no outcome. The 26 ignored outcomes are still stored with processing_status=failed; this status/outcome mismatch is an open ledger issue. Complete webhook delivery capture is not certified.
- Compatibility Sheet row writes for the three latest raw property submissions were not independently checked.
- Actual Notion page.undeleted webhook delivery remains unobserved; the scheduled 15-minute reconciliation fallback remains the recovery path.
- No database tables deleted. Workspace cleanup and CRM review-status visibility remain out of scope for this pass.
