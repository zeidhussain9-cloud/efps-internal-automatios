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

For every implementation, the agent must review all maintained root and `docs/` documentation and update every document whose content is affected by the resulting repository reality. Do not create duplicate authoritative documents.

## Current modules

- `modules/efps-inventory-mgmnt/` — property inventory business workflows and rules.
- `modules/efps-meta-catalogue-mgmnt/` — Meta/WhatsApp catalogue business workflows.
- `modules/efps-housing-portal-mgmnt/` — placeholder for future Housing.com automation.
- `modules/efps-website-mgmnt/` — EasyFind website management and automation.

## Shared capabilities

The shared layer currently contains these established capability boundaries:

- `shared/cloudinary/` — media storage/upload and stable media-reference capabilities.
- `shared/google_sheets/` — Google Sheets connectivity and range/worksheet operations.
- `shared/whatsapp_whapi/` — WhAPI transport, authentication, webhook, messaging, media, and connection capabilities.

Shared services provide technical capabilities; modules decide when and why those capabilities are used.

This repository is being implemented capability-by-capability. A capability may have a documented boundary before every runtime feature is complete; implementation status must be stated accurately and must not be guessed.
