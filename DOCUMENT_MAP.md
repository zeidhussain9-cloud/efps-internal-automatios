# Document Map

This file explains the role of maintained repository documents so future AI sessions know where a fact or decision belongs.

## Root

| Document | Role |
|---|---|
| `GEMINI.md` | Gemini CLI operating adapter and concise repository rules |
| `AGENTS.md` | Canonical AI-agent precedence and working rules |
| `PROJECT_RULES.md` | Standing engineering and automation rules |
| `BUSINESS_CONTEXT.md` | EFPS business rules, terminology, tone, and decision principles |
| `ARCHITECTURE.md` | Repository structure, boundaries, and established flows |
| `INFRASTRUCTURE.md` | External systems and verified resource identifiers; never secrets |
| `OPEN_POINTERS.md` | Unresolved decisions and verified unknowns |
| `HANDOFF.md` | Current working state between sessions |
| `README.md` | Human-oriented repository entry point |

## Documentation governance

`docs/DOCUMENT_GOVERNANCE.md` defines document classes and which documents are generated, executable, validated, human-maintained, historical, or legacy.

`docs/DOC_POLICY.md` defines how documentation is kept current during development.

## Contract documentation

`docs/data-contracts.md` records cross-module data ownership and contracts established in the new repository. More specific contracts should be added only when the related systems are actually implemented.

## Module and shared documentation

Every module and shared capability has its own `README.md` explaining its purpose and boundary. Module `GEMINI.md` files provide local AI-agent guidance.