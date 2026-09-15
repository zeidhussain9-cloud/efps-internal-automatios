# Documentation Update Matrix

**Status:** Active baseline  
**Purpose:** Define which maintained documents must be reviewed or updated when repository reality changes.

> This matrix is a routing guide. It does not replace `CORE_STEERING.md` or `DOCUMENT_GOVERNANCE.md`.

| Change type | Mandatory document review/update |
|---|---|
| Core AI operating protocol changes | `CORE_STEERING.md`, `AGENTS.md`, `GEMINI.md`, affected AI skills |
| General AI-agent governance changes | `AGENTS.md`, and `CORE_STEERING.md` if core protocol is affected |
| Gemini workflow/operating changes | `GEMINI.md`, affected Gemini skills |
| Current task/session state changes | `HANDOFF.md` |
| Repository structure changes | `docs/ARCHITECTURE.md`, root `README.md`, `docs/DOCUMENT_MAP.md`, affected local README/GEMINI files |
| Business rule/context changes | `docs/BUSINESS_CONTEXT.md` |
| Engineering/governance rule changes | `docs/PROJECT_RULES.md` |
| Architecture/boundary changes | `docs/ARCHITECTURE.md`, `docs/DATA_CONTRACTS.md` when contracts/ownership are affected |
| Data ownership/schema/contract changes | `docs/DATA_CONTRACTS.md` |
| Infrastructure/resource changes | `docs/INFRASTRUCTURE.md` |
| Credential-provider or credential-reference changes | `docs/INFRASTRUCTURE.md`, affected shared capability credential registry/README, `HANDOFF.md`, and `docs/OPEN_POINTERS.md` when verification state changes |
| New unresolved decision/unknown/conflict | `docs/OPEN_POINTERS.md` |
| Documentation structure/role changes | `docs/DOCUMENT_GOVERNANCE.md`, `docs/DOCUMENT_MAP.md` |
| Module responsibility/behavior changes | Relevant module `README.md` and `GEMINI.md`; canonical docs when cross-module truth changes |
| Shared capability responsibility/behavior changes | Relevant shared `README.md`; canonical docs when cross-cutting truth changes |
| Inventory source-extraction behavior changes | `docs/INVENTORY_SOURCE_EXTRACTION.md`, `docs/ARCHITECTURE.md`, `docs/DATA_CONTRACTS.md` if field semantics change, Inventory module `README.md`, affected regression fixtures, `HANDOFF.md` |
| Repository overview changes | Root `README.md` |
| Repository-wide AI skill changes | `.gemini/skills/README.md`, affected skill, relevant governance docs |
| Repository-specific custom skill changes | `.gemini/skills/README.md`, affected skill and references, relevant capability/module docs |

## Mandatory agent behavior

For **every implementation**, the agent must review **all maintained root documents and all documents inside `docs/`** against the resulting repository reality. It must update every document that is affected and must confirm the remaining documents are still accurate. This full review is mandatory even when the change appears small.

For a shared capability implementation, review the capability's local `README.md`, relevant capability code/tests, and the canonical architecture, contracts, infrastructure, and open-pointer documents.

For all other maintained documentation, use the routing table above to identify additional local documents that must be reviewed or updated.

If the matrix does not clearly cover a change, do not guess. Establish the correct documentation owner before proceeding and update this matrix if a durable routing rule is discovered.

## Maintenance

This matrix is the canonical routing baseline. It must be refined when actual implementation reveals a new durable document owner or recurring update pattern.
