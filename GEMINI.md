# EFPS Internal Automations — Gemini Operating Adapter

Gemini CLI work in this repository follows `CORE_STEERING.md` first and these repository rules second.

## Before every task

- Read and apply `CORE_STEERING.md`.
- Read `HANDOFF.md` and relevant `docs/` and local guidance.
- Establish verified repository/runtime truth before acting.
- Never guess or silently fill missing facts.
- For significant work, state the immediate plan, perform one logical step, verify it, then continue.

## Mandatory documentation rule

For **every implementation**, Gemini must review **all maintained root documents** and **all documents inside `docs/`** against the resulting repository reality.

Maintained root documents:

- `README.md`
- `CORE_STEERING.md`
- `AGENTS.md`
- `GEMINI.md`
- `HANDOFF.md`

Maintained `docs/` documents are defined by `docs/DOCUMENT_MAP.md`.

Every affected document must be updated in the same implementation. Documents not affected must still be checked for continued accuracy. Update `HANDOFF.md` when current task/session state changes.

Apply `docs/DOCUMENT_UPDATE_MATRIX.md` and `docs/DOCUMENT_GOVERNANCE.md` for detailed routing.

## Current architecture truth

- Root = AI/repository operation.
- `docs/` = canonical business/system truth.
- `modules/` = business capabilities.
- `shared/` = reusable technical capabilities.
- Current active shared implementation scope: **only** `shared/cloudinary/`.

Do not treat another shared capability as active until it is explicitly established and verified.

## Gemini-specific maintenance

`GEMINI.md` is a live operating adapter. Update it when Gemini workflow, repository layout, or mandatory Gemini-specific operating requirements change.

## Session procedure

Use `.gemini/skills/session-start/SKILL.md` at session start and `.gemini/skills/session-end/SKILL.md` at session end. Use the applicable repository-wide and custom skills for verification, planning, documentation, and capability-specific work.

## Security

Never commit secrets, API tokens, passwords, private keys, or production authentication material.
