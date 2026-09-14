# Document Map

This document is the canonical map of maintained repository documentation. It tells future AI sessions where a fact, rule, decision, contract, or current-state update belongs.

## Root: AI/repository operation

| Document | Role |
|---|---|
| `README.md` | Human-oriented repository entry point |
| `CORE_STEERING.md` | Mandatory core AI operating protocol |
| `GEMINI.md` | Gemini CLI operating adapter and concise repository rules |
| `AGENTS.md` | General AI-agent operating rules and core-steering enforcement |
| `HANDOFF.md` | Current working state between sessions |

## `docs/`: business and system truth

| Document | Role |
|---|---|
| `BUSINESS_CONTEXT.md` | EFPS business rules, terminology, tone, and decision principles |
| `PROJECT_RULES.md` | Standing engineering and automation rules |
| `ARCHITECTURE.md` | Repository structure, boundaries, and established flows |
| `DATA_CONTRACTS.md` | Cross-module data ownership and contracts |
| `INFRASTRUCTURE.md` | External systems and verified resource identifiers; never secrets |
| `DOCUMENT_GOVERNANCE.md` | Document classes, authority, and maintenance governance |
| `DOCUMENT_UPDATE_MATRIX.md` | Routing table for documentation review/update decisions |
| `OPEN_POINTERS.md` | Unresolved decisions and verified unknowns |

## Local documentation

Every module and shared capability has its own `README.md` explaining its purpose and boundary. Module `GEMINI.md` files provide local AI-agent guidance.

Repository-wide Gemini skills live under `.gemini/skills/`. Repository-specific custom skills may have reference files under their skill directory when the procedure requires detailed material.

## Single-source rule

One fact or rule should have one canonical home. Other documents may link to or summarize it, but must not create a competing authoritative version.

If a new maintained document is required, add it to this map and define its role before treating it as repository truth.
