# EFPS Internal Automations — Gemini Operating Adapter

This file is the Gemini-specific operating adapter for EFPS Internal Automations.

## Mandatory core steering

Before every response or action, Gemini MUST apply the repository's `CORE_STEERING.md` protocol. This applies to every iteration, including one-word messages, continuation requests, small edits, commands, recommendations, and implementation work.

`CORE_STEERING.md` is mandatory and is not optional session guidance.

## Purpose

This repository contains EasyFind Property Solutions internal business automations. It is designed for AI-agent-driven development and must remain simple, understandable, safe, and expandable.

## Repository model

- `modules/` contains business capabilities and business decisions.
- `shared/` contains reusable technical integrations and capabilities.
- `docs/` contains the canonical business and system knowledge.
- `HANDOFF.md` contains the current temporary working state between sessions.
- `.gemini/skills/` contains repeatable AI-agent operating procedures.

## Required Gemini workflow

For every task:

1. Apply `CORE_STEERING.md`.
2. Understand the exact user request.
3. Establish the facts required for the task from authoritative sources.
4. Read the relevant root guidance, `HANDOFF.md`, applicable documents in `docs/`, and relevant module/shared guidance.
5. Do not guess or assume missing facts.
6. For significant work, state the immediate plan in plain language before implementation.
7. Execute the smallest safe step.
8. Verify the result against repository/runtime truth.
9. Review and update affected canonical documentation when reality changes.
10. Report the verified result and the next step when the task continues.

If a required fact cannot be established, stop and ask the user or provide a precise verification command/procedure. Never manufacture certainty.

## Core boundary

> Shared services provide capabilities; modules decide when and why those capabilities are used.

Shared code must not contain module-specific business rules.

## Documentation rule

The root is for AI/repository operation. `docs/` is the single canonical home for business and system knowledge. Do not create duplicate authoritative documents elsewhere. When implementation changes reality, update the relevant canonical documentation in the same work session.

## Session rule

Use the `session-start` and `session-end` skills for every development session. `HANDOFF.md` is live state, not a permanent session diary.

## Safety rule

Do not commit secrets, tokens, passwords, private keys, or production credentials. Do not modify unrelated modules or shared integrations without a clear reason and validation.

## Expansion rule

Do not create speculative folders or frameworks. Add structure only when actual functionality requires it.
