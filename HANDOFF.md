# EFPS Internal Automations — Current Handoff

## Current state

The repository documentation foundation and mandatory AI steering layer are established. The shared layer now has three established capability boundaries: `cloudinary`, `google_sheets`, and `whatsapp_whapi`.

`CORE_STEERING.md` is mandatory for every AI agent, every interaction, and every iteration. `AGENTS.md` and `GEMINI.md` enforce it.

For every implementation, all maintained root documents and all documents in `docs/` must be reviewed against resulting repository reality. Affected documents must be updated in the same work session.

## Source review completed

The legacy `efps-platform` repository was reviewed for naming convention, business rules, document governance, architecture, infrastructure registry, cross-project contract, open-pointer practices, and custom agent skills.

The legacy `efps-whapi-panel` provides verified reference behavior for the shared capability boundaries. Its Cloudinary media layer uses deterministic property paths and a separate lead-media namespace. Its configuration resolves credentials from AWS Secrets Manager with environment-variable fallback. Its WhAPI network traffic is explicitly gated before live calls. fileciteturn228file0L2-L2 fileciteturn229file0L2-L2 fileciteturn223file0L2-L2

Legacy Slack-specific skills are not carried forward because they are not part of the new repository architecture. The legacy WhAPI skill remains relevant as source material for the repository-specific `.gemini/skills/whapi/` structure; technical details must be carried forward only after verification against current requirements/current integration truth.

## Current architecture

- Root contains AI/repository operating entry points.
- `CORE_STEERING.md` is the mandatory core AI operating protocol.
- `docs/` is the single canonical home for business and system knowledge.
- `modules/` contains EFPS business capabilities and business decisions.
- `shared/` contains reusable technical capabilities.
- Shared capabilities provide capabilities; modules decide when and why those capabilities are used.
- `efps-website-mgmnt` is dedicated exclusively to EasyFind website management.

## Shared capability implementation state

### `shared/cloudinary/`

Implemented as a reusable technical package boundary with credential loading, dependency-injected upload transport, deterministic property and lead media identifiers, upload helpers, catalogue URL limiting, and image fingerprinting. Live credentials are not stored in the repository.

### `shared/google_sheets/`

Restored as the canonical shared Google Sheets capability boundary. Its technical implementation is the next integration surface to complete from verified requirements; business ownership remains in modules.

### `shared/whatsapp_whapi/`

Restored as the canonical shared WhAPI capability boundary. Its implementation must follow the verified legacy safety pattern: live network traffic is explicitly gated and secrets remain outside the repository.

## Current documentation model

Root: `README.md`, `CORE_STEERING.md`, `GEMINI.md`, `AGENTS.md`, and `HANDOFF.md`.

Canonical docs: `docs/BUSINESS_CONTEXT.md`, `docs/PROJECT_RULES.md`, `docs/ARCHITECTURE.md`, `docs/DATA_CONTRACTS.md`, `docs/INFRASTRUCTURE.md`, `docs/DOCUMENT_GOVERNANCE.md`, `docs/DOCUMENT_MAP.md`, `docs/DOCUMENT_UPDATE_MATRIX.md`, and `docs/OPEN_POINTERS.md`.

`DOCUMENT_UPDATE_MATRIX.md` is the canonical routing baseline and also requires a full review of every maintained root and `docs/` document for every implementation.

No duplicate architecture, business-context, project-rule, or documentation-policy files should be introduced.

## Current AI skills

Repository-wide Gemini operating skills include `session-start`, `session-end`, `core-steering`, `truth-verification`, `change-planning`, `change-verification`, `documentation-governance`, `handoff-update`, and `repository-audit`.

The repository-specific `whapi` custom skill is currently a placeholder/reference structure derived from the legacy skill; it is not treated as verified live integration behavior.

## Current modules

- `efps-inventory-mgmnt`
- `efps-meta-catalogue-mgmnt`
- `efps-housing-portal-mgmnt`
- `efps-website-mgmnt`

## Next development rule

Before implementing a capability, apply `CORE_STEERING.md`, read the root guidance, `HANDOFF.md`, the applicable documents in `docs/`, and the relevant module/shared guidance. Establish current source truth before making implementation changes. At the end of every implementation, review all maintained root and `docs/` documents, update every affected document, update `HANDOFF.md`, and validate the final repository state.
