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

- `CORE_STEERING.md` — mandatory core steering protocol applied by every AI agent before every response or action.
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
- `shared/google_maps/` — reusable Google Maps URL extraction and Geocoding resolution capability; live application-path verified for Inventory Phase 1.
- `shared/google_sheets/` — reusable Google Sheets technical access plus the canonical 48-column `Housing_Listings` A:AV contract; live read/write boundary verified for Inventory Phase 1.
- `shared/slack/` — reusable Slack operational capability for the authorized Inventory Phase-1 workflows.
- `shared/whatsapp_whapi/` — reusable WhAPI technical transport, live gate, channel/settings primitives, webhook normalization, and neutral messaging primitives.

## Inventory Phase-1 processing model

Inventory uses three top-level stages:

1. **Stage 1 — Initial / Webhook**: dedicated inventory listener, `NEW` property-session boundary, raw capture, and initial row.
2. **Stage 2 — Deterministic Extraction / Property Processing**: deterministic extraction, normalization/business rules, Google Maps resolution, deterministic validation, optional AI verification, and wording-only AI beautification.
3. **Stage 3 — Downstream Operations**: a boundary for future/downstream consumers; it is not part of the current Inventory Phase-1 publishing implementation.

Google Maps is a Stage-2 sub-step, not a separate stage. Google Sheets is transport/output, not a top-level stage.

## Production status

Repository/source hardening is maintained separately from live external-system verification. Inventory Phase-1 Google Sheets and Google Maps runtime probes have been completed successfully. Other external integrations remain explicitly `NOT VERIFIED` until their applicable target-runtime acceptance probes succeed.
