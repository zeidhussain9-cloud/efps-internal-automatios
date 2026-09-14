# EFPS Internal Automations — Project Rules

These are the canonical standing engineering and automation rules for this repository.

## 1. Verified truth

Do not guess when repository evidence can establish the fact. Check files, code, configuration, or the relevant external source before acting. If a fact cannot be established, state the uncertainty and stop before making a consequential change.

## 2. Simplicity

Prefer the smallest implementation that solves the actual business problem. Avoid speculative abstractions, duplicate systems, and premature infrastructure.

## 3. Naming

Use lowercase, hyphenated module names following the EFPS convention: `efps-{module-name}-{resource-type}`. Modules are named, not numbered.

## 4. Architecture boundary

`shared/` contains reusable technical capabilities. `modules/` contains EFPS business capabilities and business decisions. Shared code must not contain module-specific business rules.

## 5. Documentation

When code or architecture changes reality, update the relevant documentation in the same work session. Do not knowingly leave code and documented ownership inconsistent.

## 6. Security

Never commit API keys, tokens, passwords, private keys, or production credentials. Store secrets through approved runtime configuration or secret-management mechanisms.

## 7. Idempotency

Automations should be safe to retry whenever the business operation permits it. Where true idempotency is impossible, document the limitation in the owning module.

## 8. Validation before side effects

Business-critical writes must pass the owning module's deterministic validation and permission checks before an external write is performed.

## 9. Controlled external actions

Technical access is not equivalent to business authorization. Do not send messages, alter live property data, publish listings, or call sensitive external APIs merely because the system can technically do so.

## 10. AI boundary

AI may assist with interpretation where explicitly allowed, but it must not silently become the source of truth for canonical business facts when deterministic source data exists.

## 11. Session discipline

Every development session should begin by reading the current repository guidance and `HANDOFF.md`, then establish the current state before changing code. End the session by updating the current working state and affected documentation.

## 12. No speculative repository structure

Add folders, services, schemas, deployments, or tooling when an actual capability requires them. The skeleton intentionally uses placeholders rather than invented implementation structure.
