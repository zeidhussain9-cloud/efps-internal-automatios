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

The canonical Stage-2 entry point is `process_closed_session()` in `modules/efps-inventory-mgmnt/src/pipeline.py`. Maps is invoked after deterministic extraction/normalization. Verified Maps results may populate only `google_maps_url`, `locality`, and `pincode` in this path. Maps states other than `VERIFIED` fail closed into `Needs Review`.

### Stage 3 — Downstream Operations
Consumes the processed inventory record. Housing Portal owns `posted_url`, `posted_at`, and `error_notes`. Meta Catalogue owns `meta_catalog_id` and `meta_catalog_status`. Lifecycle/control owns `listing_state` and `inventory_locked` when implemented.

## Stage-1 raw contract

`NEW` opens a property session. All subsequent text messages from that inventory listener until the next `NEW` are appended in arrival order to `raw_message_text`. The closing `NEW` is the session delimiter and is not property content. Media are recognized/countable but their binary payloads are not serialized into raw text in the current Phase-1 implementation. Duplicate webhook deliveries with the same message ID are ignored within an active session.

## Stage-2 source and authority

Deterministic extraction reads the completed `raw_message_text` only. Existing canonical Sheet values are not extraction input. Normalization may apply only verified mechanical/business rules; it must not fabricate property facts.

### Direct source-field rules

- `internal_property_type`: prefer an explicit source field. Normalize it to `Gated Community`, `Semi Gated`, or `Standalone`. If the explicit field is absent, explicit `Semi Gated` wording wins, explicit `Gated Community`/`Gated Society` wording maps to `Gated Community`, and otherwise the deterministic fallback is `Standalone`.
- `locality`: read an explicit `Location`, `Locality`, or `Area` source field when available. A verified Maps result may replace it with the verified Maps locality.
- `society_name`: use the directly supplied society name. If absent, use the resulting locality/location value as the fallback. If Maps subsequently supplies a verified locality, the pipeline applies the same fallback before persistence.
- `landmark`: use the directly supplied landmark. If absent, use the resulting locality/location value as the fallback.
- `property_subtype`: use an explicit source subtype/property-subtype value and normalize supported aliases. If absent, use `Apartment` only for a normal floor-bearing apartment-style record; standalone-property wording does not invent `Apartment`.
- `property_highlights`: preserve an explicit source highlight. Otherwise construct only factual deterministic fragments supported by the source, such as Utility area, supported subtype alias wording, multiple-unit/floor availability, or RK wording.
- `catalog_title`: if blank, construct a factual deterministic fallback from available furnishing type, BHK, and location. Optional AI beautification may later rewrite only this wording field and `property_highlights` without adding facts.
- `age_of_property_years`: populate only from an explicit/authoritative property-age fact. Do not infer age from Maps or other weak signals; blank is valid when unavailable.

## Core deterministic rules

- Decimal BHK values such as `2.5 BHK` are preserved as `2.5 BHK`.
- `G`/`Ground` floor normalizes to `0`.
- When carpet area is blank and built-up area is known, carpet area is derived as 90% of built-up area.
- Maintenance is taken directly from source. Numeric `k`/lakh values are normalized to rupees. Mixed values such as `2777 + Water` preserve the amount and stated suffix. `Maintenance: Included` means maintenance `0` and `maintenance_included = Yes`.
- Deposit expressed in months is calculated from monthly rent.
- Semi Furnished and Fully Furnished have deterministic furnishing defaults; explicit source furnishings are preserved.
- Source text indicating Unfurnished does not create a third furnish type; `furnish_type` and `flat_furnishings` remain blank.
- `servant_room` is `Yes` only when explicitly stated; otherwise `No`.
- `pet_friendly` is `No` when source text explicitly says pets are not allowed/not permitted/prohibited (or equivalent no-pet wording). If no pet restriction is mentioned, the established last-resort default is `Yes`.
- `covered_parking` defaults to `1` for Gated Community and Semi Gated when no explicit covered-parking value exists. Standalone does not receive this default.
- `preferred_tenant_type` is normalized to the live Sheet vocabulary: family variants → `Family`; anyone/open-for-all variants → `Open For All`.
- `bachelor_preference` is populated only from an explicit source preference or the established female-bachelor rule; family without an explicit bachelor preference leaves it blank.
- `internal_property_type` determines default `society_amenities` when no explicit compatible amenity value exists: Gated Community → exact gated Sheet combination; Semi Gated → exact semi-gated Sheet combination; Standalone → `-`.
- Deterministic processing fails closed rather than guessing unsupported facts.

## Furnish type contract

Live `Housing_Listings` validation for column M `furnish_type` is a strict `ONE_OF_LIST` with exactly `Fully Furnished` and `Semi Furnished`. Unfurnished source wording remains blank rather than creating a non-existent Sheet value.

## Verified live Sheet dropdown/value contract

The live production Sheet was read-only inspected for the current Phase-1 contract. Columns D, M, Y, Z, AE, and AF use strict `ONE_OF_LIST` validation with custom UI enabled. Exact observed values are:

| Column | Field | Exact observed dropdown values |
|---|---|---|
| D | `internal_property_type` | `Gated Community`; `Semi Gated`; `Standalone` |
| M | `furnish_type` | `Fully Furnished`; `Semi Furnished` |
| Y | `preferred_tenant_type` | `Family`; `Open For All` |
| Z | `bachelor_preference` | `Female Only `; `Male Only`; `Open for both` |
| AE | `society_amenities` | `Security, Lift, CCTV, Power Backup`; `Club House, Lift, Gym, CCTV, Power Backup, Swimming Pool, Garden, Sports, Kids Area`; `-` |
| AF | `flat_furnishings` | `Wardrobe, Modular Kitchen, Geyser, Fan, Light`; `Wardrobe, Modular Kitchen, Geyser, Fan, Light, Fridge, Washing Machine, TV, Sofa, Bed, Dining Table` |

The observed `Female Only ` value contains a trailing space and is intentionally preserved as the canonical Sheet value. Column AA `pet_friendly` has no Sheet validation rule; populated live values observed are `Yes` and `No`, and the application contract now emits only those two values.

No conditional/row-dependent Google Sheets dropdown validation was observed for the inspected dropdown fields. Their relationships are application/business dependencies.

## Verified business interdependencies

- `internal_property_type` → `society_amenities`: Gated Community → exact gated combination; Semi Gated → exact semi-gated combination; Standalone → `-` when amenities are blank.
- `internal_property_type` → `covered_parking`: Gated Community/Semi Gated → `1` when covered parking is blank.
- `furnish_type` → `flat_furnishings`: deterministic furnishing defaults only when explicit furnishings are absent.
- `preferred_tenant_type` → `bachelor_preference`: canonical tenant normalization plus explicit bachelor/female-bachelor handling; no invalid `Not Allowed` value is generated.
- `maintenance_included` ↔ `maintenance` and `monthly_rent` → `security_deposit` remain deterministic dependencies.

## Validation authority

Deterministic validation rejects values outside the canonical application contract. The live Sheet vocabulary is authoritative for fields with verified validation lists. `pet_friendly` has no Sheet dropdown but its observed and canonical application values are `Yes` and `No`.

## Stage-3 ownership boundary

Stage 1/2 inventory writes are restricted to A:D, F:AO, and AU. They must never overwrite E (`listing_state`), AP:AT (Housing/Meta downstream fields), or AV (`inventory_locked`).

## Verification boundary

Inventory Phase-1 verification has established the 48-column production sheet contract, Stage-1/2 write boundary, live Google Sheets access, live Google Maps Geocoding access, Maps application path, actual Stage-2 deterministic + Maps + validation path without a production Sheet write during the end-to-end probe, and live dropdown/populated-value observations recorded above.

Repository code changes that alter deterministic rules must be regression-tested before live production extraction.
