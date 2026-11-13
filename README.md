## Current inventory intake deployment — 2026-11-13

- Isolated AWS stack `efps-notion-property-intake`: `UPDATE_COMPLETE` in `ap-southeast-2`.
- Lambda `efps-notion-intake`: Active; endpoint `https://ko3771nvei.execute-api.ap-southeast-2.amazonaws.com/Prod/notion/intake`.
- Invalid Notion handshake/event signatures: HTTP 401; validly signed malformed event: HTTP 400 at page-ID validation. Notion API read-only access to both databases: HTTP 200.
- End-to-end Notion intake remains blocked: deployed Google Sheets credential resolves to `{}`; Cloudinary and Maps runtime values resolve to `MIGRATION_PLACEHOLDER`. No Sheet/Cloudinary write is verified; Notion subscription and controlled acceptance remain pending.
- Inventory module tests: 118/118; combined inventory/webhook-routing tests: 130/130; CRM npm test: 139/139; browser regression: 1/1; Vite build: PASS; isolated SAM build and template validation pass.
- Existing inventory intake routes include the Slack operator-assisted /efps add-property and /efps photos start flows, plus the WhAPI listener from its two dedicated source numbers and NEW session boundary. The deployed WhAPI Lambda was last updated 2026-10-04 and was not redeployed here. The repository handler now uses the explicit sender allowlist and dispatch regression tests. The existing WhAPI/CRM stack was not modified.

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
