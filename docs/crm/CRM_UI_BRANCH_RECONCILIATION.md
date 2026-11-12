# CRM UI branch and release reconciliation

> Revalidated 2026-11-12 against GitHub, Render and the owner's explicit local-checkout instruction.

## Canonical branch model

- main: canonical release/integration branch.
- crm-ui-dashboard: canonical CRM implementation and Render deployment branch.
- Render deploys from crm-ui-dashboard.
- Both canonical branches currently point to commit d4083c8c33802f33295b090b9b1c4e71453b5090 and share tree ba5b62470c4bbb97a155451db18dae17229a3133.
- No force-push or history rewrite was used.

## Additional branch refs

GitHub also lists four Dependabot branch refs associated with open PRs #93, #94, #96 and #97. They are automated dependency PR heads, not additional human CRM implementation/deployment branches. Retain them while their PRs are open; do not merge dependency upgrades without separate compatibility review.

## Live release evidence

- Render service: srv-darsv560tbcc73cu4ip0.
- Latest live deployment: dep-dbqod1nf3r2c73fe2gc0, commit d4083c8c33802f33295b090b9b1c4e71453b5090.
- Supabase Edge Function: whapi-crm-webhook ACTIVE v10.
- Webhook reconciliation: 18,641/18,641 message events since 2026-10-05 linked; 0 active errors.
- Inventory: 104 active rows; five-minute cron active; latest successful run 09:55 UTC.
- Deterministic scheduler: 923 completed / 0 failed; AI scheduler remains paused.
- GitHub Actions: build and automated test workflows passed; 139/139 unit/integration tests and browser 1/1 passed. Production-health smoke job skipped.

## Local checkout

The owner has deleted all local Mac checkouts and explicitly instructed that no local version be searched for or recreated. No local checkout is part of this release verification. GitHub is the canonical repository state.

## Release gate

1. Implement on crm-ui-dashboard.
2. Verify build, automated tests and browser regression.
3. Wait for Render to report the exact candidate LIVE.
4. Verify Supabase, webhook and inventory sync evidence.
5. Reconcile main to the verified CRM branch and confirm identical trees.
6. Update current-state documentation from live evidence.

Detailed current evidence is in CRM_CURRENT_VERIFIED_STATE.md and CRM_RECOVERY_AUDIT_2026-11-12.md.