# Data Contracts

This is the canonical cross-module data ownership and contract reference for EFPS Internal Automations.

## Inventory contract

`shared/google_sheets/schema.py` is the single physical `Housing_Listings` contract: 48 columns A:AV in the latest supplied order. Each column records owner, top-level population stage, allowed values where verified, and declared dependencies.

The latest physical order is:

`A listing_id, B status, C intake_status, D internal_property_type, E listing_state, F onboarded_on, G raw_message_text, H locality, I society_name, J landmark, K pincode, L google_maps_url, M furnish_type, N BHK, O bathrooms, P balconies, Q floor_number, R total_floors, S built_up_area, T carpet_area, U monthly_rent, V maintenance, W maintenance_included, X security_deposit, Y preferred_tenant_type, Z bachelor_preference, AA pet_friendly, AB servant_room, AC covered_parking, AD open_parking, AE society_amenities, AF flat_furnishings, AG property_highlights, AH catalog_title, AI cloudinary_image_urls, AJ age_of_property_years, AK whatsapp_contact_link, AL whatsapp_group_link, AM transaction_type, AN property_subtype, AO city, AP posted_url, AQ posted_at, AR error_notes, AS meta_catalog_id, AT meta_catalog_status, AU source_group, AV inventory_locked.`

`listing_id` in A is immutable row identity.

## Top-level population stages

### Stage 1 — Initial / Webhook
Receives the dedicated inventory-listener traffic, applies the property-session delimiter, creates the property identity, captures raw source text and intake metadata, and persists the initial raw record.

### Stage 2 — Deterministic Extraction / Property Processing
Processes the completed raw property. This single stage contains deterministic extraction, deterministic normalization/business rules, Google Maps resolution, deterministic validation, and optional AI verification/wording-only beautification. These are processing sub-steps, not separate top-level stages.

The canonical Stage-2 entry point is `process_closed_session()` in `modules/efps-inventory-mgmnt/src/pipeline.py`. Maps is invoked after deterministic extraction/normalization. Verified Maps results may populate only the Maps-owned normalized fields `google_maps_url`, `locality`, and `pincode` in this path. Maps states other than `VERIFIED` fail closed into `Needs Review`.

### Stage 3 — Downstream Operations
Consumes the processed inventory record. Housing Portal owns `posted_url`, `posted_at`, and `error_notes`. Meta Catalogue owns `meta_catalog_id` and `meta_catalog_status`. Lifecycle/control owns `listing_state` and `inventory_locked` when implemented.

## Stage-1 raw contract

`NEW` opens a property session. All subsequent text messages from that inventory listener until the next `NEW` are appended in arrival order to `raw_message_text`. The closing `NEW` is the session delimiter and is not property content. Media are recognized/countable but their binary payloads are not serialized into raw text in the current Phase-1 implementation. Duplicate webhook deliveries with the same message ID are ignored within an active session.

## Stage-2 source and authority

Deterministic extraction reads the completed `raw_message_text` only. Existing canonical Sheet values are not extraction input. Normalization may apply only verified mechanical/business rules; it must not fabricate property facts.

Verified deterministic rules include decimal BHK preservation, ground-floor normalization to `0`, carpet-area derivation at 90% of built-up area when blank, maintenance-included normalization to `0`, month-based deposit calculation, deterministic furnishing defaults, property-subtype alias normalization, explicit gated/semi-gated/standalone classification, deterministic amenity defaults, and the family/bachelor dependency. Explicit source values are preserved rather than silently overwritten.

Maps is a technical capability invoked by inventory processing, not a separate top-level stage. AI remains advisory and cannot replace source facts or bypass deterministic validation.

## Stage-3 ownership boundary

Stage 1/2 inventory writes are restricted to A:D, F:AO, and AU. They must never overwrite E (`listing_state`), AP:AT (Housing/Meta downstream fields), or AV (`inventory_locked`). Housing and Meta downstream modules own their respective Stage-3 fields.

## Verification boundary

Inventory Phase-1 verification has established the 48-column production sheet contract, the Stage-1/2 write boundary, live Google Sheets access, live Google Maps Geocoding access, the Maps application path, and the actual Stage-2 deterministic + Maps + validation path without a production Sheet write during the end-to-end probe.

The repository still does not by itself prove current WhAPI deployment state, Cloudinary live upload state, or Slack live deployment state. Those remain separate runtime acceptance boundaries.
