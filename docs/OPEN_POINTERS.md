## Historical Task 3 deployment checkpoint — 2026-11-14 08:14 UTC (superseded by v12)

## Current verified open pointers — 2026-11-14

- Full Raw Property Intake acceptance remains pending: two existing submissions have photos but blank Raw Property Data and remain Needs Review.
- Complete Notion webhook delivery coverage is not certified from the 18 observed event records.
- Four ignored event outcomes are non-intake changes; one rejected event is the unauthenticated endpoint probe used during smoke testing. Both are retained in the event ledger.
- Notion workspace cleanup was limited to clarifying the home and reference pages; no page or database was deleted.
- No tables deleted. WhatsApp and Notion event histories remain separate in their existing tables.

# EFPS CRM — Open Pointers

> Operational pointers updated 2026-11-14. Historical snapshots below remain dated evidence, not current state.

## Historical Task 3 initial deployment checkpoint — 2026-11-14 08:14 UTC (superseded by v12)

- Commit `ca05141bec073b87c8617c59bf79a40cd16534f9` is pushed to `crm-ui-dashboard`; Render deployment `dep-dbs1f0m417fc73f0cmig` is LIVE.
- Supabase migration `crm_notion_webhook_event_history` is applied. It extends existing `crm_inventory_intake_events`; no new table was created and `crm_webhook_events` / WhatsApp processing were not changed.
- Supabase `notion-inventory-state` ACTIVE v10 (JWT verification on). AWS stack `efps-notion-property-intake` UPDATE_COMPLETE; Lambda `efps-notion-intake` Active and update successful.
- SAM validate/build, Deno type-check, local SQL lifecycle/security checks, Python 106/106, Node 145/145, Edge contract 6/6 and browser 1/1 passed. Docker was not used.
- Live Notion form view `Submit New Property` has both `Raw Property Data` and `Photos` questions. Its data-source description was updated to reflect the deployed workflow.
- **Pending:** operator's first real property submission and evidence-backed end-to-end reconciliation across webhook ledger, Lambda, Sheets, Cloudinary, Housing Listings, and Supabase snapshot. No synthetic production property has been inserted.

## Remaining inventory intake follow-ups

- Verify one real raw-details-and-photos intake end to end after the operator submission. Confirm all source/derived records and terminal processing status.
- Verify raw Property Intake Sheets, Cloudinary and Maps credentials through the real worker execution; do not expose or rotate secrets.
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


## Latest verified open pointers — 2026-11-14

- Raw Property Intake full-chain acceptance remains unverified until a real operator submission is processed across Notion webhook, Lambda, Sheets, Cloudinary, Maps, Housing Listings and Supabase.
- Complete Notion webhook capture coverage is not certified from the 18 observed event rows; audit configured delivery types and retry outcomes before claiming completeness.
- Maps fallback and business-status UI changes are deployed.
- Notion workspace navigation and current-state references were consolidated; no page or database was deleted.
- Eleven event rows have failed status (ten ignored non-intake changes and one rejected unauthenticated probe); two remain Needs Review due to missing Raw Property Data. All records are retained for audit.
