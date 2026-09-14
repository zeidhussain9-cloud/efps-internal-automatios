# EFPS Internal Automations — Core Steering Protocol

**Version:** 1.0  
**Status:** MANDATORY  
**Scope:** Entire repository  
**Applies to:** Every AI agent, every interaction, every iteration, every response, and every action

## Absolute rule

This protocol is the repository's core AI operating gate. Every AI agent working in this repository MUST apply it before responding to the user, making a recommendation, executing a command, modifying a file, or taking any other action.

No task is too small to bypass this protocol. A one-word user iteration, a continuation request, or a minor edit must still pass through the same steering gate.

## 1. Ground every response and action in verified truth

Every response and action MUST be based on facts that are grounded in the current EFPS repository and, when required, the verified source of the fact.

The agent must distinguish between:

- Repository-verified facts.
- Verified runtime or external-system facts.
- Explicit current-session user instructions or facts.
- Unknown information.
- Conflicting information.
- Historical or potentially stale information.

Do not present an unverified statement as fact.

## 2. Never guess or assume

The agent MUST NOT guess, assume, infer unsupported facts, invent missing values, or silently fill gaps merely to continue a task.

If a required fact is unavailable, the agent MUST stop at that decision point and either:

1. Establish the fact from an authoritative available source; or
2. Ask the user for the missing information; or
3. Give the user a precise command or verification procedure needed to establish the fact.

## 3. Establish truth before acting

Before acting on a user request, the agent MUST establish the facts necessary to perform the requested work safely and correctly.

If the repository, runtime, external system, or user has not established a necessary fact, the agent MUST NOT manufacture certainty. It must explicitly identify the missing fact and establish it before proceeding.

When sources disagree, the agent MUST surface the conflict and establish which source is authoritative rather than silently choosing one.

## 4. Work step by step

Every non-trivial user task MUST be decomposed into small, verifiable steps.

The agent MUST:

1. Establish the relevant facts.
2. State the immediate plan in plain language when work is significant.
3. Perform one logical step at a time.
4. Verify the result of that step.
5. Update the user after meaningful completed steps when the task spans multiple steps.
6. Continue only when the next step is supported by verified state.

Small tasks may be completed in one step, but the steering protocol still applies.

## 5. Source authority and conflicts

The agent MUST use the repository's documented authority model and MUST NOT silently resolve contradictions.

For repository-defined knowledge, use the applicable canonical document and verify against implementation when necessary. For current behavior, prefer verified running/runtime state over stale documentation. For business decisions, do not redefine the owner's established rules without explicit instruction.

When two authoritative-looking sources conflict:

- Identify the conflict.
- Do not silently select a convenient source.
- Establish the correct source of truth.
- Update affected documentation if the established truth changes.

## 6. No silent changes

The agent MUST NOT silently:

- Change business rules.
- Change architecture.
- Change data ownership or contracts.
- Rename established resources.
- Create new modules or shared capabilities without justification.
- Modify unrelated files.
- Change infrastructure assumptions.
- Replace one source of truth with another.

Material decisions must be explicit and grounded.

## 7. Verification is mandatory

Implementation is not complete merely because code was written.

A completed change requires, as applicable:

- Implementation completed.
- Relevant behavior verified.
- Tests or other appropriate validation completed.
- Documentation checked for impact.
- Required documentation updated.
- No known unresolved contradiction introduced.

## 8. Documentation is part of implementation

Documentation updates are part of the change, not optional cleanup.

Whenever implementation changes the documented reality, the affected canonical documentation MUST be updated in the same work session.

The repository's documentation ownership and update rules must be followed uniformly. The documentation update matrix, once established, becomes the canonical routing table for deciding which documents require review or update after each type of change.

## 9. Never manufacture certainty

The agent is explicitly permitted and required to say:

- `UNKNOWN`
- `NOT VERIFIED`
- `CONFLICTING`
- `NEEDS USER INPUT`
- `NEEDS RUNTIME VERIFICATION`

These are valid states. The agent must prefer an explicit unknown over an invented answer.

## 10. Security and scope

Never commit secrets, credentials, tokens, passwords, private keys, or other sensitive authentication material.

Do not expose production data merely to make implementation easier.

Do not modify unrelated modules, shared capabilities, documentation, or infrastructure merely because they are nearby.

## Mandatory pre-response / pre-action checklist

Before every response or action, the agent must internally confirm:

- What exactly did the user request?
- What facts are established?
- Which facts are not established?
- What repository sources are authoritative for this task?
- Is any part of the proposed response or action based on a guess?
- Are there conflicting sources?
- What is the smallest safe next step?
- What must be verified after that step?
- Which documentation must be reviewed or updated if the state changes?

If a necessary answer to these questions is not established, the agent must stop and establish it before proceeding.

## Relationship to other repository guidance

This file defines the core steering protocol. `AGENTS.md` defines general AI-agent integration and must enforce this protocol. `GEMINI.md` defines Gemini-specific integration and must enforce this protocol. `HANDOFF.md` records temporary current state. `docs/` contains canonical permanent business and system knowledge.
