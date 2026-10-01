# EFPS CRM — Current Verified State

## Authoritative full-audit override — 2026-10-01

See `docs/audits/CRM_FULL_AUDIT_2026-10-01.md`. The currently verified live-data baseline is 186 leads, 6,859 messages, 454 webhook events, 309 classifications (228 historical), 196 AI runs, 196 drafts, 186 AI cursors, and 88 active inventory rows. The prior commit/tree/deployment values in this file are retained as historical checkpoints. The new hardening release is locally verified with build PASS, 76/76 tests PASS, and 1/1 browser regression PASS. Cloudinary is still an open media gate: 829 distinct URLs yielded 719 valid images, 110 timeouts, and 1 JSON response.

## Current verified repository state — 2026-10-01

This section is the current checkpoint for maintained documentation. Dated audit sections below remain historical evidence and are not silently rewritten.

- **Canonical UI/deployment branch:** `crm-ui-dashboard`
- **`crm-ui-dashboard` commit:** `da13083f6cb1f3c78ec3f4df661c515d43f556fa`
- **`crm-ui-dashboard` tree:** `f36a5ccb4bae742e83603b09bee59d01595ecf00`
- **`main` reconciliation commit:** `692bdcbbab51752b8eb7d4927921d1cfc4830de7`
- **`main` tree:** `f36a5ccb4bae742e83603b09bee59d01595ecf00`
- **Tree equality:** `tree(main) == tree(crm-ui-dashboard)` = **TRUE**; commit histories differ by design.
- **Render:** `easyfind-crm-d01-d05` / `srv-darsv560tbcc73cu4ip0`, deployment `dep-dav55km0tbcc73eelat0`, **live**.
- **Production source:** `+919148338801`.
- **Supabase CRM:** 186 leads; 309 classifications; 20 pending; 186 promoted; 6,853 messages; 436 webhook events, 436 processed, 0 received, 0 processing, 0 failed.
- **AI persistence:** 196 AI runs, 196 proposed; 196 drafts; 186 AI cursors.
- **Inventory:** 88 active Housing rows; 1,333 sync-run records; latest recorded sync = 88 rows / 0 changed / 0 removed; AU/AV remain outside the CRM operational A:AT mirror.
- **Schedulers:** `crm_webhook_reconcile_1m` active every minute; `crm_inventory_sheet_reconcile_5m` active every five minutes.
- **P1–P5:** implemented and production-verified as documented in `docs/audits/PRODUCTION_LIVE_WEBHOOK_AND_INVENTORY_AUDIT_2026-10-01.md`.
- **Verification:** `npm run build` PASS; `npm test` PASS (71/71); `npm run test:browser` PASS (1/1).
- **GitHub:** active remote UI branch search returns only `crm-ui-dashboard`; historical UI/inventory branches with deleted remotes are retained only as local historical evidence and are not active deployment branches.

### Current operational flow

```text
WhAPI +919148338801
  -> crm_webhook_events (persist + deduplicate)
  -> webhook processor/reconciler
  -> crm_messages + classification registry
  -> operator classification update
       -> non-qualified: remains outside CRM leads
       -> Qualified Lead: audited promotion transaction
            -> crm_leads + preserved messages
            -> webhook event lead linkage reconciled

CRM lead workspace
  -> complete chronological conversation + normalized requirements + evidence + notes + prior AI runs + cursor
  -> Bedrock primary / Sonnet fallback / Ollama fallback
  -> persisted crm_ai_runs + crm_drafts + provenance
  -> operator review/edit/pre-send grounding
  -> manual WhatsApp action only; no automatic send

Housing_Listings A:AV
  -> CRM reads operational A:AT only
  -> 88-row operational mirror in crm_inventory_snapshot
  -> five-minute reconciliation
  -> crm_inventory_sync_changes records future field-level changes
```

### Test-history checkpoint

The P1–P5 hardening release added regression coverage for webhook promotion linkage, reserved AU/AV exclusion, and disposable inventory create/edit/delete history. The final repository verification was 71/71 automated tests, browser 1/1, and production build PASS. Historical earlier test counts in dated handoff/audit sections are retained as historical checkpoints.

## Evidence sources

- Repository implementation and tests on `crm-ui-dashboard`.
- Supabase production database `easyfind-crm` (`qttcutwzehtskfcwxkwj`).
- Render production deployment for `easyfind-crm-d01-d05`.
- GitHub branch/ref and tree comparison.
- Historical audit: `docs/audits/PRODUCTION_LIVE_WEBHOOK_AND_INVENTORY_AUDIT_2026-10-01.md`.

## Change history since the prior 2026-10-01 audit

1. P1 historical webhook event lead linkage was implemented in the promotion transaction and existing eligible rows were backfilled.
2. P2 AU/AV were made an explicit CRM boundary: A:AT is operational; AU/AV remain Sheet-owned metadata outside the mirror.
3. P3 `crm_inventory_sync_changes` was added for future field-level inventory audit history.
4. P4 the one-minute webhook reconciler was hardened for message-backed `received`/`processing` states.
5. P5 disposable inventory create/edit/delete regression coverage was added without mutating the production Sheet.
6. The production Render deployment now runs the verified hardening commit.
7. `main` was reconciled to the same repository tree without rewriting history.

## Documentation rule

This file is the canonical current operational checkpoint. Historical audit reports remain immutable evidence. When a new verified production checkpoint is established, update this file and the maintained canonical summaries in the same work session.
