# EFPS CRM — Open Pointers

> Verified 2026-10-03 18:35 IST. Only active items are listed here.

## Release / runtime

- Deploy and runtime-verify the `dd7ba3e` CRM hardening candidate on Render. Do not call OOC automation production-live until the deployed commit is independently verified.

## External infrastructure prerequisites

- Independent encrypted backup artifact and isolated restore proof: repository backup/restore tooling and tests exist, but a separate durable backup destination and isolated restore target still require authorized infrastructure.
- AWS least-privilege IAM rotation: requires authorized AWS IAM administration and production secret rotation; no IAM-management connection is available through the current project tools.

## Closed in repository

- Deterministic OOC policy with controlled vocabulary and review gates.
- D08 visual/operational handoff documentation.
- Current CRM documentation normalization for the verified audit snapshot.

## Deferred product work

- Incremental/delta AI analysis.
- Field-level AI proposal editing.

Do not reopen historical pre-production/import gates without new regression evidence.