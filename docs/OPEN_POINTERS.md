# EFPS CRM — Open Pointers

> CRM operational pointers last verified 2026-10-05; Notion inventory deployment and backfill verified 2026-11-13. Historical release pointers are superseded.

## Current Notion inventory rollout — live verification 2026-11-13

- AWS account `294417174793` in `ap-southeast-2` has the active Notion intake Lambda. Supabase `notion-inventory-state` is ACTIVE v6 with JWT verification enabled.
- The user confirms the existing `EFPS CRM Property Intake` webhook is verified with all eight Page events selected. No event settings were changed.
- The signed-in production dashboard showed 104 Notion-owned properties (87 Available, 17 Rented Out). A live Notion edit propagated through Supabase and appeared in the dashboard. A real Notion delete soft-deleted its Supabase row after about one minute. Earlier duplicate handler verification returned `already_processed`.
- **Open blocker:** restoring the test page in Notion did not trigger a new Lambda invocation or Supabase Edge Function request; the Supabase row remained soft-deleted. The direct restore worker check passed, but live webhook delivery did not. Keep all Page events as selected; diagnose event delivery without toggling webhook settings.
- Cleanup is verified: the exact test snapshot and intake rows were removed from Supabase, and the test page was permanently deleted from Notion Trash after user approval. Supabase and the dashboard returned to 104 rows (87 Available, 17 Rented Out).
- GitHub `crm-ui-dashboard` is `61688164b25f7a7a8e6df8248f91987a9c471ef6`; GitHub `main` is `3c66a89e734d02ade5b4865f05c2dcbc99ec655b`. Both have tree `14717bf1d37afa8d678fc0526026dae357755fdf`. Render was observed live on `61688164`; `/health` and `/` returned HTTP 200 in the release check.
- Existing AWS secrets remain reused without revealing or changing values. The Sheet reconciliation cron is removed, but legacy Sheet writes remain; WhAPI remains until final cleanup. Raw photo intake credential validity is still unverified.

## Remaining user actions

- No immediate operator action is needed. The engineering follow-up is to diagnose why Notion's restore action did not deliver the selected `page.undeleted` event, then repeat a safe live restore test and confirm Supabase and the dashboard recover the listing. Do not alter webhook configuration without separate direction.

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
