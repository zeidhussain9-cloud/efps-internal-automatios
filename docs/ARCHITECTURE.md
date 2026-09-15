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

Verified inventory listener sender numbers are `917975102130` and `919902024973`. Other inbound traffic follows the lead/non-inventory boundary documented by WhAPI.

## Inventory top-level stages

### Stage 1 — Initial / Webhook
Dedicated inventory-listener traffic enters the inventory module. `NEW` opens a property session; subsequent messages are collected until the next `NEW`, which closes the property. A listing identity is created and the raw record is persisted.

### Stage 2 — Deterministic Extraction / Property Processing
The completed raw property is processed as one business stage. Its internal sub-steps are canonical source-message segmentation, deterministic extraction, field candidate resolution, normalization/business rules, Google Maps resolution, deterministic validation, and optional AI verification/wording-only beautification. These sub-steps are intentionally not separate top-level stages.

The actual Stage-2 inventory entry point is `modules/efps-inventory-mgmnt/src/pipeline.py:process_closed_session()`. Deterministic extraction uses `src/source_segments.py` before labelled fields are read, so a field cannot consume a later WhatsApp message. `src/field_resolution.py` is the sole resolver for recurring multi-candidate fields: BHK, maintenance, and internal property type. Extractors discover source candidates; the resolver selects the authoritative candidate; normalization canonicalizes it. Existing Sheet values are never extraction input. When a Maps URL is supplied or extracted, it is resolved through `shared/google_maps`. A `VERIFIED` result enriches `google_maps_url`, `locality`, and `pincode`; `PARTIAL_MATCH`, `NEEDS_RUNTIME_VERIFICATION`, and `NOT_FOUND` are informational issues and do not by themselves convert an otherwise valid deterministic result to `Needs Review`.

### Stage 3 — Downstream Operations
Stage 3 is the downstream boundary for later consumers. It is not part of the current Inventory Phase-1 publishing implementation. Future Housing Portal and Meta Catalogue work requires explicit implementation requirements and authorization.

## Canonical sheet
The single physical shape is `shared/google_sheets/schema.py`: 48 columns A:AV in the latest supplied order. The schema records owner, top-level population stage, allowed values where verified, and dependencies. `listing_id` is immutable row identity.

## Stage-1/2 write boundary
Inventory Stage 1/2 may write A:D, F:AO, and AU. It must not write E (`listing_state`), AP:AT (Housing/Meta downstream fields), or AV (`inventory_locked`). Stage-3 writers are responsible for those protected fields.

## Runtime boundary
Inventory Phase-1 runtime verification has completed successfully for the canonical Google Sheets read/write boundary and for Google Maps direct API access plus application-path consumption. WhAPI live channel identity/subscription/deployment, Cloudinary live upload, and Slack live deployment remain separate runtime acceptance items. No runtime secret is stored in the repository.

## Stage-2 source extraction contract

`docs/INVENTORY_SOURCE_EXTRACTION.md` is the canonical detailed source-segmentation/extraction contract. `docs/DETERMINISTIC_FIELD_RESOLUTION.md` is the canonical candidate-resolution contract. The repository must not solve a recurring extraction defect by adding an isolated regex exception without adding the corresponding source-shape regression fixture and checking the canonical segmentation/resolution boundary.
