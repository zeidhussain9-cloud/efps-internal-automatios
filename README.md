# EFPS Internal Automations

Internal automation repository for EasyFind Property Solutions (EFPS).

The repository follows one simple operating model:

> **Root = how the AI/repository operates.**
>
> **`docs/` = what the business/system is.**
>
> **`modules/` = business capabilities.**
>
> **`shared/` = reusable technical capabilities.**

## Mandatory AI operating protocol

- `CORE_STEERING.md` — mandatory core AI operating protocol applied by every AI agent before every response or action.
- `GEMINI.md` — Gemini-specific operating adapter.
- `AGENTS.md` — general AI-agent operating rules and enforcement of core steering.
- `HANDOFF.md` — current working state between development sessions.

## Repository structure

- `docs/` — single canonical home for EFPS business and system knowledge.
- `modules/` — business capabilities and business decisions.
- `shared/` — reusable technical integrations and capabilities.
- `.gemini/skills/` — repeatable AI session procedures.

## Mandatory documentation rule

For every implementation, the agent must review all maintained root and `docs/` documentation and update every document whose content is affected by the resulting repository reality. Do not create duplicate authoritative documents.

## Current modules

- `modules/efps-inventory-mgmnt/` — property inventory business workflows and rules; current Inventory Phase-1 implementation.
- `modules/efpd-lead-mgmnt/` — lead/enquiry business workflows and rules.
- `modules/efps-meta-catalogue-mgmnt/` — reserved future Meta/WhatsApp catalogue business workflows.
- `modules/efps-housing-portal-mgmnt/` — reserved future Housing.com automation.
- `modules/efps-website-mgmnt/` — EasyFind website management and automation.

## Established shared capabilities

- `shared/cloudinary/` — reusable Cloudinary media storage/upload capability with deterministic property/lead namespaces and secure URL helpers.
- `shared/credentials/` — canonical local macOS Keychain credential provider.
- `shared/google_maps/` — reusable Google Maps URL extraction plus later runtime Geocoding resolution.
- `shared/google_sheets/` — reusable Google Sheets technical access plus the canonical 48-column `Housing_Listings` A:AV contract; live read/write boundary verified for Inventory Phase 1.
- `shared/slack/` — reusable Slack operational capability for the authorized Inventory Phase-1 workflows.
- `shared/whatsapp_whapi/` — reusable WhAPI technical transport, live gate, channel/settings primitives, webhook normalization, and neutral messaging primitives.

## Inventory Phase-1 processing model

Inventory uses three top-level stages:

1. **Stage 1 — Initial / Webhook**: dedicated inventory listener, `NEW` property-session boundary, raw capture, and initial row.
2. **Phase-1 deterministic boundary**: canonical source segmentation, deterministic candidate extraction/resolution, normalization/dependencies, deterministic Google Maps URL extraction, and deterministic validation. This boundary is implemented by `src.phase1.run_phase1()` and is AI-independent and network-free for Maps.
3. **Later property verification / downstream processing**: runtime Google Maps resolution, optional AI verification, wording-only AI beautification, media handling, and downstream publishing. These do not provide source evidence to the deterministic boundary.

The deterministic source contract is: `raw_message_text` is authoritative; persisted Stage-2 Sheet values are never extraction input. Internal property type is restricted to `Gated Community`, `Semi Gated`, or `Standalone`; direct source evidence wins and missing/invalid evidence remains unresolved. Society/community names are not used as property-type evidence.

Property type drives the coupled parking/amenities resolution: covered parking defaults to `1` for Gated Community/Semi Gated when absent, explicit counts are preserved, open parking defaults to `-`, and society amenities use exact live Sheet dropdown combinations.

`landmark` falls back to `locality` when no better source value exists. `society_name` falls back to locality only as a last resort and is review-flagged. `pincode` and property age are non-blocking optional fields; image URLs are a separate media flow.

## Deterministic audit status — 2026-09-15

The hardened Phase-1 contract remains a 48-field canonical `Housing_Listings` schema with deterministic fields owned by the panel and downstream fields protected. `catalog_title` and `property_highlights` remain valid deterministic fields but may be wording-only AI beautification outputs after the Phase-1 boundary.

The deterministic repository work is complete for the current Phase-1 Inventory Management scope. The remaining items are live/external runtime verification dependencies documented separately in `docs/OPEN_POINTERS.md`; they are not unresolved deterministic field-contract defects.

## Live-system migration reconciliation — 2026-09-16

The repository now carries the approved live-system operational boundary on top of the latest canonical `main` without importing legacy Inventory processing. Lead Management and its current Slack/runtime surfaces remain under their existing new-repository ownership. The live WhAPI boundary routes the configured inventory listeners into the Stage-1 adapter and ordinary inbound traffic into Lead Management.

`modules/efps-inventory-mgmnt/src/inventory_runtime.py` is the only migrated Inventory runtime adapter: it captures the live Stage-1 session boundary, durable session state, deduplication, and raw intake, then delegates closed sessions to the existing canonical Inventory pipeline. `handler.py` provides the scheduled Raw-row worker using the same canonical package.

Legacy Inventory extraction, normalization, deterministic business rules, field resolution, property processing, validation/business logic, and Stage-2 implementation are explicitly excluded from the migration.

## Production status

The repository-level migration reconciliation is complete on its dedicated migration branch. Production acceptance is not claimed by this commit: AWS deployment, Slack registration, WhAPI cutover, secret injection, synthetic live Inventory traffic, and old-runtime zero-traffic confirmation remain runtime gates.
