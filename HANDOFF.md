# EFPS Internal Automations — Current Handoff

## Current state

The repository skeleton is established. No business implementation is included at this stage.

## Source review completed

The legacy `efps-platform` repository was reviewed for its naming convention, business rules, document governance, architecture, infrastructure registry, cross-project contract, and open-pointer model.

The new repository intentionally does not clone the legacy repository. Only reusable governance and business-context concepts relevant to the new architecture have been carried forward.

## Current architecture

- `shared/` contains reusable technical capabilities.
- `modules/` contains EFPS business capabilities and business decisions.
- Shared capabilities provide capabilities; modules decide when and why those capabilities are used.
- `efps-website-mgmnt` is dedicated exclusively to EasyFind website management.
- WhatsApp/WhAPI remains a shared technical capability under `shared/whatsapp_whapi/` rather than a separate business module.

## Current documentation foundation

Root governance and business documents now include `AGENTS.md`, `PROJECT_RULES.md`, `BUSINESS_CONTEXT.md`, `ARCHITECTURE.md`, `INFRASTRUCTURE.md`, `OPEN_POINTERS.md`, `DOCUMENT_MAP.md`, `GEMINI.md`, `README.md`, and this `HANDOFF.md`.

Cross-repository documentation includes document governance, documentation policy, architecture details, and data-contract guidance under `docs/`.

## Current modules

- `efps-inventory-mgmnt`
- `efps-meta-catalogue-mgmnt`
- `efps-housing-portal-mgmnt`
- `efps-website-mgmnt`

## Current shared services

- `google_sheets`
- `cloudinary`
- `whatsapp_whapi`

## Next development rule

Before implementing a capability, read the root guidance, `HANDOFF.md`, the relevant module/shared `README.md` and `GEMINI.md`, and the applicable documents in `docs/`. Establish current source truth before making implementation changes.