# EFPS Internal Automations — Architecture

## Authoritative current verified state — 2026-10-04 00:49 IST

This is the latest repository/production checkpoint. Older dated sections in maintained documents are historical evidence and must not be interpreted as current state.

- **CRM deployment branch:** `crm-ui-dashboard`
- **Verified deterministic implementation baseline:** `8996dd32d732b0d8fab17f41b42306c230cd1de1`
- **CRM tree:** `c16bafdf7ed4e369d3171a4ee58f80a919630f10`
- **main:** reconciled release branch
- **main tree:** verified equal to crm-ui-dashboard at release close
- **Tree equality:** `tree(main) == tree(crm-ui-dashboard)` = **TRUE**
- **Render:** `easyfind-crm-d01-d05` / `srv-darsv560tbcc73cu4ip0`
- **Live Render deployment:** current crm-ui-dashboard release = **LIVE**
- **Live Render:** current crm-ui-dashboard release verified LIVE
- **Production health:** `GET /health` = HTTP 200, `{"ok":true}`
- **Production WhatsApp source:** `+919148338801`
- **Supabase:** 239 leads; 8,098 messages; 1,831 webhook events; 362 classifications; 186 requirements; 277 AI runs; 214 drafts; 190 AI cursors; 88 active inventory rows.
- **Classification status:** 239 promoted; 88 classified; 32 excluded; 3 pending = 362 total.
- **Webhook status:** 1,831 processed; 0 received; 0 processing; 0 failed.
- **Message reconciliation:** 8,098 total = 6,047 lead-linked + 2,051 classified non-lead; unreconciled = 0.
- **Historical classification population:** 228 historical records; 140 qualified mappings.
- **Inventory:** 88 active rows = 71 Available + 17 Rented Out; 1,377 sync runs; latest sync recorded 88 rows / 0 changed / 0 removed; inventory-change rows = 0.
- **Cloudinary:** 829/829 distinct production URLs returned HTTP 200 with `image/*` content-type by direct HEAD checks from the production-machine network path.
- **AI integrity:** draft→AI-run lead mismatch = 0; stale evidence references = 0; invalid cursor lead links = 0.
- **Tests:** `npm run build` PASS; `npm test` 120/120 PASS; `npm run test:browser` 1/1 PASS.
- **Supabase Edge Function:** `whapi-crm-webhook` ACTIVE v9.
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

The P1–P5 hardening release added regression coverage for webhook promotion linkage, reserved AU/AV exclusion, and disposable inventory create/edit/delete history. The final repository verification was 78/78 automated tests, browser 1/1, and production build PASS. Historical earlier test counts in dated handoff/audit sections are retained as historical checkpoints.



This is the canonical cross-repository architecture reference.

## Core model
- `shared/` — reusable technical capabilities and integrations.
- `modules/` — EFPS business capabilities and business decisions.

> Shared services provide capabilities; modules decide when and why they are used.

## Shared capabilities
- `shared/cloudinary/` — reusable media storage/upload capability.
- `shared/google_sheets/` — Sheets transport and the canonical 48-column `Housing_Listings` contract.
- `shared/google_maps/` — reusable Maps URL extraction and Google Geocoding resolution capability; inventory decides when it is required.
- `shared/whatsapp_whapi/` — WhAPI transport, webhook normalization/verification, and the two-listener source boundary.
- `shared/slack/` — reusable Slack transport, security, routing, and authorized Inventory Phase-1 operational capability.
- `shared/credentials/` — local macOS Keychain credential provider used by shared adapters.

## Inventory top-level stages

### Stage 1 — Initial / Webhook
Dedicated inventory-listener traffic enters the inventory module. `NEW` opens a property session; subsequent messages are collected until the next `NEW`, which closes the property. A listing identity is created and the raw record is persisted.

**Row insertion:** New properties insert at row 2 (immediately after the header), pushing existing rows down. This keeps the most recent listings at the top of the sheet.

**Image caption extraction:** Media messages (images, videos, documents) with text captions have their caption text extracted and stored in the session. Forwarded property listings sent as images with text descriptions are fully captured.

### Stage 2 — Deterministic Extraction / Property Processing
The completed raw property is processed as one business stage with the following deterministic boundary:

```text
raw_message_text
  -> canonical source segmentation
  -> candidate extraction
  -> canonical field resolution
  -> deterministic normalization/business rules
  -> deterministic validation
  -> Maps enrichment/verification
  -> optional AI verification/wording-only beautification
```

The authoritative deterministic entry point is `modules/efps-inventory-mgmnt/src/pipeline.py:deterministic()`. The authoritative full Stage-2 entry point is `process_closed_session()`.

`src/source_segments.py` prevents labelled extraction from consuming a later WhatsApp message. `src/field_resolution.py` owns recurring multi-candidate resolution for BHK, maintenance, and internal property type. `normalize.py` consumes canonical resolved values and does not independently rediscover or reclassify property type.

The projection audit has established additional source-shape guards at the extraction boundary: singular/decimal balcony counts are explicit source facts; explicit no-pet wording is authoritative; `📍 Landmark:` markers do not convert Maps URLs into landmark values; deterministic Maps URLs are source-extracted without network access in the projection path.

Existing persisted Sheet Stage-2 values are never extraction input. The raw source remains authoritative for deterministic facts.

### Stage 3 — Meta Catalogue Publishing
Stage 3 implements Meta/WhatsApp Business catalogue creation and publishing. Properties flow through:

1. **Catalogue Ready gate**: After photos are uploaded (`intake_status=Processed` → automatic check → `intake_status=Catalogue Ready`)
2. **Manual catalogue creation**: Operator runs `/efps catalogue start` → `go` in thread
3. **WhAPI product creation**: System calls `POST /business/products` with property description, images, price
4. **Status update**: On success, writes `meta_catalog_id` (Product ID), `meta_catalog_status=Posted`, `intake_status=Published`

The description generator (`modules/efps_meta_catalogue_mgmnt/src/generator.py`) creates minimalistic catalogue cards:
- Title from `catalog_title` column (as-is)
- Clean bullet-list format: rent, deposit, maintenance, size, floor, tenant preferences, pet policy, availability
- Footer: society/location line + Google Maps link
- All text deterministic (no AI generation)

Stage 3 writes are restricted to columns AS:AT (`meta_catalog_id`, `meta_catalog_status`) and C (`intake_status`).

## Canonical sheet
The single physical shape is `shared/google_sheets/schema.py`: 48 columns A:AV. The schema records owner, stage, allowed values where verified, and declared dependencies.

## Deterministic business dependency graph

```text
internal_property_type -> society_amenities
internal_property_type -> covered_parking (blank-only default)
furnish_type -> flat_furnishings (blank-only default)
preferred_tenant_type -> bachelor_preference
maintenance -> maintenance_included
built_up_area -> carpet_area (blank-only fallback)
monthly_rent -> security_deposit (month-based source form)
```

`internal_property_type` has exactly three business values: `Gated Community`, `Semi Gated`, `Standalone`.

## Stage-1/2 write boundary
Inventory Stage 1/2 recurring updates write A:D and F:AO. E (`listing_state`) is protected from the recurring Stage-1/2 update; the initial Stage-1 row bootstrap currently sets it to `Available`. AP:AT are downstream-owned by Housing/Meta workflows. AU (`source_group`) and AV (`inventory_locked`) are reserved and must remain blank.

## Runtime boundary
Inventory Phase-1 runtime verification has completed successfully for the canonical Google Sheets read/write boundary and for Google Maps direct API access plus application-path consumption. WhAPI live channel identity/subscription/deployment, Cloudinary live upload, and Slack live deployment remain separate runtime acceptance items.

## Live-system migration boundary — 2026-09-16

The repository-level live migration is layered on the latest canonical `main`. Lead Management, Slack handlers, and shared WhAPI/Slack capabilities already present on `main` remain authoritative; the migration does not replace newer implementations with the stale migration branch.

The live webhook ownership is:

```text
WhAPI webhook
    -> shared.whatsapp_whapi.webhook.parse_delivery()
    -> inventory listener? ──yes──> Inventory Stage-1 runtime adapter
    -> otherwise ────────────────> Lead Management
```

`modules/efps-inventory-mgmnt/src/inventory_runtime.py` owns only the live Stage-1 integration boundary: durable session capture, message deduplication, raw intake, listing identity allocation, initial-row persistence, and handoff of a closed session to the canonical existing pipeline. It does not implement or copy legacy extraction, normalization, field resolution, validation, or Stage-2 business rules.

`handler.py` is the scheduled Raw-row adapter and calls the canonical Inventory package directly. The SAM template supplies the existing Lead resources plus the `efps-sessions` table ARN required by the Stage-1 durable session store.

No Stage-2 implementation from the legacy system is part of this architecture.

## Private CRM architecture — reconciliation baseline

The private CRM is a separate EFPS business capability and UI product layered over the existing systems. Its canonical implementation repository is `zeidhussain9-cloud/efps-internal-automatios`.

### CRM source layers

**Housing inventory**
- Current business dataset: live `Housing_Listings` worksheet in spreadsheet `1zdOLWklkWlnVECCtcH4SJj6vm6nEVjINpTT2U2UJEKc`.
- Physical contract: `shared/google_sheets/schema.py`, 48 columns A:AV.
- Live Column L currently has physical header `w`; canonical field is `google_maps_url`. Current code maps the canonical physical position, so the mismatch is a live schema/header conflict rather than evidence of a new field.

**Lead data**
- Historical source evidence: three WhatsApp backup sets and their decrypted `msgstore.db` files.
- Historical normalized dataset: legacy `leads.db`.
- Curated historical extraction spreadsheet: Leads Tracker `1GfM9lPQSukVpxCEVUlUDxFj_WYg0xQj8Inn7FA4sLVI`, containing historical `Leads`, `Conversations`, `Events`, `Extraction Log`, and `Priority Sharing` tabs. It is retained as evidence and is not part of the current CRM runtime path.
- Current CRM runtime: WhAPI live ingress → `crm_webhook_events` durable boundary → Supabase CRM tables.
- Current inventory runtime is separate: `Housing_Listings` spreadsheet `1zdOLWklkWlnVECCtcH4SJj6vm6nEVjINpTT2U2UJEKc` → inventory adapter/sync → `crm_inventory_snapshot`.
- The old Leads Tracker remains accessible to the legacy service account, but repository and Render runtime audit found no current executable reference to its spreadsheet ID.

### CRM data boundary

The future local-first CRM stores source-backed records, controlled CRM state, AI-derived state, and audit/synchronization state separately. The exact model is documented in `docs/crm/CRM_DATA_MODEL.md`.

The D01–D05 prototype uses synthetic data only. It must not read or write live customer or inventory records until a later explicit integration gate.

## Documentation authority

`docs/DATA_CONTRACTS.md` owns cross-module field semantics and dependencies. `docs/DETERMINISTIC_FIELD_RESOLUTION.md` owns candidate resolution and precedence. `docs/INVENTORY_SOURCE_EXTRACTION.md` owns source segmentation and extraction boundaries. `docs/DOCUMENT_MAP.md` owns documentation roles. `docs/MIGRATION_LIVE_SYSTEM_MAP_20260916.md` owns the approved live-system migration boundary.

## CRM hosted AI boundary — 2026-09-27

The `crm-ui-dashboard` branch deploys a separate authenticated Render CRM. `src/ollama-adapter.mjs` reads and caches dedicated root `steering.md` as its single system instruction (maximum 2 KiB), then sends only the selected fixed fictional fixture to the existing hosted Ollama `/api/chat` endpoint. The API key remains server-side in Render. The first sentence above records the historical pilot architecture. The current production provider order is AWS Bedrock Claude Opus 4.6 primary and Ollama gpt-oss:20b fallback. Production AI receives complete lead history and normalized requirements; requirement changes require operator acceptance and WhatsApp sending remains manual.

## 2026-10-01 — Production CRM AI architecture checkpoint

The CRM production AI path is now lead-context based rather than fixture based. `src/ollama-adapter.mjs` receives the complete chronological message history for the selected lead together with the normalized requirement profile, field evidence, operator notes, prior AI runs, per-lead cursor and message timing. Root `steering.md` supplies the dedicated EFPS CRM model instructions. The browser never supplies the model's system instruction or substitutes its own conversation history.

The AI output is advisory and durable: requirement proposals are accepted/rejected by an operator, accepted changes update the normalized requirement profile and evidence, and generated replies are stored as versioned drafts. WhatsApp sending remains an explicit operator action.

## 2026-10-01 — Current AI generation chain

The current production AI provider chain is Bedrock Claude Opus 4.6 (`au.anthropic.claude-opus-4-6-v1`) → Bedrock Claude Sonnet 4.6 (`au.anthropic.claude-sonnet-4-6`) → Ollama `gpt-oss:20b`. Drafts retain provider/model provenance and source-message evidence. Stale drafts are detected from newer CRM messages, and the operator must pass the deterministic pre-send grounding check before opening WhatsApp. Incremental/delta message analysis remains intentionally deferred.
