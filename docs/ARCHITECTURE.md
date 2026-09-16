# EFPS Internal Automations — Architecture

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

### Stage 3 — Downstream Operations
Stage 3 is the downstream boundary for later consumers. It is not part of the current Inventory Phase-1 publishing implementation.

## Canonical sheet
The single physical shape is `shared/google_sheets/schema.py`: 48 columns A:AV. The schema records owner, stage, allowed values where verified, and declared dependencies. AU (`source_group`) and AV (`inventory_locked`) are reserved/dummy columns with no current owner or operational stage.

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
Inventory Stage 1/2 may write only A:D and F:AO. It must not write E (`listing_state`), AP:AT (Housing/Meta downstream fields), AU (`source_group`), or AV (`inventory_locked`). AU/AV are reserved/dummy columns and must remain blank. Stage-3 writers do not currently use AU/AV.

## Runtime boundary
Inventory Phase-1 runtime verification has completed successfully for the canonical Google Sheets read/write boundary and for Google Maps direct API access plus application-path consumption. WhAPI live channel identity/subscription/deployment, Cloudinary live upload, and Slack live deployment remain separate runtime acceptance items.

## Lead management runtime contracts

The Lead interactive surface uses Slack message/thread history for `history::open`; it does not use a `lead_history` modal. Lost-stage actions directly set the stage and do not open a `lead_lost` modal. Audit display timestamps are rendered in IST while audit records are stored with UTC timestamps.

The Lead dashboard is discovered through Slack history. Dashboard state is not persisted in `DDB_SESSIONS`, newly created dashboards are not pinned, and digest refresh uses the same Slack-history discovery/update/post behavior.

The WhAPI webhook authenticates the query token before evaluating the live gate. This ordering matches the inspected legacy `modules/efps-whapi-panel/webhook_handler.py:lambda_handler` behavior at legacy commit `bd186c7c3418d633bca6766b1b92204c7a56d484`.

## Documentation authority

`docs/DATA_CONTRACTS.md` owns cross-module field semantics and dependencies. `docs/DETERMINISTIC_FIELD_RESOLUTION.md` owns candidate resolution and precedence. `docs/INVENTORY_SOURCE_EXTRACTION.md` owns source segmentation and extraction boundaries. `docs/DOCUMENT_MAP.md` owns documentation roles.
