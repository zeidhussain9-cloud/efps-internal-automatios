# EFPS Inventory Management

## Three-stage workflow

### Stage 1 — Initial / Webhook
The dedicated inventory listener receives the normalized WhAPI message. `NEW` opens a property session; subsequent messages from that listener are collected until the next `NEW`, which closes the property. A canonical `listing_id` is created for the property row, and the raw record is persisted with the source text and intake metadata.

### Stage 2 — Deterministic Extraction / Property Processing
The completed `raw_message_text` is the extraction source. Processing runs deterministic extraction, deterministic normalization/business rules, Google Maps resolution, deterministic validation, and then optional AI verification/wording-only beautification. AI cannot replace source facts or bypass a deterministic validation failure.

### Stage 3 — Downstream Operations
Stage 3 consumes the processed inventory record. Housing Portal owns `posted_url`, `posted_at`, and `error_notes`; Meta Catalogue owns `meta_catalog_id` and `meta_catalog_status`; inventory lifecycle control owns `listing_state` and `inventory_locked` when that downstream/lifecycle functionality is implemented.

## Property boundary
`NEW` is the property-session delimiter. Every text message until the next `NEW` belongs to that property. Media are recognized/countable but their binary payloads are not downloaded or serialized into `raw_message_text` in the current implementation.

## Raw source
Text messages are preserved in `raw_message_text`, in arrival order with timestamp/message-id metadata when available. Duplicate webhook deliveries carrying the same message ID are ignored within the active session.

## Extraction source
Deterministic extraction reads the completed property's `raw_message_text` only. Existing canonical Sheet values are never used as extraction input during replay.

## Maps
`shared/google_maps` is the reusable technical Maps capability. Inventory owns when/why a property requires Maps and consumes verified results for `locality`, `pincode`, and `google_maps_url`.

## Current implementation boundary
This change implements the Stage 1/Stage 2 schema alignment and processing rules. Stage 3 posting/catalogue/lifecycle writers remain outside the inventory Phase-1 write path; their owned columns are protected from Stage-1/2 writes.
