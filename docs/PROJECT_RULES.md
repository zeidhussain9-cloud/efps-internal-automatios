# Project Rules

These are standing engineering and automation rules for EFPS Internal Automations.

## Truth and scope

1. Apply `CORE_STEERING.md` before every response or action.
2. Establish repository and runtime truth before implementation; never guess or silently infer missing facts.
3. Use the smallest safe change that satisfies the verified requirement.
4. Do not modify unrelated modules, shared capabilities, infrastructure, or documentation.
5. Preserve explicit business ownership boundaries.

## Architecture

- `modules/` owns EFPS business capabilities and business decisions.
- `shared/` owns reusable technical capabilities and must remain business-neutral.
- Shared services provide capabilities; modules decide when and why they are used.
- The current active shared implementation scope is only `shared/cloudinary/`.
- New shared capabilities require explicit justification and verification before being treated as repository structure.

## Documentation

- `docs/` is the canonical home for permanent business and system knowledge.
- Every implementation must review every maintained root document and every document inside `docs/` against resulting repository reality.
- Update every affected document in the same work session.
- Update `HANDOFF.md` whenever current working state changes.
- Use `DOCUMENT_UPDATE_MATRIX.md` and `DOCUMENT_GOVERNANCE.md` for document ownership and routing.
- Do not create duplicate authoritative documents.

## Security

- Never commit secrets, API tokens, passwords, private keys, or production authentication material.
- Do not expose production data merely to simplify implementation.
- Document verified resource identifiers without storing secret values.

## Validation

A change is complete only when the applicable implementation, verification, validation, and documentation checks are complete and there are no known contradictions with repository truth.
