# Session End Skill

Use this at the end of every EFPS Internal Automations development session.

## Mandatory steering

Apply `CORE_STEERING.md` as part of the final verification gate before declaring any task complete.

## Steps

1. Review the files changed in the session.
2. Verify implementation against current repository truth and relevant runtime/external facts.
3. Check for unknowns, conflicts, or unsupported assumptions; do not declare completion with unresolved required facts.
4. Review documentation impact and update all affected canonical documents in the same work session.
5. Update `HANDOFF.md` so it reflects the current working state.
6. Validate the work that can be validated at the current stage.
7. Confirm the resulting repository state/commit before declaring the task complete.

## Principle

A task is not complete when code exists but repository documentation, current state, and verified reality are inconsistent.
