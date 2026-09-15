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

### Furnish type contract

Live `Housing_Listings` validation for column M `furnish_type` is a strict `ONE_OF_LIST` with exactly:

- `Fully Furnished`
- `Semi Furnished`

The repository contract is aligned to those two values. Source text such as `Unfurnished`, `un-furnished`, `not furnished`, or `empty` does not create a third `furnish_type` value. It results in blank `furnish_type` and blank `flat_furnishings`, because the live Sheet has no `Unfurnished` dropdown value.

`Semi Furnished` and `Fully Furnished` drive deterministic `flat_furnishings` defaults only when explicit `flat_furnishings` are absent.

## Verified live Sheet dropdown contract

The live production Sheet was read-only inspected for the current Phase-1 contract. Columns D, M, Y, Z, AE, and AF use strict `ONE_OF_LIST` validation with custom UI enabled. The exact observed values are:

| Column | Field | Exact observed dropdown values |
|---|---|---|
| D | `internal_property_type` | `Gated Community`; `Semi Gated`; `Standalone` |
| M | `furnish_type` | `Fully Furnished`; `Semi Furnished` |
| Y | `preferred_tenant_type` | `Family`; `Open For All` |
| Z | `bachelor_preference` | `Female Only `; `Male Only`; `Open for both` |
| AE | `society_amenities` | `Security, Lift, CCTV, Power Backup`; `Club House, Lift, Gym, CCTV, Power Backup, Swimming Pool, Garden, Sports, Kids Area`; `-` |
| AF | `flat_furnishings` | `Wardrobe, Modular Kitchen, Geyser, Fan, Light`; `Wardrobe, Modular Kitchen, Geyser, Fan, Light, Fridge, Washing Machine, TV, Sofa, Bed, Dining Table` |

The observed `Female Only ` value contains a trailing space in the live validation configuration. This is intentionally preserved as the canonical Sheet value; equivalent source wording is normalized to this exact string.

Column AA `pet_friendly` has no Google Sheets data-validation rule. However, the populated live values inspected in AA are exactly `Yes` and `No`.

No conditional/row-dependent Google Sheets dropdown validation was observed for D, M, Y, Z, AE, or AF: each has one validation configuration in the inspected range. Therefore the field dependencies below are application/business rules, not conditional Sheet dropdown rules.

## Verified business interdependencies

- `internal_property_type` → `society_amenities`: `Gated Community` deterministically defaults to the exact live Sheet value `Club House, Lift, Gym, CCTV, Power Backup, Swimming Pool, Garden, Sports, Kids Area`; `Semi Gated` deterministically defaults to `Security, Lift, CCTV, Power Backup`; `Standalone` does not invent amenities. Explicit source amenities are preserved and deterministic validation requires any nonblank value to be one of the verified Sheet combinations.
- `furnish_type` → `flat_furnishings`: `Semi Furnished` and `Fully Furnished` populate the corresponding deterministic default furnishing sets only when `flat_furnishings` is blank. Unfurnished source text produces blank furnishing fields.
- `preferred_tenant_type` → `bachelor_preference`: Family/family-only with no explicit bachelor preference now leaves `bachelor_preference` blank because the live Sheet has no `Not Allowed` value. `Family & Female Bachelors` and explicit female preference normalize to the exact live Sheet value `Female Only `, including the observed trailing space.
- `society_amenities` declares dependency on `internal_property_type` in the canonical schema.
- `flat_furnishings` declares dependency on `furnish_type` in the canonical schema.
- `bachelor_preference` declares dependency on `preferred_tenant_type` in the canonical schema.
- `maintenance` ↔ `maintenance_included` and `security_deposit` → `monthly_rent` are additional deterministic field dependencies.

## Validation authority

Deterministic validation rejects values that are outside the canonical application contract. No Sheet dropdown value is to be invented from source text or general knowledge. The live Sheet vocabulary is authoritative for fields with verified validation lists.

## Stage-3 ownership boundary

Stage 1/2 inventory writes are restricted to A:D, F:AO, and AU. They must never overwrite E (`listing_state`), AP:AT (Housing/Meta downstream fields), or AV (`inventory_locked`). Housing and Meta downstream modules own their respective Stage-3 fields.

## Verification boundary

Inventory Phase-1 verification has established the 48-column production sheet contract, the Stage-1/2 write boundary, live Google Sheets access, live Google Maps Geocoding access, the Maps application path, the actual Stage-2 deterministic + Maps + validation path without a production Sheet write during the end-to-end probe, and the live dropdown/populated-value observations recorded above.

The repository still does not by itself prove current WhAPI deployment state, Cloudinary live upload state, or Slack live deployment state. Those remain separate runtime acceptance boundaries.
