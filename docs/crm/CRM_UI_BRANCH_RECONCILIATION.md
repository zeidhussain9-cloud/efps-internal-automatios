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

- Render service: srv-darsv560tbcc73cu4ip0. The signed-in browser showed deployment `dep-dbrev7ajnfac739de33g` LIVE on `61688164b25f7a7a8e6df8248f91987a9c471ef6`; `/health` and `/` returned HTTP 200 in the release check.
- GitHub `crm-ui-dashboard` is `61688164b25f7a7a8e6df8248f91987a9c471ef6`; `main` is `3c66a89e734d02ade5b4865f05c2dcbc99ec655b`. Both share tree `14717bf1d37afa8d678fc0526026dae357755fdf`.
- Supabase inventory and signed-in dashboard: 104 listings (87 Available / 17 Rented). A Notion edit visibly propagated through Supabase to the dashboard. A real delete event reached Supabase and soft-deleted the row after about one minute. Earlier duplicate handler replay returned `already_processed`.
- Restore is an open live-flow failure: restoring the test page in Notion produced no observed Lambda invocation or Edge Function POST, so the Supabase row remained soft-deleted. The direct restore handler was checked separately and is not evidence of webhook delivery.
- The exact test rows were removed from Supabase; the test page was permanently deleted from Notion Trash after user approval. Dashboard returned to 104 listings.
- Supabase Edge Function `whapi-crm-webhook`: ACTIVE v10. Inventory Sheet cron is removed; compatibility Sheet writes remain. The old WhAPI inventory path stays until final cleanup.
- Earlier code-bearing release passed Inventory Contract 130/130, SAM container build/validation, CRM checks, and production health smoke. The latest documentation-only commit's path-filtered Inventory Contract rerun is not established here.

## Local checkout

The active local checkout is on `crm-ui-dashboard` and tracks the published branch after the release reconciliation. `main` and `crm-ui-dashboard` have identical tracked trees. GitHub is the remote release record.

## Release gate

1. Diagnose why restore did not deliver the selected Notion `page.undeleted` event; safely repeat the end-to-end restore check only with a new identified test record and remove it afterward.
2. Keep the Sheets compatibility paths and old WhAPI listener until their separately agreed cleanup.

Detailed current evidence is in CRM_CURRENT_VERIFIED_STATE.md and CRM_RECOVERY_AUDIT_2026-11-12.md.
