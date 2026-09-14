# Document Governance

This is the canonical policy for maintaining documentation in EFPS Internal Automations.

## Core rule

Every maintained document must have one clear role and one canonical subject. Do not duplicate the same authoritative fact across multiple documents.

## Document classes

- **Human:** owner decisions, business context, architecture explanations, or judgement that cannot be safely generated.
- **Validated:** hand-written documents whose important facts can be checked against implementation or verified infrastructure.
- **Generated:** documents produced from a source of truth. Never hand-edit generated output; change the source and regenerate it.
- **Executable:** documents consumed directly by automation or models where structure is enforced by code.
- **Historical:** dated records of what was true at a particular point in time. Do not silently refresh them into current truth.
- **Legacy:** retained only as evidence of an old system. Never treat it as current instructions.

## Canonical ownership

- Business rules → `BUSINESS_CONTEXT.md`
- Engineering rules → `PROJECT_RULES.md`
- Architecture → `ARCHITECTURE.md`
- Data ownership/contracts → `DATA_CONTRACTS.md`
- Infrastructure identifiers → `INFRASTRUCTURE.md`
- Unresolved decisions/unknowns → `OPEN_POINTERS.md`
- Current working state → `HANDOFF.md`
- Document roles → `DOCUMENT_MAP.md`
- AI operating instructions → root `CORE_STEERING.md`, `GEMINI.md`, and `AGENTS.md`

## Mandatory implementation review

For **every implementation**, review all maintained documents in the repository root and all documents inside `docs/` against the resulting repository reality.

The maintained root set is:

- `README.md`
- `CORE_STEERING.md`
- `AGENTS.md`
- `GEMINI.md`
- `HANDOFF.md`

The maintained `docs/` set is defined by `DOCUMENT_MAP.md`.

Update every affected document in the same work session. Documents not affected must still be checked for continued accuracy. Update `HANDOFF.md` whenever current task/session state changes.

## Maintenance rules

1. Establish facts from repository evidence or verified external sources before documenting them.
2. Update the relevant canonical document in the same work session when implementation changes its reality.
3. Do not keep duplicate competing statements of the same fact.
4. Use `DOCUMENT_UPDATE_MATRIX.md` as the routing baseline, without weakening the full-review requirement above.
5. Resolve open pointers only from verified evidence or explicit owner decisions.
6. Update generated documents through their source of truth.
7. Preserve historical records as historical records.
8. Add every new maintained document to `DOCUMENT_MAP.md`.

Documentation is part of implementation. A change is not complete when code and maintained repository truth knowingly disagree.
