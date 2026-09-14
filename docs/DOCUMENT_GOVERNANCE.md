# Document Governance

Every maintained document in this repository must have one clear role.

## Document classes

- **Human:** owner decisions, business context, architecture explanations, or judgement that cannot be safely generated.
- **Validated:** hand-written documents whose important facts can be checked against implementation or verified infrastructure.
- **Generated:** documents produced from a source of truth. Never hand-edit the generated output; change the source and regenerate it.
- **Executable:** documents consumed directly by automation or models where structure is enforced by code.
- **Historical:** dated records of what was true at a particular point in time. Do not silently refresh them into current truth.
- **Legacy:** retained only as evidence of an old system. Never treat it as current instructions.

## Repository rule

A new maintained document should be added to `DOCUMENT_MAP.md` and assigned a class before it becomes part of the working contract.

The new repository should avoid duplicating the same fact across multiple authoritative documents. Put business rules in `BUSINESS_CONTEXT.md`, engineering rules in `PROJECT_RULES.md`, architecture in `ARCHITECTURE.md`, infrastructure identifiers in `INFRASTRUCTURE.md`, unresolved decisions in `OPEN_POINTERS.md`, and current session state in `HANDOFF.md`.