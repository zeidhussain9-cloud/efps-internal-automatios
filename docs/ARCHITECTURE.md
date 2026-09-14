# EFPS Internal Automations — Architecture

This is the canonical cross-repository architecture reference.

## Core model
- `shared/` — reusable technical capabilities and integrations.
- `modules/` — EFPS business capabilities and business decisions.

> Shared services provide capabilities; modules decide when and why they are used.

## Shared capabilities
- `shared/cloudinary/` — reusable media storage/upload capability.
- `shared/google_sheets/` — Sheets transport and the canonical 48-column `Housing_Listings` contract.
- `shared/google_maps/` — reusable Maps URL/geocoding capability; inventory decides when it is required.
- `shared/whatsapp_whapi/` — WhAPI transport, webhook normalization/verification, and the two-listener source boundary.
- `shared/slack/` — reserved placeholder only; no Slack functionality is implemented here.

Verified inventory listener sender numbers are `917975102130` and `919902024973`. Other inbound traffic follows the lead/non-inventory boundary documented by WhAPI.

## Inventory top-level stages

### Stage 1 — Initial / Webhook
Dedicated inventory-listener traffic enters the inventory module. `NEW` opens a property session; subsequent messages are collected until the next `NEW`, which closes the property. A listing identity is created and the raw record is persisted.

### Stage 2 — Deterministic Extraction / Property Processing
The completed raw property is processed as one business stage. Its internal sub-steps are deterministic extraction, normalization/business rules, Google Maps resolution, deterministic validation, and optional AI verification/wording-only beautification. These sub-steps are intentionally not separate top-level stages.

### Stage 3 — Downstream Operations
The processed inventory record is consumed by downstream workflows. Housing Portal owns AP:AR (`posted_url`, `posted_at`, `error_notes`); Meta Catalogue owns AS:AT (`meta_catalog_id`, `meta_catalog_status`); lifecycle/control owns E and AV (`listing_state`, `inventory_locked`) when implemented.

## Canonical sheet
The single physical shape is `shared/google_sheets/schema.py`: 48 columns A:AV in the latest supplied order. The schema records owner, top-level population stage, allowed values where verified, and dependencies. `listing_id` is immutable row identity.

## Stage-1/2 write boundary
Inventory Stage 1/2 may write A:D, F:AO, and AU. It must not write E (`listing_state`), AP:AT (Housing/Meta downstream fields), or AV (`inventory_locked`). Stage-3 writers are responsible for those protected fields.

## Runtime boundary
Source code cannot prove current production credentials, WhAPI webhook subscriptions, deployed webhook URL, Maps API access, or AI runtime access. Those remain runtime verification items and are never guessed.
