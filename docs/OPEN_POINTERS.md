# EFPS CRM — Open Pointers

> Verified 2026-10-04 00:49 IST. Only active items are listed here; historical release pointers are superseded.

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

Current live population verified 2026-10-05: **253 promoted qualified leads**, **253 normalized requirement profiles**, **0 missing profiles**, and **71 active canonical inventory listings**. Requirement evidence remains a separate provenance layer and is not fabricated by this audit.
