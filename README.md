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

- `modules/efps-inventory-mgmnt/` — property inventory business workflows and rules.
- `modules/efpd-lead-mgmnt/` — lead/enquiry business workflows and rules.
- `modules/efps-meta-catalogue-mgmnt/` — Meta/WhatsApp catalogue business workflows.
- `modules/efps-housing-portal-mgmnt/` — placeholder for future Housing.com automation.
- `modules/efps-website-mgmnt/` — EasyFind website management and automation.

## Established shared capabilities

- `shared/cloudinary/` — reusable Cloudinary media storage/upload capability.
- `shared/google_sheets/` — reusable Google Sheets technical access plus the canonical `Housing_Listings` contract/schema.
- `shared/whatsapp_whapi/` — reusable WhAPI/WhatsApp technical integration boundary with explicit live-traffic safety controls, webhook configuration, and normalized message delivery.

These boundaries do not imply that every endpoint, workflow, or live production integration is complete. Implementation status must be verified before calling a capability production-ready.
