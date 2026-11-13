# CRM UI branch and release reconciliation

> Revalidated 2026-11-13 after the Notion inventory release.

## Canonical branch model

- main: canonical release/integration branch.
- crm-ui-dashboard: canonical CRM implementation and Render deployment branch.
- Render deploys from crm-ui-dashboard.
- Render is live on the verified `crm-ui-dashboard` release. Its published source and docs are reconciled into `main`; the tracked trees are identical.
- No force-push or history rewrite was used.

## Additional branch refs

GitHub also lists four Dependabot branch refs associated with open PRs #93, #94, #96 and #97. They are automated dependency PR heads, not additional human CRM implementation/deployment branches. Retain them while their PRs are open; do not merge dependency upgrades without separate compatibility review.

## Live release evidence

- Render service: srv-darsv560tbcc73cu4ip0.
- Latest live deployment: `dep-dbrei8avcj2c73erda3g` is LIVE on commit `ddb0f6391f99ba9a848fd30c8b03bd5db9c1b53c`; routes `/health` and `/` returned HTTP 200. GitHub Inventory Contract passed 130/130, SAM container build/validation passed, and Production health smoke passed.
- Supabase inventory: 104 active Notion rows (87 Available / 17 Rented). Create, edit, Listing ID write-back, duplicate suppression, soft-delete, and restore were tested with an identified temporary page. Delete/restore were direct worker invokes, not confirmed webhook deliveries. Its Supabase rows were removed; the Notion page remains in Trash pending permanent removal through signed-in UI.
- Supabase Edge Function: whapi-crm-webhook ACTIVE v10.
- Webhook reconciliation: 18,641/18,641 message events since 2026-10-05 linked; 0 active errors.
- Inventory (updated 2026-11-13): 104 active Notion-owned rows (87 Available / 17 Rented); Sheet reconciliation cron removed; dashboard reads Notion only.
- Deterministic scheduler: 923 completed / 0 failed; AI scheduler remains paused.
- GitHub Actions on current release: CRM tests/build/browser passed; Inventory Contract 130/130 passed; SAM container validation passed; Production health smoke passed.

## Local checkout

The active local checkout is on `crm-ui-dashboard` and tracks the published branch after the release reconciliation. `main` and `crm-ui-dashboard` have identical tracked trees. GitHub is the remote release record.

## Release gate

1. Sign in to production CRM and verify the authenticated inventory page.
2. Permanently remove the temporary test page from Notion Trash.
3. Keep the Sheets compatibility paths and old WhAPI listener until their separately agreed cleanup.

Detailed current evidence is in CRM_CURRENT_VERIFIED_STATE.md and CRM_RECOVERY_AUDIT_2026-11-12.md.
