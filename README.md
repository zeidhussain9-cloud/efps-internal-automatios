## Current inventory intake deployment — 2026-11-13

- Isolated AWS stack `efps-notion-property-intake`: `UPDATE_COMPLETE` in `ap-southeast-2`.
- Lambda `efps-notion-intake`: Active; endpoint `https://ko3771nvei.execute-api.ap-southeast-2.amazonaws.com/Prod/notion/intake`.
- Invalid Notion handshake/event signatures: HTTP 401; validly signed malformed event: HTTP 400. Controlled create/archive write probes for both Notion databases: HTTP 200. Supabase idempotency claim/replay: PASS.
- Notion Housing Listings is the canonical editing surface. The isolated `efps-notion-property-intake` Lambda is deployed in AWS account `294417174793` (`ap-southeast-2`) with the direct Supabase projection path. The existing Housing Listings backfill queued 104 pages; Supabase confirms 104 processed pages and 104 active `housing_notion` rows in the dashboard snapshot. The existing EFPS CRM Property Intake Connection was found in Notion Developer Connections; the user confirmed its webhook and all eight Page events remain selected.
- Existing AWS secret ARNs were reused without creating, rotating, overwriting, or displaying secret values. The legacy WhAPI `NEW`-delimited inventory listener remains untouched until final cleanup.
- Checks: `npm test` (139 passed, includes production build), inventory Python suite (88 passed), browser check (1 passed), and SAM template lint passed. Deployment reused the previously built Linux dependency artifact because no container runtime is installed.
- The dashboard now reads active `housing_notion` rows only. The old five-minute Sheet reconciliation is disabled. Slack `/efps` and raw photo intake remain legacy compatibility producers while their future Notion handoff is finalized.

## CRM production metrics snapshot — 2026-10-05 (historical; not reverified in this task)

- Production branch: `crm-ui-dashboard`
- Verified release candidate: `dd7ba3e94293181c620825433e5f2be8a71e91ff`
- Verified tree: `verified after the documentation release is reconciled into main`
- GitHub Actions: CRM Synthetic CI PASS; CRM UI Verification PASS on the same commit.
- Local MacBook checkout `/Users/zeidzakir/Projects/efps-internal-automatios-local/efps-internal-automatios` was reset to the verified `crm-ui-dashboard` remote branch for release verification.
- Production Render deployment: dep-db1b2svf3r2c73brd6m0 is LIVE from 1982c7ea0a158ee0edcb00fad43e021876c13b9d; /health returns HTTP 200.
- Historical production verification: 253 leads, 9,224 messages, 3,025 persisted webhook events, 277 AI runs, 214 drafts, 88 inventory rows (71 Available / 17 Rented Out).
- Scheduler state at that historical checkpoint: webhook reconciliation is active every minute; inventory reconciliation is active every 5 minutes; deterministic classification is active hourly; the AI scheduler is intentionally paused and has no active cron trigger.
- OOC hardening is implemented but not yet a production-live claim: only controlled out-of-coverage locations can auto-apply OOC; selective, mixed and unknown locations remain review-required.
- Independent encrypted backup/isolated restore and AWS least-privilege IAM rotation remain external infrastructure prerequisites; neither is marked complete without independent evidence.

Historical documents retain dated evidence. Current-state claims in CRM documentation must point to the latest verified release candidate or a later production audit; older counts must not be copied into current-status sections.
## AI scheduler — intentionally paused

- `crm_ai_scheduler_6h` is **paused** as of 2026-10-04.
- Its implementation and `crm_invoke_ai_scheduler()` function remain in the repository and database.
- The pg_cron trigger has been removed, so no recurring AI scheduler execution is currently scheduled.
- The deterministic classification scheduler remains active independently at `0 * * * *`.
- Reactivation requires an explicit operational decision and a new scheduler activation.
