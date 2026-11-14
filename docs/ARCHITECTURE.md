# EFPS Internal Automations — Architecture

## Current verified production state — 2026-11-14 (live check)

Notion Housing Listings is the canonical operator editor. Supabase public.crm_inventory_snapshot is the CRM projection. The live projection has 106 active Notion-owned rows, 1 soft-deleted Notion-owned row, and 0 active rows with blank locality and society name.

- Branches main and crm-ui-dashboard are synchronized with identical tracked trees; GitHub advertises exactly these two branch refs.
- Render CRM service srv-darsv560tbcc73cu4ip0 is LIVE; the exact deployment ID and commit are authoritative in Render and are not duplicated here.
- Supabase: notion-inventory-state ACTIVE v12 with JWT verification enabled; migration 20261114095316_crm_inventory_business_status is registered and applied.
- AWS: efps-notion-intake is Active; LastUpdateStatus Successful, last modified 2026-11-14T09:46:50Z, Python 3.12, 512 MB, 180-second timeout. Maps API-unavailable fallback is deployed.
- Two current Property Intake submissions are processed: EF-2611-PAGH (VRR Fortuna) and EF-2611-Y5KC (Shobha Royal Pavilion). Both have Raw Property Data, Photos, Processed Property relations, matching Housing Listings pages and matching active Supabase snapshots.
- Supabase inventory: 106 active rows, 1 soft-deleted row; latest sync 2026-11-14 08:44:18 UTC. The empty deleted row remains only as a tombstone, not an active listing.
- Notion webhook ledger: 26 observed event rows: 5 processed, 18 ignored non-intake changes, 2 needs-review outcomes, 1 rejected unauthenticated probe. Complete delivery capture is not certified.
- Notion history remains in crm_inventory_intake_events; WhatsApp history remains in crm_webhook_events. No tables were deleted.
- Processing-note limitation: current Processing Notes is a replaceable summary, not append-only. The two current submissions contain the full initial-failure/manual-fallback narrative, but worker/RPC reprocessing replaces the field. The event ledger separately retains status/error history. Do not promise automatic preservation of every narrative until append-only note history is implemented.
- Existing-property edits happen in Housing Listings and sync through page events; Submit New Property is for new intake. Direct update flow: Notion page edit → signed page event → Lambda → notion-inventory-state → existing Supabase snapshot → CRM dashboard.

# EFPS Internal Automations — Architecture

## Historical pre-deployment implementation note (superseded 2026-11-14)

The repository now contains a local-only Task 3 extension to the existing `crm_inventory_intake_events` ledger, with lifecycle hooks in the existing Notion Edge Function/Lambda path. It does not create a new event table or change `crm_webhook_events` / WhatsApp processing. The migration and function/Lambda code have not been applied or deployed to production; the production architecture therefore remains as recorded in the verified state below until deployment is separately authorized.

## Historical verified state — 2026-11-13 (superseded by 2026-11-14 state above)

This section supersedes older dated operational snapshots below. Historical checkpoints remain audit history.

- **Repository:** `zeidhussain9-cloud/efps-internal-automatios`; deployment branch `crm-ui-dashboard`; Render service `srv-darsv560tbcc73cu4ip0`.
- **Inventory source and read model:** Notion Housing Listings is canonical; Supabase `public.crm_inventory_snapshot` is the dashboard projection, with `source_kind='housing_notion'`.
- **Reconciliation:** 104 active Notion pages / 104 active Supabase rows; 0 missing, 0 orphaned, 0 duplicate IDs, 0 semantic field mismatches. Intake events: 104 processed, 104 Listing IDs present, 104/104 mapped to snapshot IDs.
- **Reserved fields:** AU `source_group` and AV `inventory_locked` are blank across all 104 Notion pages. 43 populated `inventory_locked` values were corrected.
- **Runtime:** Supabase `notion-inventory-state` ACTIVE v9 (JWT verification on); AWS stack `efps-notion-property-intake` `UPDATE_COMPLETE`; Lambda `efps-notion-intake` Active in `ap-southeast-2`.
- **Recovery:** EventBridge reconciliation runs every 15 minutes, queues only changed/restored pages, repairs event Listing IDs, and soft-deletes snapshot rows absent from the full Notion page result. Empty Notion results fail closed. A rented listing was soft-deleted through the worker and successfully reactivated by the reconciler. Actual Notion `page.undeleted` delivery remains unobserved, but missed restore events are recovered automatically by the scheduled fallback.
- **Failure handling:** Lambda retries empty Listing ID allocation three times; asynchronous failures receive two retries and then enter a 14-day SQS failure queue. Structured logs correlate page ID, event type, webhook event ID, AWS request ID, outcome and duration; log retention is 30 days.
- **Inventory counts:** 104 active rows = 87 Available + 17 Rented Out. Production `/health` returned HTTP 200.
- **Legacy boundaries:** Sheet reconciliation cron is disabled; compatibility Sheet writes and the old WhAPI `NEW` listener remain untouched pending separately agreed cleanup. Raw Property Intake photo/enrichment credentials remain a separate unverified compatibility path.
- **Notion webhook settings:** all eight Page event selections remain user-confirmed and unchanged. No secret values were exposed or changed.

### Inventory intake paths — current ownership

~~~text
SLACK OPERATOR INTAKE
  /efps add-property and /efps photos start
  -> canonical Inventory pipeline
  -> legacy Housing_Listings compatibility sheet (not read by dashboard)

NOTION PROPERTY INTAKE (raw-details/photos compatibility path; legacy media credentials need separate validation)
  Notion Connection webhook
  -> isolated Lambda signature validation + async worker
  -> Supabase crm_inventory_intake_events idempotency claim
  -> canonical Inventory processing pipeline
  -> compatibility Housing_Listings Sheet + Cloudinary photo URLs
  -> Housing Listings Notion page + intake relation/status

CANONICAL NOTION HOUSING LISTINGS
  -> signed page events (all eight Page event types retained)
  -> isolated Lambda + Supabase idempotency claim
  -> direct upsert/tombstone of public.crm_inventory_snapshot
  -> dashboard reads active housing_notion rows only

LEGACY SHEET RECONCILIATION
  -> Supabase cron removed on 2026-11-13
  -> dashboard ignores housing_sheet rows

LEGACY WHAPI NEW-DELIMITED INVENTORY
  -> retained only pending the final cleanup phase
  -> old efps-sessions DynamoDB state
  -> not part of the new Notion intake architecture
~~~

The Notion idempotency table and RPCs are in Supabase, not DynamoDB. The existing legacy WhAPI path is intentionally retained for now and must not be removed until the final cleanup phase.

### Current Notion operational flow

```text
Notion Housing Listings
  -> signed page event
  -> asynchronous Lambda worker fetches the latest page from Notion
  -> Supabase crm_inventory_intake_events claim/replay protection
  -> direct housing_notion upsert to crm_inventory_snapshot by immutable listing_id
  -> CRM dashboard

Notion Property Intake (raw details and photos)
  -> existing deterministic processing and listing-page creation
  -> Housing Listings page event feeds the same direct projection
```

The old WhAPI `NEW`-delimited inventory path is legacy and retained only until the final cleanup phase. It is not the new Notion workflow. Remaining Sheets writes are legacy compatibility intake; they do not feed the dashboard inventory.

### Current WhAPI API safety boundary

The CRM webhook remains a live ingestion boundary, but direct WhAPI API traffic is intentionally disabled by the current safety release. The shared client defaults EFPS_WHAPI_API_ENABLED=false, EFPS_WHAPI_CATALOG_WRITE_ENABLED=false, and EFPS_WHAPI_WEBHOOK_ENABLED=true, and hard-blocks all non-catalog API operations. Catalog-repair admin code/workflow has been removed. The Stage 3 catalogue implementation remains repository code/history but is not an active production API path while these controls are disabled.

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
  -> Notion-owned operational mirror in crm_inventory_snapshot
  -> event-driven Notion page sync (Sheet cron disabled)
  -> crm_inventory_sync_changes records future field-level changes
```

### Test-history checkpoint

The P1–P5 hardening release added regression coverage for webhook promotion linkage, reserved AU/AV exclusion, and disposable inventory create/edit/delete history. Current migration verification: 139 Node tests, 88 inventory Python tests, browser 1/1, production build, and SAM template lint all PASS. Earlier counts remain historical checkpoints.



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

## Historical runtime boundary — 2026-09-16
This was the acceptance state at the migration checkpoint, not the current runtime state. The current verified WhAPI and Notion inventory deployment facts are recorded in the authoritative 2026-11-13 section at the top of this document.

## Historical live-system migration boundary — 2026-09-16

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

Historical note: the Notion adapter originally used the legacy `efps-sessions` table. That implementation has been replaced. The current Notion adapter uses Supabase `crm_inventory_intake_events` through the `notion-inventory-state` Edge Function; the isolated SAM template has no DynamoDB parameter or DynamoDB IAM actions. See the current verified state and remaining AWS secret/subscription gates at the top of this document.

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


## Latest verified Notion inventory boundary — 2026-11-14 (live check)

Notion Housing Listings remains the canonical operator editor. The CRM projection has 106 active Notion-owned rows and 1 soft-deleted tombstone. Supabase notion-inventory-state is ACTIVE v12 and the Maps API-unavailable fallback is deployed. Two current intake submissions are Processed and reconciled to Housing Listings and Supabase. Notion webhook history remains in crm_inventory_intake_events; WhatsApp events remain in crm_webhook_events. Processing Notes are replaceable summaries, not append-only narratives. No tables were deleted.
