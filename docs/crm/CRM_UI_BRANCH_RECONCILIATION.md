# CRM UI branch and release reconciliation

> Verified 2026-11-12 14:50 IST against GitHub, the Mac worktrees and the live Render deployment.

## Canonical branch model

- `main`: canonical release/integration branch.
- `crm-ui-dashboard`: canonical CRM implementation and Render deployment branch.
- Render deploys from `crm-ui-dashboard`.
- Before this recovery release, `main` was at `0aae093b8b4fc524aa731d16cf5603d39b830598`; the CRM branch release commit `97dff533cfeee3138866277430a471ccc8369ac3` includes that main checkpoint as its parent. This permits a fast-forward reconciliation without force-push.
- Final release closeout advances `main` to the verified `crm-ui-dashboard` head and verifies `tree(main) == tree(crm-ui-dashboard)`.
- GitHub lists four additional Dependabot refs tied to open PRs #93, #94, #96 and #97. These are automation PR heads, not human development/deployment branches; retain them while their PRs remain open. Do not merge their major dependency upgrades without separate compatibility testing.

## Recovery release evidence

- Render service: `easyfind-crm-d01-d05` / `srv-darsv560tbcc73cu4ip0`.
- Live deployment at the recovery checkpoint: `dep-dbqo57o473hc73881mdg`, commit `97dff533cfeee3138866277430a471ccc8369ac3`.
- Supabase project: `qttcutwzehtskfcwxkwj`; `whapi-crm-webhook` ACTIVE v10.
- Production health and root routes return HTTP 200.
- Inventory sync returned consecutive HTTP 200 responses at five-minute cadence with 104 rows and 0 changes on the stable runs.
- WhAPI: 18,621/18,621 message events since 2026-10-05 linked to `crm_messages`; 0 current errors.
- Group messages are not attached to lead timelines; 1,809 historical group links were removed with prior associations retained.
- Deterministic scheduler: 922 completed / 0 failed since 2026-10-05; AI scheduler remains paused.

## Local checkout

- Repository: `/Users/zeidzakir/Projects/efps-internal-automatios`.
- CRM worktree: `/Users/zeidzakir/Projects/efps-internal-automatios/leads_automation/crm-ui-dashboard`.
- The nested CRM worktree tracks `crm-ui-dashboard`; the root worktree tracks `main`.
- The unrelated pre-existing workspace files were preserved. No clean/reset operation was used on unrelated files.
- After GitHub branch updates, fetch and sync both worktrees from GitHub; do not treat a local-only commit as canonical.

## Release gate

1. Commit and push implementation to `crm-ui-dashboard`.
2. Verify build, full automated tests, browser regression and production-specific checks.
3. Wait for Render to report the exact candidate LIVE; verify Supabase and external sync results.
4. Refresh current-state docs with production evidence.
5. Fast-forward `main` to the verified CRM branch head; verify both refs have the same tree.
6. Confirm only the two canonical human branches remain; open Dependabot refs are retained only while their PRs are open.

Detailed live status is maintained in `CRM_CURRENT_VERIFIED_STATE.md`; the recovery evidence is in `CRM_RECOVERY_AUDIT_2026-11-12.md`.