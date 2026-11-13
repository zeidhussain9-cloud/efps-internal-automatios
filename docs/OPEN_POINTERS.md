# EFPS CRM — Open Pointers

> CRM operational pointers last verified 2026-10-05; Notion inventory deployment blockers verified 2026-11-13. Historical release pointers are superseded.

## Current inventory intake acceptance gates — 2026-11-13

- Update AWS Secrets Manager `efps-whapi-panel-sheet` with the complete service-account JSON currently held in macOS Keychain service `efps-whapi-panel-sheet` (account `efps`). The current AWS value is `{}`. The local Keychain credential successfully read the canonical `Housing_Listings` sheet and its 46-column A:AT header matched the repository contract.
- Update AWS Secrets Manager `efps-whapi-panel-cloudinary` with the verified Keychain JSON fields `cloud_name`, `api_key`, and `api_secret`. The current AWS values are placeholders; the local credential's authenticated Cloudinary ping returned HTTP 200.
- Update AWS Secrets Manager `efps-whapi-panel-maps` with the verified Google Maps API key from local Keychain service `efps-whapi-panel-maps`. The current AWS value is `MIGRATION_PLACEHOLDER`; the local credential returned a VERIFIED Bengaluru geocode.
- Configure the Notion Developer Connection webhook subscription to `https://ko3771nvei.execute-api.ap-southeast-2.amazonaws.com/Prod/notion/intake` for `page.created` and `page.properties_updated`. The handshake will populate `webhook_secret` automatically.
- After those actions, run the controlled end-to-end Notion intake with photos, same-event replay, Notion relation/status, and the existing Sheet-to-Supabase sync. No production inventory row has been created by the permission/idempotency probes.
- The Notion path now uses Supabase `crm_inventory_intake_events` and the `notion-inventory-state` Edge Function. No DynamoDB table is used by Notion. The old WhAPI `NEW`-delimited inventory listener is retained only until the final cleanup phase, per user instruction.

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
