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

- Render service: `srv-darsv560tbcc73cu4ip0`; the signed-in production inventory page showed 104 Notion-owned properties (87 Available / 17 Rented Out).
- Live Notion/Supabase reconciliation: 104 active pages / 104 active snapshots; 0 missing, orphaned, duplicate or semantic field mismatches. All 104 intake events have matching Listing IDs.
- `notion-inventory-state` ACTIVE v9; AWS `efps-notion-intake` Active; CloudFormation stack `UPDATE_COMPLETE`.
- A 15-minute scheduled reconciler queues changed/restored pages, repairs event-to-listing mappings, and soft-deletes missing projections. Empty source results fail closed. A soft-delete/recovery test passed on rented listing `EF-2609-09B5`.
- Actual Notion `page.undeleted` webhook delivery is not independently observed; the scheduled fallback now restores a page that is active in Notion even if that webhook is missed.
- Reserved `source_group` and `inventory_locked` are blank across all 104 Notion pages; 43 populated `inventory_locked` values were cleared.
- Sheet reconciliation cron is removed. Legacy Sheet writes and old WhAPI inventory path remain until separately agreed cleanup. No CRM UI or lead classification changes were made.

## Local checkout

The active local checkout is on `crm-ui-dashboard` and tracks the published branch after the release reconciliation. `main` and `crm-ui-dashboard` have identical tracked trees. GitHub is the remote release record.

## Release gate

1. Actual Notion `page.undeleted` delivery remains unobserved; the 15-minute reconciliation fallback now recovers missed restores and was live-tested on an active rented listing. Keep the eight user-confirmed Page event selections unchanged.
2. Keep the Sheets compatibility paths and old WhAPI listener until their separately agreed cleanup.

Detailed current evidence is in CRM_CURRENT_VERIFIED_STATE.md and CRM_RECOVERY_AUDIT_2026-11-12.md.
