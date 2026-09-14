# EFPS Internal Automations — Current Handoff

## Current state

The repository skeleton, documentation foundation, mandatory AI steering layer, documentation update matrix, and initial skill placeholders are established. No business implementation is included at this stage.

`CORE_STEERING.md` is mandatory for every AI agent, every interaction, and every iteration. `AGENTS.md` and `GEMINI.md` enforce it.

## Source review completed

The legacy `efps-platform` repository was reviewed for naming convention, business rules, document governance, architecture, infrastructure registry, cross-project contract, open-pointer practices, and custom agent skills.

Legacy Slack-specific skills are not carried forward because they are not part of the new repository architecture. The legacy WhAPI skill was identified as the relevant repository-specific custom skill and a new placeholder/reference structure has been created under `.gemini/skills/whapi/`; its contents must be rebuilt only from verified requirements and current integration truth.

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

Canonical docs: `docs/BUSINESS_CONTEXT.md`, `docs/PROJECT_RULES.md`, `docs/ARCHITECTURE.md`, `docs/DATA_CONTRACTS.md`, `docs/INFRASTRUCTURE.md`, `docs/DOCUMENT_GOVERNANCE.md`, `docs/DOCUMENT_MAP.md`, `docs/DOCUMENT_UPDATE_MATRIX.md`, and `docs/OPEN_POINTERS.md`.

`DOCUMENT_UPDATE_MATRIX.md` is now established as the canonical routing baseline. It must evolve only when actual implementation reveals durable documentation ownership or recurring update patterns.

No duplicate architecture, business-context, project-rule, or documentation-policy files should be introduced.

## Current AI skills

Repository-wide Gemini operating skills include `session-start`, `session-end`, `core-steering`, `truth-verification`, `change-planning`, `change-verification`, `documentation-governance`, `handoff-update`, and `repository-audit`.

The repository-specific `whapi` custom skill is currently a placeholder derived from the legacy skill's verified structural coverage; it is not yet a complete technical reference.

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

Before implementing a capability, apply `CORE_STEERING.md`, then read the root guidance, `HANDOFF.md`, the applicable documents in `docs/`, and the relevant module/shared guidance. Establish current source truth before making implementation changes. At session end, verify the result, apply the documentation update matrix, update `HANDOFF.md`, and validate the final repository state.
