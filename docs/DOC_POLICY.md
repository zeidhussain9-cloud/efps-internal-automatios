# Documentation Policy

Documentation is part of the implementation, not a separate cleanup task.

## Rules

1. Establish facts from the repository or verified external sources before documenting them.
2. Update the relevant document during the same work session when implementation changes its reality.
3. Do not keep duplicate competing statements of the same fact in multiple authoritative documents.
4. Current state belongs in `HANDOFF.md`; permanent business rules belong in `BUSINESS_CONTEXT.md`; engineering rules belong in `PROJECT_RULES.md`.
5. Unresolved owner decisions belong in `OPEN_POINTERS.md` rather than being resolved by agent assumption.
6. A generated document must be updated through its source of truth, not by hand.
7. Historical records must retain their dates and must not be silently rewritten into current truth.
8. A new document is not complete until its role is recorded in `DOCUMENT_MAP.md`.

## Session practice

Update documentation as work happens rather than reconstructing the state from memory after a long session. At session end, verify that code, contracts, architecture, and current state still agree.