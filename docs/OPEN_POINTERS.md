# EFPS CRM — Open Pointers

> **Verified 2026-10-03 18:04 IST (12:34 UTC).** This file contains only active items. Historical audit findings are retained in dated audit documents and are not duplicated here.

## Completed

- Live WhAPI ingestion and automatic webhook reconciliation.
- Lead/classification promotion and event/message/lead reconciliation.
- Housing inventory five-minute reconciliation with hash-based snapshot comparison.
- Six-hour AI scheduler with persistence, checkpointing, idempotency and draft provenance.
- Deterministic `Out of Coverage Area` status assignment using the controlled coverage policy introduced in `e375c1f811e962e140caba2c964fb05cd94ab02a`.
- D08 visual/interaction handoff documentation.
- Current production documentation normalization.

## External infrastructure prerequisites

- Independent encrypted backup artifact and isolated restore proof: repository backup/restore tooling exists, but a separate durable storage target and isolated restore target must be provisioned in authorized infrastructure.
- AWS least-privilege credential rotation: requires authorized AWS IAM provisioning/rotation; no AWS IAM management connection is available through the current project tools.

## Deferred product work

- Incremental/delta AI analysis.
- Field-level editing of AI-proposed requirement updates.

Do not re-open older dated gates as current blockers unless a new verification shows a regression.