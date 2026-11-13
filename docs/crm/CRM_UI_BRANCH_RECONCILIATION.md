# CRM UI branch and release reconciliation

> Revalidated 2026-11-13 against GitHub, Render and the active local checkout. The follow-up source correction remains local pending approval for publication.

## Canonical branch model

- main: canonical release/integration branch.
- crm-ui-dashboard: canonical CRM implementation and Render deployment branch.
- Render deploys from crm-ui-dashboard.
- Remote `crm-ui-dashboard` points to `6b206ddf07515cff2df82140d86ee873e4ea2965`; remote `main` points to `954b24fc21b8b91a6bd5cae3e24a116e31fbdce7`. Their tree hashes matched at `7cce604603616847c9994fdeb45e432141b5a4ad` before the local follow-up fix.
- No force-push or history rewrite was used.

## Additional branch refs

GitHub also lists four Dependabot branch refs associated with open PRs #93, #94, #96 and #97. They are automated dependency PR heads, not additional human CRM implementation/deployment branches. Retain them while their PRs are open; do not merge dependency upgrades without separate compatibility review.

## Live release evidence

- Render service: srv-darsv560tbcc73cu4ip0.
- Latest live deployment: `dep-dbrbc8gjo6nc73etsmr0`, commit `6b206ddf07515cff2df82140d86ee873e4ea2965`. Routes `/health` and `/` returned HTTP 200; no post-deploy error logs were returned. Inventory Contract failed on that remote commit due to reserved Notion fields; local commit `6e16562` fixes this and passes the audit, but publication was rejected by approval review.
- Supabase Edge Function: whapi-crm-webhook ACTIVE v10.
- Webhook reconciliation: 18,641/18,641 message events since 2026-10-05 linked; 0 active errors.
- Inventory (updated 2026-11-13): 104 active Notion-owned rows (87 Available / 17 Rented); Sheet reconciliation cron removed; dashboard reads Notion only.
- Deterministic scheduler: 923 completed / 0 failed; AI scheduler remains paused.
- GitHub Actions: build and automated test workflows passed; 139/139 unit/integration tests and browser 1/1 passed. Production-health smoke job skipped.

## Local checkout

The active local checkout is on `crm-ui-dashboard`. Its reserved-field correction and current-session documentation are not published; remote refs remain at the commits recorded above. GitHub is the remote canonical release record.

## Release gate

1. Implement on crm-ui-dashboard.
2. Verify build, automated tests and browser regression.
3. Wait for Render to report the exact candidate LIVE.
4. Verify Supabase, webhook and inventory sync evidence.
5. Reconcile main to the verified CRM branch and confirm identical trees.
6. Update current-state documentation from live evidence.

Detailed current evidence is in CRM_CURRENT_VERIFIED_STATE.md and CRM_RECOVERY_AUDIT_2026-11-12.md.