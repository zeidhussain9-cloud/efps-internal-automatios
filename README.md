# EFPS Internal Automations

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
- **Tests:** `npm run build` PASS; `npm test` 76/76 PASS; `npm run test:browser` 1/1 PASS.
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



Internal automation repository for EasyFind Property Solutions (EFPS).

The repository follows one simple operating model:

> **Root = how the AI/repository operates.**
>
> **`docs/` = what the business/system is.**
>
> **`modules/` = business capabilities.**
>
> **`shared/` = reusable technical capabilities.**

## Mandatory AI operating protocol

- `CORE_STEERING.md` — mandatory core AI operating protocol applied by every AI agent before every response or action.
- `GEMINI.md` — Gemini-specific operating adapter.
- `AGENTS.md` — general AI-agent operating rules and enforcement of core steering.
- `HANDOFF.md` — current working state between development sessions.

## Repository structure

- `docs/` — single canonical home for EFPS business and system knowledge.
- `modules/` — business capabilities and business decisions.
- `shared/` — reusable technical integrations and capabilities.
- `.gemini/skills/` — repeatable AI session procedures.

## Mandatory documentation rule

For every implementation, the agent must review all maintained root and `docs/` documentation and update every document whose content is affected by the resulting repository reality. Do not create duplicate authoritative documents.

## CRM production checkpoint — 2026-10-01

- Canonical CRM UI branch: `crm-ui-dashboard`; Render service: `easyfind-crm-d01-d05` (`srv-darsv560tbcc73cu4ip0`).
- Current live commit: 1c196577fc414be52c8fc889b3886f11e0e9da5d; deploy: dep-dav82h3m8hqs7399j4ug.
- Production source: `+919148338801`; `+917975102130` and `+919902024973` remain UI-visible but inactive.
- Supabase current state: 186 leads, 310 classifications, 23 pending, 186 promoted, 6,870 messages, 465 webhook events.
- Webhook audit: 46/46 processed, 0 received, 0 failed.
- Contact Classification now has three queues: Not pushed to CRM, Qualified lead pushed to CRM, and Unqualified leads. Not pushed includes pending + explicitly unqualified; Unqualified is the explicit excluded subset.
- RLS is enabled on all CRM tables; anon/authenticated have no SELECT privilege. Render reports Basic Auth configured and database connectivity connected.
- Browser Realtime is notification-only; the server webhook/database path is independent.

## Current modules
## Current modules

## Current modules

- `modules/efps-inventory-mgmnt/` — property inventory business workflows and rules; current Inventory Phase-1 implementation.
- `modules/efpd-lead-mgmnt/` — lead/enquiry business workflows and rules.
- `modules/efps_meta_catalogue_mgmnt/` — Meta/WhatsApp Business catalogue creation and publishing workflows.
- `modules/efps-housing-portal-mgmnt/` — reserved future Housing.com automation.
- `modules/efps-website-mgmnt/` — EasyFind website management and automation.

## Established shared capabilities

- `shared/cloudinary/` — reusable Cloudinary media storage/upload capability with deterministic property/lead namespaces and secure URL helpers.
- `shared/credentials/` — canonical local macOS Keychain credential provider.
- `shared/google_maps/` — reusable Google Maps URL extraction plus later runtime Geocoding resolution.
- `shared/google_sheets/` — reusable Google Sheets technical access plus the canonical 48-column `Housing_Listings` A:AV contract; live read/write boundary verified for Inventory Phase 1.
- `shared/slack/` — reusable Slack operational capability for the authorized Inventory Phase-1 workflows.
- `shared/whatsapp_whapi/` — reusable WhAPI technical transport, live gate, channel/settings primitives, webhook normalization, and neutral messaging primitives.

## Inventory Phase-1 processing model

Inventory uses three top-level stages:

1. **Stage 1 — Initial / Webhook**: legacy inventory source handling, `NEW` property-session boundary, raw capture, and initial row.
2. **Phase-1 deterministic boundary**: canonical source segmentation, deterministic candidate extraction/resolution, normalization/dependencies, deterministic Google Maps URL extraction, and deterministic validation. This boundary is implemented by `src.phase1.run_phase1()` and is AI-independent and network-free for Maps.
3. **Later property verification / downstream processing**: runtime Google Maps resolution, optional AI verification, wording-only AI beautification, media handling, and downstream publishing. These do not provide source evidence to the deterministic boundary.

The deterministic source contract is: `raw_message_text` is authoritative; persisted Stage-2 Sheet values are never extraction input. Internal property type is restricted to `Gated Community`, `Semi Gated`, or `Standalone`; direct source evidence wins and missing/invalid evidence remains unresolved. Society/community names are not used as property-type evidence.

Property type drives the coupled parking/amenities resolution: covered parking defaults to `1` for Gated Community/Semi Gated when absent, explicit counts are preserved, open parking defaults to `-`, and society amenities use exact live Sheet dropdown combinations.

`landmark` falls back to `locality` when no better source value exists. `society_name` falls back to locality only as a last resort and is review-flagged. `pincode` and property age are non-blocking optional fields; image URLs are a separate media flow.

## Deterministic audit status — 2026-09-15

The hardened Phase-1 contract remains a 48-field canonical `Housing_Listings` schema with deterministic fields owned by the panel and downstream fields protected. `catalog_title` and `property_highlights` remain valid deterministic fields but may be wording-only AI beautification outputs after the Phase-1 boundary.

The deterministic repository work is complete for the current Phase-1 Inventory Management scope. The remaining items are live/external runtime verification dependencies documented separately in `docs/OPEN_POINTERS.md`; they are not unresolved deterministic field-contract defects.

## Live-system migration reconciliation — 2026-09-16

The CRM UI branch now uses a lead-only live WhatsApp path. WhAPI messages for the connected CRM source `+919148338801` enter the Supabase Edge Function and are written directly to CRM leads/messages. The legacy inventory runtime remains isolated from this CRM webhook and is not a CRM routing destination.

`modules/efps-inventory-mgmnt/src/inventory_runtime.py` is the only migrated Inventory runtime adapter: it captures the live Stage-1 session boundary, durable session state, deduplication, and raw intake, then delegates closed sessions to the existing canonical Inventory pipeline. `handler.py` provides the scheduled Raw-row worker using the same canonical package.

Legacy Inventory extraction, normalization, deterministic business rules, field resolution, property processing, validation/business logic, and Stage-2 implementation are explicitly excluded from the migration.

## Private CRM workstream

The private EasyFind CRM is now running as a production UI from `crm-ui-dashboard`. Canonical CRM documentation lives under `docs/crm/`.

Current production status:
- D01–D05 approved for the current UI baseline.
- Render `easyfind-crm-d01-d05` deploys `crm-ui-dashboard`.
- Historical and live WhatsApp data for `+919148338801` reconcile through Supabase.
- The other configured source numbers remain visible for later onboarding.

The CRM reconciliation documents distinguish historical WhatsApp/SQLite evidence from the current Supabase operational store. The production source boundary for this deployment is explicitly +919148338801.

## Production status

The current CRM UI deployment is live. WhAPI events for +919148338801 are recorded in crm_webhook_events before downstream reconciliation; historical and live records use the same source-aware CRM path. Render health and deployment state are independently verified.

## CRM UI branch and dedicated model steering

**Current CRM UI branch: `crm-ui-dashboard`.** Render service `easyfind-crm-d01-d05` deploys this branch. The hosted CRM Ollama adapter reads compact root `steering.md` as its dedicated system instruction; it is separate from `CORE_STEERING.md`. Current production CRM data is real and source-scoped to WhatsApp `+919148338801`; the other configured source numbers remain visible for later onboarding. See `docs/crm/LEAD_CRM_MASTER_PLAN.md`.

## CRM daily operating flow — 2026-09-30

- Contact Classification is a single qualification queue with two sub-tabs: Not pushed to CRM, and Qualified leads pushed to CRM.
- There is no separate classification filter. Each contact has one classification dropdown and an explicit Update action.
- Selecting a non-qualified classification saves the classification and keeps the contact in Not pushed to CRM.
- Selecting Qualified Lead and clicking Update performs the audited Supabase promotion transaction; only after success does the contact move to Qualified leads pushed to CRM and appear in Leads Inbox with preserved messages linked.
- The Dashboard is intentionally action-oriented: CRM leads, contacts not pushed, qualified contacts pushed, and follow-ups due today, followed by the next open follow-ups.
- Classification writes are explicitly gated by CRM_CLASSIFICATION_WRITE_ENABLED=true, protected CRM access, DATABASE_URL, and the server-side repository transaction.
