# Gemini Skills

Repeatable AI-agent operating procedures for this repository.

Current repository-wide skills include:

- `session-start/` — establish repository truth and session plan before implementation.
- `session-end/` — reconcile code, documentation, validation, and current handoff state before finishing work.
- `core-steering/` — apply the mandatory repository steering protocol.
- `truth-verification/` — establish authoritative facts before acting.
- `change-planning/` — plan implementation boundaries and affected documentation.
- `change-verification/` — validate resulting repository behavior and state.
- `documentation-governance/` — route and verify documentation updates.
- `handoff-update/` — maintain current cross-session state.
- `repository-audit/` — inspect repository truth and structural consistency.

Repository-specific shared capability skills:

- `cloudinary/` — EFPS Cloudinary media-storage capability and verified credential boundary.
- `google-maps/` — reusable Google Maps technical resolution capability.
- `google-sheets/` — EFPS Google Sheets access plus the canonical 48-column `Housing_Listings` contract/ownership/stage rules.
- `whapi/` — EFPS WhAPI/WhatsApp integration, webhook configuration, listener routing facts, and safety rules.

A capability skill is technical guidance for that shared capability; business workflow decisions remain with the owning module.

For every implementation, review all maintained root documents and all documents in `docs/`, and update affected documentation in the same work session.
