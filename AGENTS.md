# EFPS Internal Automations — AI Agent Rules

## Mandatory core steering

Before every response, recommendation, command, file change, or other action, apply `CORE_STEERING.md`.

There are no trivial-task exceptions. One-word inputs, continuation requests, small edits, and implementation requests all pass through the same steering gate.

## Operating requirements

1. Establish current truth from repository evidence, verified runtime/external sources, and explicit user instructions.
2. Never guess, invent missing facts, or silently resolve conflicts.
3. Break non-trivial work into small, verifiable steps and verify each meaningful step before proceeding.
4. Keep business rules in their canonical documents and business decisions in the owning module.
5. Keep shared capabilities technical and business-neutral.
6. Do not make silent changes to architecture, data ownership, infrastructure assumptions, names, or unrelated files.
7. Treat documentation as part of implementation, not optional cleanup.

## Mandatory documentation review for every implementation

For **every implementation**, review **all maintained documents in the repository root** and **all documents inside `docs/`** against the resulting repository reality.

The maintained root set currently includes:

- `README.md`
- `CORE_STEERING.md`
- `AGENTS.md`
- `GEMINI.md`
- `HANDOFF.md`

The maintained `docs/` set is defined by `docs/DOCUMENT_MAP.md`.

Every affected document must be updated in the same implementation. Documents whose subjects are unchanged must still be checked for accuracy. `HANDOFF.md` must be updated whenever current task/session state changes.

Use `docs/DOCUMENT_UPDATE_MATRIX.md` and `docs/DOCUMENT_GOVERNANCE.md` to route additional local documentation updates.

## Current repository architecture

- Root = AI/repository operation.
- `docs/` = canonical business and system truth.
- `modules/` = EFPS business capabilities and business decisions.
- `shared/` = reusable technical capabilities.

The repository currently has six established shared capability boundaries:

- `shared/cloudinary/`
- `shared/credentials/`
- `shared/google_maps/`
- `shared/google_sheets/`
- `shared/slack/`
- `shared/whatsapp_whapi/`

Established boundary does not mean every runtime feature is complete. Implementation status must be stated accurately and verified before being called live or production-ready.

## Security

Never commit secrets, credentials, tokens, passwords, private keys, or production authentication material.

## Completion standard

A change is complete only when implementation, applicable validation, repository verification, and required documentation updates are complete with no known contradiction.
