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

## Current production audit — 2026-10-01 (post-reconciliation)

See the authoritative current-state block at the top of this document for the verified Render/Supabase checkpoint.

# CRM Two-Layer Classification and Webhook Gate

## Unreleased lead-card display contract

On `crm-ui-feedback-polish-2026-10-02`, a promoted CRM lead may display its persisted `crm_leads.classification` value, separately from the operational `crm_leads.lead_type` status. A missing classification is shown as “Not recorded”; the UI does not infer or rewrite a classification.

The Contact Classification queue remains the source of operator decisions. “Cold Inquiry” is shown only when present in stored classification data; lead age, message age, budget, and AI output do not create cold-lead or financial-risk labels. An overdue attention cue is derived only from an incomplete stored follow-up whose due time has passed. These are display-only changes and do not alter the promotion transaction or classification registry.

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



## Current production behavior — 2026-09-30

The Contact Classification screen is intentionally simple: one queue with two tabs.

- **Waiting for classification:** pending and non-qualified contacts.
- **Qualified lead pushed to CRM:** contacts successfully promoted into Lead CRM.

The operator selects one classification and clicks **Update**. A non-qualified choice saves as excluded and remains outside Lead CRM. A **Qualified Lead** choice executes the transactional promotion path and moves the contact only after the database confirms success. Each row includes a direct **Open WhatsApp** link.

The 2026-09-30 production failure was PostgreSQL `42P18` in the new-lead insert. The cause was an untyped `$5` parameter inside `jsonb_build_object()`; the consolidated fix explicitly casts `$5::text`. The operator retry succeeded after deployment.

## Canonical flow

1. WhAPI callback arrives for the connected source `+919148338801`.
2. The Supabase Edge Function authenticates the callback and persists the callback in `crm_webhook_events`.
3. The webhook event is not rejected because the contact is unknown or non-qualified.
4. Message events with a resolvable phone are reconciled into `crm_contact_classifications`.
5. Contact classification is Layer 1: Qualified Lead; Personal / Family; Agent / Partner; Business; Promotion / Marketing; Vendor / Supplier; Internal; Cold Inquiry; Property Listing Sent; Unknown / Pending.
6. Only Qualified Lead is eligible to create/promote a `crm_leads` record.
7. `crm_leads.lead_type` is Layer 2 and describes the operational state of an already-qualified lead.
8. Qualified live messages are appended to `crm_messages` using provider message identity and original message timestamp.
9. Non-qualified contacts remain in the classification/event layers; their events are not promoted into CRM.
10. If a non-qualified contact is later classified as Qualified Lead, the promotion path creates the lead and backfills preserved message events.

## Credential boundary

The WhAPI channel API token is a provider credential. It is not a semantic classifier and is not required by the inbound webhook receiver. The inbound receiver uses a separate webhook authentication secret. Production secret material must not be committed to GitHub or placed in the Render browser/API environment unnecessarily.

## Historical data rule

The historical SQLite archive remains source evidence. It must not be reclassified from aggregate statistics. Current production Supabase records carry their own source and webhook provenance.

## No intake queue

`crm_intake_contacts` / `crm_intake_messages` are not part of this architecture. The classification registry replaces the intake queue.

## Inventory

Inventory sender/source routing is outside this CRM classification path and remains unchanged.
