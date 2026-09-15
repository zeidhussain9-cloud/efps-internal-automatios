# EFPS Internal Automations — Core Steering Protocol

**Version:** 1.2  
**Status:** MANDATORY  
**Scope:** Entire repository  
**Applies to:** Every AI agent, every interaction, every iteration, every response, and every action

## Absolute rule

This protocol is the repository's core AI operating gate. Every AI agent working in this repository MUST apply it before responding to the user, making a recommendation, executing a command, modifying a file, or taking any other action.

No task is too small to bypass this protocol. A one-word user iteration, a continuation request, or a minor edit must still pass through the same steering gate.

## 1. Ground every response and action in verified truth

Every response and action MUST be based on facts grounded in the current EFPS repository and, when required, the verified source of the fact.

The agent must distinguish between repository-verified facts, verified runtime/external facts, explicit current-session user instructions, unknown information, conflicts, and historical/stale information.

## 2. Never guess or assume

The agent MUST NOT guess, assume, infer unsupported facts, invent missing values, or silently fill gaps merely to continue a task.

If a required fact is unavailable, the agent MUST establish it from an authoritative source, ask the user for the missing information, or provide a precise verification procedure.

## 3. Establish truth before acting

Before acting on a request, establish the facts necessary to perform the work safely and correctly. Conflicts must be surfaced and resolved from an authoritative source rather than silently choosing one.

## 4. Work step by step

Every non-trivial task MUST be decomposed into small, verifiable steps: establish facts, state the immediate plan when significant, perform one logical step, verify it, update the user after meaningful steps, then continue only from verified state.

## 5. Source authority and conflicts

Use the documented authority model. For current behavior, prefer verified implementation/runtime state over stale documentation. For business decisions, do not redefine established owner rules without explicit instruction.

## 6. No silent changes

The agent MUST NOT silently change business rules, architecture, data ownership, established names, unrelated files, infrastructure assumptions, or sources of truth.

## 7. Verification is mandatory

Implementation is not complete merely because code was written. Completion requires relevant implementation, appropriate validation, documentation review/update, and no known unresolved contradiction introduced.

## 8. Documentation is part of every implementation

For **every implementation**, the agent MUST review **all maintained documents in the repository root** and **all documents inside `docs/`** against the resulting repository reality.

The maintained root set is:

- `README.md`
- `CORE_STEERING.md`
- `AGENTS.md`
- `GEMINI.md`
- `HANDOFF.md`

The maintained `docs/` set is defined by `docs/DOCUMENT_MAP.md`.

Every affected document MUST be updated in the same work session. Documents not affected MUST still be checked for continued accuracy. `HANDOFF.md` MUST be updated when current task/session state changes.

## 9. Never manufacture certainty

The agent is explicitly permitted and required to say `UNKNOWN`, `NOT VERIFIED`, `CONFLICTING`, `NEEDS USER INPUT`, or `NEEDS RUNTIME VERIFICATION` when appropriate.

## 10. Security and scope

Never commit secrets, credentials, tokens, passwords, private keys, or other sensitive authentication material. Do not expose production data merely to make implementation easier.

## Shared-capability rule

The repository currently has six established shared capability boundaries:

- `shared/cloudinary/`
- `shared/credentials/`
- `shared/google_maps/`
- `shared/google_sheets/`
- `shared/slack/`
- `shared/whatsapp_whapi/`

A shared capability may be structurally established before every runtime feature is complete. Status must be stated accurately; capability boundaries must not be mistaken for proof that every feature is live.

## Mandatory pre-response / pre-action checklist

Before every response or action, the agent must internally confirm:

- What exactly did the user request?
- What facts are established?
- Which facts are not established?
- What sources are authoritative for this task?
- Is any part based on a guess?
- Are there conflicting sources?
- What is the smallest safe next step?
- What must be verified after that step?
- Which root and `docs/` documents must be updated if repository reality changes?

If a necessary answer is not established, the agent must stop and establish it before proceeding.

## Relationship to other repository guidance

This file defines the core steering protocol. `AGENTS.md` defines general AI-agent integration and must enforce this protocol. `GEMINI.md` defines Gemini-specific integration and must enforce this protocol. `HANDOFF.md` records temporary current state. `docs/` contains canonical permanent business and system knowledge.
