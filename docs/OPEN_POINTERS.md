# EFPS CRM — Open Pointers

> CRM operational pointers last verified 2026-10-05; Notion inventory deployment and backfill verified 2026-11-13. Historical release pointers are superseded.

## Current Notion inventory rollout — 2026-11-13

- AWS identity is account `294417174793` in `ap-southeast-2`. SAM updated `efps-notion-property-intake` to `UPDATE_COMPLETE`; Lambda `efps-notion-intake` is Active with a successful update and CodeSha256 `+b4hBplC+2CGZag7HnpSDdmfwDqwuvHqtuSSLoGd/6c=`. Supabase `notion-inventory-state` is ACTIVE v6, JWT verification enabled.
- The user confirms the existing `EFPS CRM Property Intake` Connection webhook remains verified with all eight Page events selected. No Notion settings were changed.
- Live testing confirmed create, edit, Listing ID write-back, duplicate suppression, soft-delete, and restore clearing the tombstone. Delete/restore used direct Lambda worker invocations; webhook delivery for those events was not independently observed. The test snapshot and intake event were removed. Supabase has 104 active Notion rows (87 Available, 17 Rented), no `housing_sheet` rows, and no test record. The test page remains in Notion Trash; permanent deletion from Trash requires a signed-in Notion UI.
- GitHub commit `ddb0f6391f99ba9a848fd30c8b03bd5db9c1b53c` passed Inventory Contract (130/130), SAM build/validation, CRM checks, and production health smoke. Render deployment `dep-dbrei8avcj2c73erda3g` is LIVE on that commit; `/health` and `/` returned HTTP 200. Signed-in dashboard inventory rendering remains unchecked because the browser is at the operator sign-in gate.
- Existing AWS secret ARNs were reused; values were not printed, copied, created, rotated, or overwritten. The Sheet reconciliation cron is removed, but legacy Slack/raw-intake Sheet writes remain. The old WhAPI `NEW`-delimited listener remains until final cleanup. Raw photo intake credential validity remains unverified.

## Remaining user actions

- Sign in to the production CRM in the browser so the authenticated inventory page can be visually checked.
- Sign in to Notion and permanently delete test page `417fedf9-b4e8-81ed-b882-df6cf2abd723` from Trash if zero residual test content is required. The connected API can only move it to Trash; it cannot permanently empty Trash.

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
