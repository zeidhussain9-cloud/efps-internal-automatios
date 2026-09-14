# EFPS Internal Automations — AI Operating Rules

## Purpose
This repository contains EasyFind Property Solutions internal business automations. It is designed for AI-agent-driven development and must remain simple, understandable, safe, and expandable.

## Repository Model
- `modules/` contains business capabilities and business decisions.
- `shared/` contains reusable technical integrations and capabilities.
- `docs/` contains shared cross-module truth.
- `HANDOFF.md` contains the current temporary working state.
- `.gemini/skills/` contains repeatable AI-agent operating procedures.

## Core Boundary
Shared services provide capabilities; modules decide when and why those capabilities are used. Shared code must not contain module-specific business rules.

## Documentation Rule
When implementation changes reality, update the relevant documentation in the same work session. Do not leave code and documented architecture, ownership, or current status inconsistent.

## AI-Agent Working Rule
Before changing code, understand the current repository state, read the relevant root/module/shared guidance, state a plain-language plan, then implement the smallest safe change. Never guess when repository evidence is available.

## Session Rule
Use the `session-start` and `session-end` skills for every development session. `HANDOFF.md` is live state, not a permanent session diary.

## Safety Rule
Do not commit secrets, tokens, passwords, private keys, or production credentials. Do not modify unrelated modules or shared integrations without a clear reason and validation.

## Expansion Rule
Do not create speculative folders or frameworks. Add structure only when actual functionality requires it.
