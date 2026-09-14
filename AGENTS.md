# Agent Rules

This is the canonical general operating guide for AI agents in EFPS Internal Automations.

## Mandatory core steering

`CORE_STEERING.md` is the repository's mandatory core AI operating protocol.

Every AI agent MUST apply `CORE_STEERING.md` before every response, recommendation, command, file change, or other action. This applies to every iteration, including one-word user messages, continuation requests, and seemingly trivial tasks.

No agent may bypass the Core Steering Protocol because a task appears small or obvious.

## Authority and truth

Agents must establish truth before acting. They must not guess, assume, invent missing information, or silently fill gaps.

Repository-defined facts must be grounded in the current repository. Runtime or external behavior must be verified from the relevant current source when required. Explicit current-session user instructions are authoritative for the requested action, subject to safety and repository constraints.

If a necessary fact is unavailable, the agent must stop and either establish it from an authoritative source, ask the user for it, or provide a precise command/verification procedure to establish it.

If sources conflict, the agent must surface the conflict and establish the correct source of truth rather than silently choosing one.

## Before changing anything

Apply `CORE_STEERING.md`, then read the relevant root guidance, `HANDOFF.md`, applicable documents in `docs/`, and relevant module/shared guidance. Establish the current repository state before making a change.

## Stepwise execution

Break non-trivial tasks into small, verifiable steps. State the immediate plan in plain language before significant implementation, execute the smallest safe step, verify it, and update the user after meaningful completed steps when the task spans multiple steps.

## No silent changes

Do not silently redefine business rules, change architecture, alter data ownership/contracts, rename established resources, create speculative modules/shared capabilities, modify unrelated files, change infrastructure assumptions, or replace an existing source of truth.

## Verification

A change is not complete merely because code was written. Completion requires appropriate implementation verification, validation, documentation impact review, required documentation updates, and no known unresolved contradiction introduced.

## Documentation

Documentation is part of implementation. When implementation changes documented reality, update the affected canonical documentation in the same work session.

Follow the repository's documentation governance and documentation update routing consistently. `HANDOFF.md` is for live temporary state; permanent business and system knowledge belongs in `docs/`.

## Naming

Use lowercase, hyphenated names and the EFPS `efps-{module-name}-{resource-type}` convention where applicable. Do not number modules. Do not add an `-agent` suffix unless the owner explicitly establishes a new convention.

## Security

Never commit credentials, secrets, tokens, passwords, private keys, or production authentication material. Do not expose production data merely to make implementation easier.

## Required behavior when certainty is unavailable

Agents must explicitly use states such as `UNKNOWN`, `NOT VERIFIED`, `CONFLICTING`, `NEEDS USER INPUT`, or `NEEDS RUNTIME VERIFICATION` when applicable. Never manufacture certainty merely to provide an answer.
