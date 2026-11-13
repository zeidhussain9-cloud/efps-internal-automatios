## Current inventory intake deployment — 2026-11-13 (updated after signed-in live checks)

- AWS stack `efps-notion-property-intake` is `UPDATE_COMPLETE`; Lambda `efps-notion-intake` is Active in `ap-southeast-2`. Notion Housing Listings is the canonical editor; Supabase `notion-inventory-state` is ACTIVE v6. The verified webhook and all eight Page event selections were left unchanged.
- A signed-in live test confirmed a Notion edit reached the Supabase projection and rendered in the production CRM dashboard. A real Notion delete reached the projection after an observed delay of about one minute and soft-deleted the row. A duplicate handler replay returned `already_processed` in the earlier controlled check.
- **Restore is not verified end to end and currently failed in the live test:** restoring the page in Notion did not produce a new Lambda invocation or Supabase Edge Function request, and the projection remained soft-deleted. The restore handler passed a direct worker check, but webhook delivery did not.
- The test page `EFPS TEST ONLY - DO NOT CONTACT - 20261113-101056Z` was permanently deleted from Notion Trash after user approval. Its exact test projection and intake-event rows were deleted. Supabase returned to 104 active Notion rows (87 Available, 17 Rented Out); the dashboard returned to 104. No test record remained in the checked Supabase tables or Notion Trash.
- Signed-in inventory behavior was verified on code-bearing release `61688164b25f7a7a8e6df8248f91987a9c471ef6`. The later documentation-only follow-up was published on `crm-ui-dashboard`, reconciled into `main`, auto-deployed by Render, and passed GitHub's production health smoke. The branches have identical tracked trees; see GitHub and Render for current refs and deployment IDs. The signed-in inventory page showed 104 listings (87 Available, 17 Rented Out) and the Notion/Supabase source labels.
- The existing AWS secret ARNs were reused; no secret values were displayed or changed. The Sheet reconciliation cron is removed, but compatibility Sheet writes remain. The old WhAPI `NEW` listener remains until final cleanup.

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
