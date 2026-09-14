# EFPS Internal Automations — AI Operating Rules

## Purpose

This repository contains EasyFind Property Solutions internal business automations. It is designed for AI-agent-driven development and must remain simple, understandable, safe, and expandable.

## Repository model

- `modules/` contains business capabilities and business decisions.
- `shared/` contains reusable technical integrations and capabilities.
- `docs/` contains the canonical business and system knowledge.
- `HANDOFF.md` contains the current temporary working state between sessions.
- `.gemini/skills/` contains repeatable AI-agent operating procedures.

## Core boundary

> Shared services provide capabilities; modules decide when and why those capabilities are used.

Shared code must not contain module-specific business rules.

## Documentation rule

The root is for AI/repository operation. `docs/` is the single canonical home for business and system knowledge. Do not create duplicate authoritative documents elsewhere. When implementation changes reality, update the relevant canonical documentation in the same work session.

## AI-agent working rule

Before changing code, understand the current repository state, read the relevant root guidance, `HANDOFF.md`, applicable documents in `docs/`, and local module/shared guidance. State a plain-language plan before significant implementation. Never guess when repository evidence is available.

## Session rule

Use the `session-start` and `session-end` skills for every development session. `HANDOFF.md` is live state, not a permanent session diary.

## Safety rule

Do not commit secrets, tokens, passwords, private keys, or production credentials. Do not modify unrelated modules or shared integrations without a clear reason and validation.

## Expansion rule

Do not create speculative folders or frameworks. Add structure only when actual functionality requires it.
