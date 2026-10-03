# CRM UI branch reconciliation — current verified state

> Verified 2026-10-03 20:26 IST. Historical recovery/reconciliation sections below are retained as historical evidence and superseded.

- Intended branches for this workstream: main and crm-ui-dashboard.
- Render deploy branch: crm-ui-dashboard.
- Contact Classification includes the first-class Group Message / group_message Unqualified category.
- Pending WhatsApp group traffic is automatically routed to Group Message using persisted webhook chat_id suffix evidence (@g.us).
- Current source snapshot: 228 leads; 7,746 messages; 1,471 webhook events; 277 AI runs; 214 drafts; 354 classifications; 88 active inventory listings.
- Classification status: 228 promoted / 88 classified / 27 excluded / 11 pending.

## Current release evidence

The release record reports the crm-ui-dashboard commit SHA, tree SHA, CI result, Render deployment ID, Supabase Edge Function version, Supabase migration version, and final equality of main and crm-ui-dashboard trees.

## Historical evidence

### 2026-10-02 — Replit feedback branch recovery and line-by-line audit checkpoint

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

# CRM UI branch reconciliation

## Unreleased feedback branch — not reconciled or deployed

Work is isolated on `crm-ui-feedback-polish-2026-10-02`. The production reconciliation details below remain unchanged and do not include this branch. This work adds only CRM UI/read-only overview behavior and regression coverage; no merge, deployment, production-data write, integration change, or schema migration has been performed. Record the branch’s local verification separately from the production verification below.

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



**Canonical UI branch:** `crm-ui-dashboard`
**Reference branch:** `main` (reconciled repository branch; not the Render deployment branch)
**Checkpoint:** 2026-10-01 — commit `da13083f6cb1f3c78ec3f4df661c515d43f556fa`, tree `f36a5ccb4bae742e83603b09bee59d01595ecf00`
**`main` checkpoint:** `692bdcbbab51752b8eb7d4927921d1cfc4830de7`, tree `f36a5ccb4bae742e83603b09bee59d01595ecf00`

## Current contract

- GitHub contains only the intended `crm-ui-dashboard` and `main` branches for the UI workstream.
- The UI source selector exposes all three audited EFPS WhatsApp source numbers: `+919148338801`, `+917975102130`, `+919902024973`. The connected live WhAPI ingress remains `+919148338801`.
- Current production evidence is 186 leads, 310 classifications, 23 pending classifications, 186 promoted classifications, and 6,870 CRM messages for +919148338801.
- Historical message provenance remains source-backed; SQLite message IDs are stored as `source_message_id`, not fabricated provider IDs.
- The live CRM path is lead-only. There is no listener abstraction, no inventory listener, no lead listener or staged intake queue. `crm_contact_classifications` is the pre-lead registry and operator qualification gate.
- WhAPI pushes `messages` webhooks to the Supabase Edge Function `whapi-crm-webhook`.
- `crm_webhook_events` records the webhook activity before lead/message processing.
- Existing promoted source-phone leads receive appended messages; unseen source-phone contacts remain classifications/messages until an operator selects Qualified Lead.
- `crm_messages` is rendered chronologically by provider `message_at`.
- Supabase Realtime signals the UI after message insertion; the browser does not poll WhAPI or poll the CRM workspace.
- The CRM never sends WhatsApp messages automatically.
- Render remains the authenticated UI/API host. Supabase is the live webhook ingress and CRM database. No AWS runtime is used for the CRM webhook.

## Data gates completed

The current production CRM registry contains 186 leads and 310 classifications, with 23 pending classifications and 186 promoted. Current CRM messages total 6,870 for the production source. No separate intake queue is used.

## Live webhook gate

Current persisted counts are 186 leads, 310 classifications, 6,870 messages and 465 webhook events (465 processed, 0 received, 0 processing, 0 failed).

The WhAPI-to-Supabase live ingress is enabled for the current production source. Do not run another historical WhAPI API extraction as part of ordinary CRM reconciliation. Historical SQLite evidence and live webhook data remain distinct provenance classes.

## Canonical technical document

See `docs/crm/CRM_LIVE_WHAPI_WEBHOOK.md` for the complete live architecture, event table, lead association rules, ordering, Realtime behavior and security boundary.


## Classification write fix — 2026-09-30

A single operator test on contact `+919216063368` produced the definitive Render diagnostic: PostgreSQL `42P18`, `could not determine data type of parameter $5`, at the `insert lead` stage. The failing parameter was the source number passed into `jsonb_build_object()` during new-lead creation. The consolidated fix explicitly casts that parameter to `text`. Local build and the full 62-test suite passed before deployment. Render deployment `dep-daum4rtg1s2s73cntsv0` is live from commit `45dbab7b1ba92387e5e001f74929ad40c92be6a9`. The subsequent operator retry succeeded.

## 2026-10-02 — Final recovered-candidate audit record

- Candidate branch: `crm-ui-feedback-polish-2026-10-02`
- Candidate HEAD: `1241b062dfbc7a96b139ec0a7f68d68f43baab51e`
- Production/dashboard baseline: `97b43a7d158eb8b3cd773ed3febb45c4f8a52540`
- Pull request: #60 — CRM UI feedback polish
- Replit-only workspace artifacts removed before promotion.
- Production dependency manifest and lockfile restored to the verified baseline.
- Recovered implementation includes classification visibility/tone, overdue follow-up attention, inventory filtering/sorting/pagination, stale-response guards, classification pagination reset, and browser/server regression coverage.
- No production merge, Render deployment, database mutation, schema migration, or webhook/integration change has been performed from this candidate.
- Automated build/test evidence for this exact candidate is still pending; do not mark the candidate production-verified until `npm run build`, `npm test`, and `npm run test:browser` are observed passing.
- `main` and `crm-ui-dashboard` remain unchanged from the verified production baseline until that evidence gate is satisfied.


## 2026-10-02 synchronized state

The recovered CRM UI feedback work is now on `crm-ui-dashboard`. The `main` branch has been reconciled to the same repository tree without rewriting main history. Replit-only workspace artifacts were excluded and the production dependency manifest was restored. Render deploys from `crm-ui-dashboard`; repository reconciliation is verified, while live runtime status must be confirmed from Render.
