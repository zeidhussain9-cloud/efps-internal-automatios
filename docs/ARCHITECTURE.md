# EFPS Internal Automations — Architecture

This is the canonical cross-repository architecture reference.

## Core model
- `shared/` — reusable technical capabilities and integrations.
- `modules/` — EFPS business capabilities and business decisions.

> Shared services provide capabilities; modules decide when and why they are used.

## Shared capabilities
- `shared/cloudinary/` — reusable media storage/upload capability.
- `shared/google_sheets/` — Sheets transport and the canonical 48-column `Housing_Listings` contract.
- `shared/google_maps/` — reusable Maps URL extraction and Google Geocoding resolution capability; inventory decides when it is required.
- `shared/whatsapp_whapi/` — WhAPI transport, webhook normalization/verification, and the two-listener source boundary.
- `shared/slack/` — reusable Slack transport, runtime signature security, routing, and operational capability.
- `shared/webhook/` — generic HTTP request/response primitives used by entry boundaries.
- `shared/credentials/` — local macOS Keychain credential provider used as the local fallback by shared adapters.

## Business modules
- `modules/efpd-lead-mgmnt/` owns Lead state, persistence access, cards, audit, media handling, and dashboard behavior.
- `modules/efps-inventory-mgmnt/` owns Inventory Stage-1 intake and the canonical Stage-2 implementation.

## Inventory top-level stages

### Stage 1 — Initial / Webhook
Dedicated inventory-listener traffic enters the inventory module. `NEW` opens a property session; subsequent messages are collected until the next `NEW`, which closes the property. A listing identity is created and the raw record is persisted.

### Stage 2 — Deterministic Extraction / Property Processing
The completed raw property is processed as one business stage with the following deterministic boundary:

```text
raw_message_text
  -> canonical source segmentation
  -> candidate extraction
  -> canonical field resolution
  -> deterministic normalization/business rules
  -> deterministic validation
  -> Maps enrichment/verification
  -> optional AI verification/wording-only beautification
```

The authoritative deterministic entry point is `modules/efps-inventory-mgmnt/src/pipeline.py:deterministic()`. The authoritative full Stage-2 entry point is `process_closed_session()`.

Existing persisted Sheet Stage-2 values are never extraction input. The raw source remains authoritative for deterministic facts.

The live-system migration does not import legacy Inventory extraction, normalization, resolution, validation, or pipeline behavior. Only the Stage-1 live intake boundary is integrated with the migration.

## Stage 3 — Downstream Operations
Stage 3 is the downstream boundary for later consumers. It is not part of the current Inventory Phase-1 publishing implementation.

## Canonical sheet
The single physical shape is `shared/google_sheets/schema.py`: 48 columns A:AV. The schema records owner, stage, allowed values where verified, and declared dependencies.

## Lead and Slack runtime boundary
WhAPI inbound delivery enters the root webhook routing boundary. Inventory-listener traffic goes to Inventory Stage 1; other direct inbound traffic goes to Lead Management. Slack slash commands, Events API delivery, and interactive actions are public adapters that use the shared Slack signature verifier. AWS resolves the signing secret from `SLACK_SIGNING_SECRET`; local development may fall back to the canonical Keychain credential.

Slack Events are idempotent by `event_id` using an atomic claim in the existing `efps-sessions` table. Lead inbound media references are retained in the existing interaction media fields. Lead card delivery edits the existing card where possible and recreates a deleted card when an update fails.

## Stage-1/2 write boundary
Inventory Stage 1/2 may write A:D, F:AO, and AU. It must not write E (`listing_state`), AP:AT (Housing/Meta downstream fields), or AV (`inventory_locked`). Stage-3 writers are responsible for those protected fields.

## Runtime boundary
Repository-side remediation is distinct from live acceptance. AWS deployment, Slack runtime registration/permissions, WhAPI destination configuration, destination webhook delivery, and target Google Sheets access must be verified against the destination deployment before the old runtime is retired.

## Documentation authority

`docs/DATA_CONTRACTS.md` owns cross-module field semantics and dependencies. `docs/DETERMINISTIC_FIELD_RESOLUTION.md` owns candidate resolution and precedence. `docs/INVENTORY_SOURCE_EXTRACTION.md` owns source segmentation and extraction boundaries. `docs/MIGRATION_LIVE_SYSTEM_MAP_20260916.md` owns the current live-system migration scope and source-authority classification. `docs/DOCUMENT_MAP.md` owns documentation roles.
