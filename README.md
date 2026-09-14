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

## Documentation rule

Business and system documentation belongs in `docs/`. Do not create duplicate authoritative documents in the root or elsewhere. Each maintained document must have one clear role and one canonical subject.

## Current modules

- `modules/efps-inventory-mgmnt/` — property inventory business workflows and rules.
- `modules/efps-meta-catalogue-mgmnt/` — Meta/WhatsApp catalogue business workflows.
- `modules/efps-housing-portal-mgmnt/` — placeholder for future Housing.com automation.
- `modules/efps-website-mgmnt/` — EasyFind website management and automation.

## Current shared capabilities

- `shared/google_sheets/` — reusable Google Sheets capabilities.
- `shared/cloudinary/` — reusable Cloudinary media capabilities.
- `shared/whatsapp_whapi/` — reusable WhatsApp/WhAPI capabilities.

This repository is currently a structural foundation. Implementation is added only when the corresponding capability is actually required.
