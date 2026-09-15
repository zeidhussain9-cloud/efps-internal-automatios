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

- `modules/efps-inventory-mgmnt/` — canonical Inventory business workflows and deterministic processing.
- `modules/efpd-lead-mgmnt/` — canonical Lead/Enquiry business workflows and migrated live lead-management behavior.
- `modules/efps-meta-catalogue-mgmnt/` — reserved future Meta/WhatsApp catalogue business workflows; not part of the current migration.
- `modules/efps-housing-portal-mgmnt/` — reserved future Housing.com automation; not part of the current migration.
- `modules/efps-website-mgmnt/` — website management and automation.

## Established shared capabilities

- `shared/cloudinary/` — reusable Cloudinary media storage/upload capability with deterministic property/lead namespaces.
- `shared/credentials/` — canonical local macOS Keychain credential provider.
- `shared/google_maps/` — reusable Google Maps URL extraction and Geocoding resolution capability.
- `shared/google_sheets/` — reusable Google Sheets technical access plus the canonical 48-column `Housing_Listings` A:AV contract.
- `shared/slack/` — reusable Slack transport, security, routing, and the shared WhAPI/Slack operational integration surface.
- `shared/whatsapp_whapi/` — provider-specific WhAPI transport and webhook/message primitives used by the shared operational surface.
- `shared/webhook/` — generic HTTP webhook request/response primitives.

## Inventory processing model

Inventory uses three top-level stages:

1. **Stage 1 — Initial / Webhook**: dedicated inventory listener, `NEW` property-session boundary, raw capture, and initial row.
2. **Stage 2 — Deterministic Extraction / Property Processing**: canonical source segmentation, deterministic candidate extraction/resolution, normalization/business rules, Google Maps resolution, deterministic validation, optional AI verification, and wording-only AI beautification.
3. **Stage 3 — Downstream Operations**: a boundary for future/downstream consumers; it is not part of the current migration.

The legacy repository is not an authority for any Inventory business rule or processing behavior. The current new-repository Inventory implementation remains authoritative.

## Live-system migration

The current migration moves only approved live operational capabilities into the new architecture. Lead Management is migrated into `modules/efpd-lead-mgmnt/`; shared technical capabilities are reused rather than duplicated. Legacy Inventory logic, downstream publishing, and Society Approvals remain out of scope.

See `docs/MIGRATION_LIVE_SYSTEM_MAP_20260916.md` for the explicit migration classification and current live-verification boundaries.

## Production status

Repository migration implementation and external-system live cutover are separate verification states. Code placement and integration can be reviewed from the repository; live WhAPI/Slack/AWS cutover remains `NOT VERIFIED` until the target runtime acceptance probes succeed.
