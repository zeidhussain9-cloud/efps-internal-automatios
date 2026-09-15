# EFPS Internal Automations — Current Handoff

## Current state

The canonical Inventory implementation remains authoritative and is not being migrated from legacy. The approved live-system migration is in progress on the dedicated branch `migration/live-system-20260916`, created from the verified remote tip `4a83a395c097d66447d52b312f05d155a9afe284` because the previously reported local `a3139bf` state differed from the current remote branch state.

## Migration boundary

- Legacy Inventory processing, extraction, normalization, field resolution, business rules, pipeline behavior, and historical hacks are **out of scope**.
- Inventory migration work is limited to the live intake/connection boundary feeding the canonical new Inventory implementation.
- Lead Management is an approved migration and lives under `modules/efpd-lead-mgmnt/`.
- Shared technical capabilities are reused under `shared/`; no duplicate legacy transport is introduced.
- Slack operational behavior is migrated into the root Slack endpoints, `shared/slack/`, the Lead module, and the Inventory operator workflow where each capability belongs.
- Meta Catalogue, Housing.com, website/downstream publishing, other Stage-3 operations, and Society Approvals are outside the current migration.

## Current implementation additions

- `webhook_handler.py` — canonical WhAPI webhook entry point and routing boundary.
- `commands_handler.py` / `commands.py` — Slack slash-command adapter and approved command surface.
- `events_handler.py` — Slack Events API adapter for photo, verification, and bug-report thread workflows.
- `interactive_handler.py` — Lead card button/modal adapter.
- `leads_worker.py` — Lead DynamoDB stream + dashboard worker entry point.
- `handler.py` — canonical new Inventory batch entry point.
- `modules/efpd-lead-mgmnt/src/` — migrated Lead business/state/card/audit/media/dashboard implementation.
- `modules/efps-inventory-mgmnt/src/inventory_runtime.py` — new Stage-1 live intake adapter; it delegates processing to the existing Inventory package.
- `modules/efps-inventory-mgmnt/src/slack_ops.py` — Inventory-owned Slack verification/photo workflow.
- `shared/webhook/` — generic request/response primitives.
- `shared/slack/bugs.py` and `shared/slack/crash_report.py` — shared Slack operational failure surface.
- `template.yaml` — destination deployment contract for the migrated runtime resources.

## Canonical Inventory implementation

The existing Inventory package remains untouched as the business-rule authority. `pipeline.py`, `field_resolution.py`, extraction, normalization, validation, Maps resolution, AI review/beautification, and the 48-column Sheet contract remain new-repository implementation.

## Verification state

Repository-side code review is in progress. Live external acceptance remains **NOT VERIFIED** in this execution environment because the requested Mac checkout path and local Keychain runtime are not available here. No real customer-facing WhatsApp message or production Sheet write is being used for migration validation.

Required remaining acceptance evidence includes target AWS deployment, Slack live registration/permissions, WhAPI live endpoint/token compatibility, safe synthetic webhook delivery through the deployed target, Lead end-to-end behavior, and old-runtime zero-traffic confirmation before retirement.

## Migration documentation

`docs/MIGRATION_LIVE_SYSTEM_MAP_20260916.md` is the canonical migration map for this changeset. It distinguishes MIGRATE, ALREADY PRESENT, NEW-REPOSITORY AUTHORITATIVE, OUT OF SCOPE, and NEEDS LIVE VERIFICATION.
