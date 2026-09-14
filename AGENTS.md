# Agent Rules

This is the canonical precedence and working guide for AI agents in EFPS Internal Automations.

## Authority order

1. The owner's instruction in the current session.
2. `docs/PROJECT_RULES.md` for standing engineering and automation rules.
3. Running code and verified external infrastructure for actual system behavior.
4. `docs/BUSINESS_CONTEXT.md` for EFPS business decisions and domain rules.
5. `docs/ARCHITECTURE.md`, `docs/INFRASTRUCTURE.md`, `docs/DATA_CONTRACTS.md`, `docs/OPEN_POINTERS.md`, and module/shared guidance for documented structure and ownership.
6. General explanatory prose and historical records are lower authority than the sources above.

## Before changing anything

Read the root guidance, `HANDOFF.md`, the applicable documents in `docs/`, and the relevant module/shared guidance. Establish the current state from the repository before making a change.

## Working principles

- Do not guess.
- Do not silently redefine EFPS business rules.
- Do not add a second source of truth when an existing authoritative source exists.
- Explain the plan in plain language before significant implementation.
- Keep changes small and verifiable.
- Update documentation when implementation changes the documented reality.

## Naming

Use lowercase, hyphenated names and the EFPS `efps-{module-name}-{resource-type}` convention where applicable. Do not number modules. Do not add an `-agent` suffix unless the owner explicitly establishes a new convention.

## Security

Never commit credentials or sensitive secrets. Do not expose production data merely to make an implementation easier.
