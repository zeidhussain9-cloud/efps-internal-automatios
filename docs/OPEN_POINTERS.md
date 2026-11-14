# EFPS CRM — Open Pointers

> CRM operational pointers last verified 2026-10-05; Notion inventory recovery hardening verified 2026-11-13. Historical release pointers are superseded.

## Task 3 — Notion webhook event history (local implementation, not deployed)

- Local `crm_inventory_intake_events` migration and Notion Lambda/Edge Function lifecycle integration are implemented on `crm-ui-dashboard`; no production migration or code deployment has occurred.
- Production Supabase confirms the existing page-level table is present; the Task 3 event-history extension is not applied. `notion-inventory-state` remains ACTIVE v9; `whapi-crm-webhook` remains ACTIVE v10. Existing `crm_webhook_events` and WhatsApp processing are unchanged.
- Mac tooling installed: Supabase CLI 3.1.0, Deno 2.9.8 and PostgreSQL 17.12. Docker was deliberately not installed or used.
- The migration executed successfully against an isolated local PostgreSQL database. SQL lifecycle checks passed for receipt, queue/worker/terminal transitions, duplicate suppression, retry after failure, history retention, and Listing ID correlation. RLS/privilege assertions passed.
- Deno type-check passed for `notion-inventory-state/index.ts`. Full local checks: Python 106/106, repository Node 145/145, Edge Function contract 6/6, browser 1/1, Python compilation and `git diff --check` pass.
- Production remains unchanged: no Task 3 migration applied, `notion-inventory-state` ACTIVE v9 and `whapi-crm-webhook` ACTIVE v10. No production end-to-end webhook test has been run.
- Remaining before production: review final diff and run Supabase production advisors/read-only checks. With separate authorization, deploy in order: migration → `notion-inventory-state` Edge Function → AWS `efps-notion-intake` Lambda.

## Current Notion inventory — recovery hardening verified 2026-11-13

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
