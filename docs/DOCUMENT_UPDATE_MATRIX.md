# Documentation Update Matrix

**Status:** Initial routing baseline  
**Purpose:** Define which canonical documents must be reviewed or updated when repository reality changes.

> This matrix is a routing guide. It does not replace `CORE_STEERING.md` or `DOCUMENT_GOVERNANCE.md`.

| Change type | Mandatory document review/update |
|---|---|
| Core AI operating protocol changes | `CORE_STEERING.md`, `AGENTS.md`, `GEMINI.md`, affected AI skills |
| General AI-agent governance changes | `AGENTS.md`, `CORE_STEERING.md` if core protocol is affected |
| Gemini workflow/operating changes | `GEMINI.md`, affected Gemini skills |
| Current task/session state changes | `HANDOFF.md` |
| Repository structure changes | `docs/ARCHITECTURE.md`, `README.md`, `docs/DOCUMENT_MAP.md`, affected module/shared README files |
| Business rule/context changes | `docs/BUSINESS_CONTEXT.md` |
| Engineering/governance rule changes | `docs/PROJECT_RULES.md` |
| Architecture/boundary changes | `docs/ARCHITECTURE.md`, `docs/DATA_CONTRACTS.md` when data ownership/contracts are affected |
| Data ownership/schema/contract changes | `docs/DATA_CONTRACTS.md` |
| Infrastructure/resource changes | `docs/INFRASTRUCTURE.md` |
| New unresolved decision/unknown/conflict | `docs/OPEN_POINTERS.md` |
| Documentation structure/role changes | `docs/DOCUMENT_GOVERNANCE.md`, `docs/DOCUMENT_MAP.md` |
| Module responsibility/behavior changes | Relevant module `README.md` and `GEMINI.md`; canonical docs when cross-module truth changes |
| Shared capability responsibility/behavior changes | Relevant shared capability `README.md`; canonical docs when cross-cutting truth changes |
| Repository overview changes | Root `README.md` |
| New/changed repository-wide skill | `.gemini/skills/README.md`, affected skill `SKILL.md`, and relevant governance docs |
| New/changed module-specific skill | Relevant module skill documentation and module README/GEMINI guidance |
| New/changed shared-capability skill | Relevant shared capability skill documentation and shared README guidance |

## Mandatory agent behavior

For every change, the agent must determine whether one or more rows apply. A document marked for review must be checked against the resulting repository reality even when no textual update is ultimately required.

If the matrix does not clearly cover a change, do not guess. Establish the correct documentation owner before proceeding and update this matrix if a durable routing rule is discovered.

## Maintenance

This matrix is intentionally a baseline while the repository foundation is being established. It must be refined as actual implementation reveals new document ownership or recurring update patterns.
