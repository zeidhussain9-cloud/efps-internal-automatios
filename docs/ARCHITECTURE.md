# EFPS Internal Automations — Architecture

This is the canonical cross-repository architecture reference.

## Core model
- `shared/` — reusable technical capabilities and integrations.
- `modules/` — EFPS business capabilities and business decisions.

> Shared services provide capabilities; modules decide when and why those capabilities are used.

## Shared capabilities
- `shared/cloudinary/` — reusable media storage; Phase 2 inventory media consumption.
- `shared/google_sheets/` — Sheets transport and the canonical 48-column `Housing_Listings` contract.
- `shared/google_maps/` — reusable Maps URL/geocoding capability. It must remain business-neutral; modules decide when a Maps lookup is required.
- `shared/whatsapp_whapi/` — WhAPI transport, webhook normalization/verification, and the two-listener source boundary.
- `shared/slack/` — reserved placeholder only; no Phase-1 implementation.

Verified inventory listener sender numbers are `917975102130` and `919902024973`. Other inbound traffic follows the lead/non-inventory boundary documented by WhAPI.

## Phase-1 inventory
`modules/efps-inventory-mgmnt/` owns the property workflow from `NEW → collect → NEW` through raw-text assembly, deterministic extraction, normalization, Maps resolution, validation, AI verification, and wording-only AI beautification.

The deterministic extractor reads only `raw_message_text`; it does not use existing Sheet canonical values as source facts. Images are recognized/countable but are not downloaded in Phase 1. Downstream-owned AK:AO fields remain untouched. Phase 1 does not implement lifecycle/locking, duplicate governance, Cloudinary media retrieval, or downstream publishing.

## Canonical sheet
The single source of physical shape is `shared/google_sheets/schema.py`: 48 columns A:AV, 41 contract + 2 extra + 5 tail. The schema records owner, first-population stage, allowed values, and field dependencies. `listing_id` is immutable row identity.

## Runtime boundary
Source code cannot prove current production credentials, WhAPI webhook subscriptions, deployed webhook URL, Maps API access, or Vertex runtime access. Those remain runtime verification items and are never guessed.
