# EFPS Internal Automations — Current Handoff

## Current state

The repository skeleton and documentation foundation are established. No business implementation is included at this stage.

The mandatory AI operating foundation now includes `CORE_STEERING.md`, which every AI agent must apply before every response or action. `AGENTS.md` and `GEMINI.md` explicitly enforce this protocol.

## Source review completed

The legacy `efps-platform` repository was reviewed for naming convention, business rules, document governance, architecture, infrastructure registry, cross-project contract, and open-pointer practices.

The new repository intentionally does not clone the legacy repository. Reusable governance and valid EFPS business-context concepts were carried forward and adapted to the new architecture.

## Current architecture

- Root contains AI/repository operating entry points.
- `CORE_STEERING.md` is the mandatory core AI operating protocol.
- `docs/` is the single canonical home for business and system knowledge.
- `modules/` contains EFPS business capabilities and business decisions.
- `shared/` contains reusable technical capabilities.
- Shared capabilities provide capabilities; modules decide when and why those capabilities are used.
- `efps-website-mgmnt` is dedicated exclusively to EasyFind website management.
- WhatsApp/WhAPI remains a shared technical capability under `shared/whatsapp_whapi/` rather than a separate business module.

## Current documentation model

Root: `README.md`, `CORE_STEERING.md`, `GEMINI.md`, `AGENTS.md`, and `HANDOFF.md`.

Canonical docs: `docs/BUSINESS_CONTEXT.md`, `docs/PROJECT_RULES.md`, `docs/ARCHITECTURE.md`, `docs/DATA_CONTRACTS.md`, `docs/INFRASTRUCTURE.md`, `docs/DOCUMENT_GOVERNANCE.md`, `docs/DOCUMENT_MAP.md`, and `docs/OPEN_POINTERS.md`.

A documentation update matrix is intentionally deferred until the remaining documentation migration/foundation work is complete, so it can be built against the final canonical document set rather than a moving structure.

No duplicate architecture, business-context, project-rule, or documentation-policy files should be introduced.

## Current modules

- `efps-inventory-mgmnt`
- `efps-meta-catalogue-mgmnt`
- `efps-housing-portal-mgmnt`
- `efps-website-mgmnt`

## Current shared capabilities

- `google_sheets`
- `cloudinary`
- `whatsapp_whapi`

## Next development rule

Before implementing a capability, apply `CORE_STEERING.md`, then read the root guidance, `HANDOFF.md`, the applicable documents in `docs/`, and the relevant module/shared `README.md` and `GEMINI.md`. Establish current source truth before making implementation changes.
