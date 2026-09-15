# Data Contracts

This is the canonical cross-module data ownership and contract reference for EFPS Internal Automations.

## Inventory contract

`shared/google_sheets/schema.py` is the single physical `Housing_Listings` contract: 48 columns A:AV in the latest supplied order. Each column records owner, top-level population stage, allowed values where verified, and declared dependencies.

The latest physical order is:

`A listing_id, B status, C intake_status, D internal_property_type, E listing_state, F onboarded_on, G raw_message_text, H locality, I society_name, J landmark, K pincode, L google_maps_url, M furnish_type, N BHK, O bathrooms, P balconies, Q floor_number, R total_floors, S built_up_area, T carpet_area, U monthly_rent, V maintenance, W maintenance_included, X security_deposit, Y preferred_tenant_type, Z bachelor_preference, AA pet_friendly, AB servant_room, AC covered_parking, AD open_parking, AE society_amenities, AF flat_furnishings, AG property_highlights, AH catalog_title, AI cloudinary_image_urls, AJ age_of_property_years, AK whatsapp_contact_link, AL whatsapp_group_link, AM transaction_type, AN property_subtype, AO city, AP posted_url, AQ posted_at, AR error_notes, AS meta_catalog_id, AT meta_catalog_status, AU source_group, AV inventory_locked.`

## Stage-2 deterministic contract

The completed `raw_message_text` is the only extraction source. Existing Sheet values are not extraction input.

### Canonical execution boundary

`modules/efps-inventory-mgmnt/src/pipeline.py:deterministic()` is the authoritative deterministic processing entry point used by Stage 2. It performs source extraction, resolves `internal_property_type` through `field_resolution.py`, and passes that canonical result explicitly into normalization. `normalize.py` must not independently rediscover or reclassify `internal_property_type`.

### Direct fields

- `internal_property_type`: extract and resolve source evidence to exactly `Gated Community`, `Semi Gated`, or `Standalone`. Boolean gating labels are explicit evidence. Explicit negative boolean values resolve to `Standalone`. When no source evidence exists, the declared fallback is `Standalone`.
- `society_name`: use the directly supplied society name. Also accept apartment/community/building-name labels. Strip presentation-only markdown. Placeholder-only values such as `*` or `-` count as blank. If blank, use the resulting location/locality.
- `landmark`: use the directly supplied landmark. Also accept landmark labels. Strip presentation-only markdown. Placeholder-only values such as `*` or `-` count as blank. If blank, use the resulting location/locality.
- `locality`: use explicit `Property Location`, `Location`, `Locality`, or `Area`; a verified Maps locality may replace it.
- `property_subtype`: use explicit subtype and normalize supported aliases. If absent, default to `Apartment` only for a normal floor-bearing apartment-style record; standalone-property wording does not invent Apartment.
- `property_highlights`: preserve explicit highlights. Otherwise construct only factual deterministic fragments supported by source.
- `catalog_title`: construct a factual fallback from furnishing type, BHK, and location when blank. AI may rewrite wording only.
- `age_of_property_years`: populate only from an explicit/authoritative property-age fact; otherwise blank.

### Canonical source-message parsing

Inventory sessions can concatenate multiple WhatsApp messages. `modules/efps-inventory-mgmnt/src/source_segments.py` is the canonical segmentation implementation. Labelled extraction operates inside source-message units so a field cannot consume a later message's value.

### Canonical field resolution

`modules/efps-inventory-mgmnt/src/field_resolution.py` is the canonical candidate-resolution layer for BHK, maintenance, and internal property type. Extractors discover candidates; the resolver selects the authoritative source candidate; normalization canonicalizes that result. Existing Sheet values are never candidates.

For repeated source evidence, later explicit values supersede earlier explicit values. Explicit labelled/boolean evidence outranks generic wording. Explicit negative gating is authoritative against generic positive wording.

- `BHK`: preserve decimal values and later explicit corrections.
- `maintenance`: only maintenance-labelled context or the specific `rent + maintenance` form can create a maintenance candidate. Normalize `K`/lakh units. Preserve source qualifiers such as `+ Water`.
- `internal_property_type`: one canonical resolver owns Gated Community, Semi Gated, and Standalone. Downstream normalization consumes the resolved value and does not rediscover it.

### Dependency graph

```text
raw_message_text
  |
  +--> BHK
  +--> maintenance --------> maintenance_included
  +--> internal_property_type --> society_amenities
  |                             |
  |                             +--> covered_parking (default only when blank)
  +--> furnish_type ----------> flat_furnishings (default only when blank)
  +--> built_up_area ----------> carpet_area (fallback only when blank)
  +--> monthly_rent -----------> security_deposit (when deposit is expressed in months)
  +--> preferred_tenant_type --> bachelor_preference
```

These are application/business dependencies. A dependent field may still have explicit source evidence; the parent controls only the documented fallback/default relationship.

### Maintenance storage contract

`maintenance` is stored as a normalized numeric amount with an optional source qualifier. Examples:

- `3.7K` → `3700`
- `2777 + Water` → `2777 + Water`
- `Included` → `0`, with `maintenance_included = Yes`
- `5K + Water` → `5000 + Water`

`maintenance_included` is an independently evaluated fact. The presence of an amount does not imply inclusion.

### Core deterministic rules

- Decimal BHK values such as `2.5 BHK` are preserved.
- `G`/`Ground` floor normalizes to `0`.
- Carpet area defaults to 90% of built-up area when carpet area is blank.
- Deposit expressed in months is calculated from monthly rent.
- Semi Furnished and Fully Furnished receive deterministic furnishing defaults only when explicit furnishings are absent. Unfurnished leaves furnish fields blank because the live Sheet has no Unfurnished value.
- `servant_room` is `Yes` only when explicitly stated; otherwise `No`.
- `pet_friendly` is `No` when pets are explicitly not allowed/not permitted/prohibited; absent restriction retains the established `Yes` fallback.
- `covered_parking` defaults to `1` for Gated Community/Semi Gated when blank; Standalone does not receive this default.
- `preferred_tenant_type` normalizes family variants to `Family` and anyone/open-for-all variants to `Open For All`.
- `bachelor_preference` is populated only from explicit source preference or the established female-bachelor rule.
- `internal_property_type` determines the exact default `society_amenities`: Gated Community → gated combination; Semi Gated → semi-gated combination; Standalone → `-`.

## Review-status contract

`Needs Review` is reserved for deterministic validation errors or explicit AI conflicts after the deterministic gate. Google Maps uncertainty is recorded as an issue but does not by itself set `Needs Review`.

## Verified live Sheet vocabulary

| Column | Field | Exact observed values |
|---|---|---|
| D | `internal_property_type` | `Gated Community`; `Semi Gated`; `Standalone` |
| M | `furnish_type` | `Fully Furnished`; `Semi Furnished` |
| Y | `preferred_tenant_type` | `Family`; `Open For All` |
| Z | `bachelor_preference` | `Female Only `; `Male Only`; `Open for both` |
| AE | `society_amenities` | `Security, Lift, CCTV, Power Backup`; `Club House, Lift, Gym, CCTV, Power Backup, Swimming Pool, Garden, Sports, Kids Area`; `-` |
| AF | `flat_furnishings` | `Wardrobe, Modular Kitchen, Geyser, Fan, Light`; `Wardrobe, Modular Kitchen, Geyser, Fan, Light, Fridge, Washing Machine, TV, Sofa, Bed, Dining Table` |

Column AA `pet_friendly` has no Sheet validation rule; observed/application values are `Yes` and `No`.

## Stage-1/2 write boundary

Stage 1/2 writes are restricted to A:D, F:AO, and AU. E (`listing_state`), AP:AT (Housing/Meta downstream fields), and AV (`inventory_locked`) are protected.

## Model-audit contract

`tools/inventory_model_test.py` is read-only. It compares deterministic Stage-2 output against persisted Sheet values without using persisted Stage-2 values as extraction evidence. Blank Stage-2 cells becoming populated are expected projections. Lifecycle transitions, formatting-only differences, populated source conflicts, and protected-column changes are distinct categories.

A populated Sheet value that conflicts with a source-grounded deterministic result is a stale/historical Sheet conflict until adjudicated; the raw source remains authoritative for deterministic extraction. The audit fails closed while populated source conflicts or protected-column changes remain.

## Verification boundary

Production Google Sheets access, the 48-column contract, write boundary, Google Maps access/application path, and live dropdown observations have been verified. Repository changes to deterministic rules require regression coverage before live production extraction.
