## 2026-10-02 — Replit feedback branch recovery and line-by-line audit checkpoint

The isolated branch `crm-ui-feedback-polish-2026-10-02` was recovered after the Replit workspace exhausted its credits. The branch is based directly on production checkpoint `97b43a7d158eb8b3cd773ed3febb45c4f8a52540` and contains the recovered UI/inventory implementation plus regression coverage.

### Audited implementation extracted for verification

- Lead cards now expose persisted `crm_leads.classification` separately from operational `crm_leads.lead_type`; missing classification is rendered as `Not recorded` and is not inferred from age, message history, budget, or AI output.
- Lead cards expose a persisted overdue-follow-up count derived from incomplete follow-ups whose due time has passed. No financial-risk label is inferred from budget.
- Lead status tones are secondary, low-contrast semantic styling and remain text-labelled; color is not the only meaning.
- Lead-card classification spacing and mobile hierarchy were hardened with explicit identity-to-classification separation and narrow-screen overflow coverage.
- Inventory KPI cards remain clickable and use full-inventory summaries/facets rather than page counts.
- Inventory search, status/BHK/locality/photo filters, sorting, and 24-row pagination now compose through the protected inventory overview response. Filter/sort changes reset to page zero; the browser ignores stale inventory/audit responses.
- Inventory pagination has explicit query validation and deterministic filter/sort/page regression coverage.
- Global and lead Activity requests use cancellation guards so stale responses cannot overwrite current state.
- Contact Classification filter/source changes reset pagination without issuing a stale page response.
- Browser regression coverage now exercises inventory page 2, filter reset, classification visibility, overdue attention, mobile classification spacing, and horizontal-overflow safety.

### Audit exclusions / corrections

- Replit-only `.replit` and startup-instruction asset were removed from the promotion candidate.
- Replit-mutated dependency ranges and package-firewall lockfile URLs were removed; the production `package.json` and `package-lock.json` were restored to the verified `97b43a7` baseline.
- No production database write, webhook/integration change, schema migration, or Render deployment is included in this checkpoint.

### Verification state

Implementation review is complete at the repository diff level. Build, full automated tests, browser regression, production deployment, and branch reconciliation remain evidence-gated until the recovered candidate is executed and verified. This section must not be interpreted as a production-live claim.

# EFPS CRM — Current Verified State

## Unreleased feedback branch update — production unchanged

The isolated branch `crm-ui-feedback-polish-2026-10-02` separates each lead’s stored classification from lead status, shows overdue attention only for a persisted overdue open follow-up, and adds read-only server-side inventory filtering, sorting, and pagination. No merge, deployment, production-data mutation, integration change, or schema change is part of this work. Local verification results for the branch will be recorded after the requested checks.

## Authoritative full-audit override — 2026-10-01

The authoritative current live-data baseline is 186 leads, 6,870 messages, 465 webhook events, 310 classifications, 196 AI runs, 196 drafts, 186 AI cursors, and 88 active inventory rows. 52 leads now have reconciled WhatsApp sender names persisted as display names, with 52 reconciliation activity records. All 196 AI runs and 310 classification records have corresponding activity-history entries; 192/196 AI runs contain recorded input/output token usage and the remaining 4 accurately display as not recorded. Build, 78/78 tests, browser 1/1, Cloudinary 829/829, deployment, and branch reconciliation are verified.

## Authoritative current verified state — 2026-10-01 21:55 IST

This is the latest repository/production checkpoint. Older dated sections in maintained documents are historical evidence and must not be interpreted as current state.

- **CRM deployment branch:** `crm-ui-dashboard`
- **CRM commit:** `1c196577fc414be52c8fc889b3886f11e0e9da5d`
- **CRM tree:** `908b635b2b7b04bdf3515934de2769393e282c34`
- **main:** `b2fbf366021852aedd4bf0ec66484ad421fb5662`
- **main tree:** `908b635b2b7b04bdf3515934de2769393e282c34`
- **Tree equality:** `tree(main) == tree(crm-ui-dashboard)` = **TRUE**
- **Render:** `easyfind-crm-d01-d05` / `srv-darsv560tbcc73cu4ip0`
- **Live Render deployment:** `dep-dav82h3m8hqs7399j4ug` = **LIVE**
- **Live Render commit:** `1c196577fc414be52c8fc889b3886f11e0e9da5d`
- **Production health:** `GET /health` = HTTP 200, `{"ok":true}`
- **Production WhatsApp source:** `+919148338801`
- **Supabase:** 186 leads; 6,870 messages; 465 webhook events; 310 classifications; 186 requirements; 196 AI runs; 196 drafts; 186 AI cursors; 88 active inventory rows.
- **Classification status:** 186 promoted; 88 classified; 23 pending; 13 excluded = 310 total.
- **Webhook status:** 465 processed; 0 received; 0 processing; 0 failed.
- **Message reconciliation:** 6,870 total = 4,806 lead-linked + 2,064 classified non-lead; unreconciled = 0.
- **Historical classification population:** 228 historical records; 140 qualified mappings.
- **Inventory:** 88 active rows = 71 Available + 17 Rented Out; 1,377 sync runs; latest sync recorded 88 rows / 0 changed / 0 removed; inventory-change rows = 0.
- **Cloudinary:** 829/829 distinct production URLs returned HTTP 200 with `image/*` content-type by direct HEAD checks from the production-machine network path.
- **AI integrity:** draft→AI-run lead mismatch = 0; stale evidence references = 0; invalid cursor lead links = 0.
- **Tests:** `npm run build` PASS; `npm test` 78/78 PASS; `npm run test:browser` 1/1 PASS.
- **Supabase Edge Function:** `whapi-crm-webhook` ACTIVE v8.
- **AWS legacy webhook:** no changes in the audited CRM hardening range.
- **24-item CRM audit:** GREEN / VERIFIED.

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
