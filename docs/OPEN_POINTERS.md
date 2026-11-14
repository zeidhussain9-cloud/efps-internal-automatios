## Historical Task 3 deployment checkpoint — 2026-11-14 08:14 UTC (superseded by v12)

## Current verified open pointers — 2026-11-14 (live check)

- Google Sheets status editing: the connected Housing_Listings column E currently offers only Available and Rented Out and has no conditional-format rules. The Sheet11 reference row lists no allowed values. The requested separate Sheet 2 source has not been identified. There is currently no Google Sheets edit → Supabase sync path; existing property updates sync from Notion Housing Listings page events. Obtain the exact Sheet 2 link, then implement the intended sheet-owned status update path before asking the operator to test it.
- Notion webhook coverage: 26 event rows are observed (5 processed, 18 ignored, 2 needs review, 1 rejected); complete delivery capture is not certified.
- Raw-intake Sheets compatibility: the two current submissions have Photos, Raw Property Data, Housing Listings relations and matching Supabase snapshots; the corresponding compatibility Sheet writes were not independently verified in this check.
- Restore event: actual Notion page.undeleted webhook delivery remains unobserved; the scheduled 15-minute reconciliation fallback remains the recovery path.
- No database tables deleted. Workspace cleanup and CRM review-status visibility are out of scope for this pass.

# EFPS CRM — Open Pointers

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

- Processing-note durability: the current note field is overwritten during reprocessing. Implement append-only narrative history before promising every attempt is preserved.
- Notion webhook delivery completeness is not certified from the 26 observed event rows (5 processed, 18 ignored, 2 needs review, 1 rejected).
- Compatibility Sheet row writes for the two latest raw property submissions were not independently checked.
- Actual Notion page.undeleted webhook delivery remains unobserved; the scheduled 15-minute reconciliation fallback remains the recovery path.
- No database tables deleted. Workspace cleanup and CRM review-status visibility remain out of scope for this pass.
