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

- `cloudinary/` — EFPS Cloudinary media-storage capability, verified credential boundary, and media handling rules.
- `google-sheets/` — EFPS Google Sheets access plus the canonical `Housing_Listings` schema/ownership contract.
- `whapi/` — EFPS WhAPI/WhatsApp integration skill and references.

A capability skill is technical guidance for that shared capability; business workflow decisions remain with the owning module.

For every implementation, review all maintained root documents and all documents in `docs/`, and update affected documentation in the same work session.
