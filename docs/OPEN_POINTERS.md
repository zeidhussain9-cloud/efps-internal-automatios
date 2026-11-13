# EFPS CRM — Open Pointers

> CRM operational pointers last verified 2026-10-05; Notion inventory deployment and backfill verified 2026-11-13. Historical release pointers are superseded.

## Current Notion inventory rollout — 2026-11-13

- Confirmed AWS account `294417174793` in `ap-southeast-2`; SAM updated the isolated `efps-notion-property-intake` stack to `UPDATE_COMPLETE`. Lambda reports a successful update. Existing secret ARNs were reused with no secret values printed, copied, created, rotated, or overwritten.
- The existing `EFPS CRM Property Intake` Connection is present in Notion Developer Connections. The user confirms its webhook and all eight Page events remain verified/selected: `page.content_updated`, `page.created`, `page.deleted`, `page.locked`, `page.moved`, `page.properties_updated`, `page.undeleted`, `page.unlocked`.
- The internal `_efps_notion_backfill` replay accepted 104 pages. Supabase confirms 104 processed intake events and 104 active `housing_notion` rows (87 Available, 17 Rented); no `housing_sheet` snapshot rows or test-like listings remain. The old Sheet cron was unscheduled.
- Remaining work: complete the Render deployment and verify the production inventory UI after it becomes live. Raw Property Intake with photos still uses the legacy Sheet/Cloudinary/Maps path; its existing AWS secret values were left untouched and were not validated in this rollout. The old WhAPI `NEW`-delimited listener remains untouched until final cleanup.

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
