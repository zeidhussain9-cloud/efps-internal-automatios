# EFPS Internal Automations — Current Handoff

## Current state

The canonical Inventory implementation remains authoritative. The original migration commit `a2f63b508e5205c4cf3b79d32d4968ee36955b30` remains preserved, and this remediation is a separate follow-on commit on `migration/live-system-20260916`.

## Migration boundary

- Legacy Inventory processing, extraction, normalization, field resolution, business rules, pipeline behavior, and historical hacks are **out of scope**.
- Inventory migration work is limited to the live intake/connection boundary feeding the canonical new Inventory implementation.
- Lead Management is an approved migration and lives under `modules/efpd-lead-mgmnt/`.
- Shared technical capabilities remain under `shared/`; no duplicate legacy transport is introduced.
- Meta Catalogue, Housing.com, website/downstream publishing, other Stage-3 operations, and Society Approvals remain outside the current migration.

## Remediation state

Repository-side defects identified by the post-migration audit were remediated without changing Inventory Stage-2 business logic. The remediation covers Stage-1 import wiring, Lead worker packaging, AWS Slack signing-secret resolution, Slack Events idempotency and error handling, Lead media-reference persistence, Lead card recovery, the Slack Events authentication bypass, canonical WhAPI user-agent handling, root dependency packaging, and documentation alignment.

## Verification state

**REPOSITORY REMEDIATION COMPLETE** means the destination source tree contains the reviewed fixes and the original migration commit remains intact. It does **not** mean the destination is live-accepted.

**LIVE SYSTEM MIGRATION VERIFIED: NOT VERIFIED** in this execution environment. The canonical Mac checkout is unavailable here, and no AWS deployment/CloudFormation stack inspection, Slack live registration check, WhAPI destination cutover check, destination Google Sheets credential probe, or old-runtime zero-traffic confirmation has been performed from this session.

No customer-facing WhatsApp message was sent and no unnecessary production Sheet write was performed.

## Required live acceptance before retirement

1. Deploy the remediation commit to the intended AWS environment and validate Lambda package contents/imports.
2. Validate Slack app registration, endpoint URLs, signing secret, bot membership/permissions, and controlled error behavior.
3. Validate the destination WhAPI webhook URL/token relationship and a safe synthetic non-inventory webhook probe.
4. Validate destination Google Sheets read/write boundary without unnecessary production mutation.
5. Validate Lead and Inventory routing end to end using safe synthetic traffic.
6. Confirm the old runtime has zero required traffic before retirement.

Until those checks are evidenced, the old live system must remain in place.

## Canonical documents

`docs/MIGRATION_LIVE_SYSTEM_MAP_20260916.md` is the canonical migration scope/source-authority map. `docs/OPEN_POINTERS.md` contains the remaining runtime verification items.
