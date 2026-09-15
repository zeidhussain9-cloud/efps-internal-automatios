# Data Contracts

This is the canonical cross-module data ownership and contract reference for EFPS Internal Automations.

## Inventory contract

`shared/google_sheets/schema.py` is the single physical `Housing_Listings` contract: 48 columns A:AV in the latest supplied order. Each column records owner, top-level population stage, allowed values where verified, and declared dependencies.

The latest physical order is:

`A listing_id, B status, C intake_status, D internal_property_type, E listing_state, F onboarded_on, G raw_message_text, H locality, I society_name, J landmark, K pincode, L google_maps_url, M furnish_type, N BHK, O bathrooms, P balconies, Q floor_number, R total_floors, S built_up_area, T carpet_area, U monthly_rent, V maintenance, W maintenance_included, X security_deposit, Y preferred_tenant_type, Z bachelor_preference, AA pet_friendly, AB servant_room, AC covered_parking, AD open_parking, AE society_amenities, AF flat_furnishings, AG property_highlights, AH catalog_title, AI cloudinary_image_urls, AJ age_of_property_years, AK whatsapp_contact_link, AL whatsapp_group_link, AM transaction_type, AN property_subtype, AO city, AP posted_url, AQ posted_at, AR error_notes, AS meta_catalog_id, AT meta_catalog_status, AU source_group, AV inventory_locked.`

## Stage-2 deterministic contract

The completed `raw_message_text` is the only extraction source. Existing Sheet values are not extraction input.

### Direct fields

- `internal_property_type`: extract the explicit source field first. Accept common `:` or `-` label separators. Normalize to `Gated Community`, `Semi Gated`, or `Standalone`. If the explicit field is absent, semi-gated wording wins, then gated-community/society wording, otherwise Standalone.
- `society_name`: use the directly supplied society name. Strip presentation-only markdown. Placeholder-only values such as `*` or `-` count as blank. If blank, use the resulting location/locality.
- `landmark`: use the directly supplied landmark. Strip presentation-only markdown. Placeholder-only values such as `*` or `-` count as blank. If blank, use the resulting location/locality.
- `locality`: use explicit `Location`, `Locality`, or `Area`; a verified Maps locality may replace it.
- `property_subtype`: use explicit subtype and normalize supported aliases. If absent, default to Apartment only for a normal floor-bearing apartment-style record; standalone-property wording does not invent Apartment.
- `property_highlights`: preserve explicit highlights. Otherwise construct only factual deterministic fragments supported by the source, such as Utility area, supported subtype alias wording, multiple-unit/floor availability, or RK wording.
- `catalog_title`: construct a factual fallback from furnishing type, BHK, and location when blank. AI may rewrite wording only.
- `age_of_property_years`: populate only from an explicit/authoritative property-age fact; otherwise blank. Do not infer it from Maps.

### Core rules

- Decimal BHK values such as `2.5 BHK` are preserved.
- `G`/`Ground` floor normalizes to `0`.
- Carpet area defaults to 90% of built-up area when carpet area is blank.
- Maintenance is read directly from source. Numeric `k`/lakh values normalize to rupees; mixed values such as `2777 + Water` preserve the stated suffix. `Included` means maintenance `0` and `maintenance_included = Yes`.
- Deposit expressed in months is calculated from monthly rent.
- Semi Furnished and Fully Furnished receive deterministic furnishing defaults only when explicit furnishings are absent. Unfurnished source wording leaves furnish fields blank because the live Sheet has no Unfurnished value.
- `servant_room` is `Yes` only when explicitly stated; otherwise `No`.
- `pet_friendly` is `No` when pets are explicitly not allowed/not permitted/prohibited or equivalent no-pet wording is present. If no pet restriction is mentioned, the established last-resort default is `Yes`.
- `covered_parking` defaults to `1` for Gated Community and Semi Gated when no explicit covered-parking value exists. Standalone does not receive this default.
- `preferred_tenant_type` normalizes family variants to `Family` and anyone/open-for-all variants to `Open For All`.
- `bachelor_preference` is populated only from explicit source preference or the established female-bachelor rule.
- `internal_property_type` determines default `society_amenities`: Gated Community → exact gated Sheet combination; Semi Gated → exact semi-gated Sheet combination; Standalone → `-`.

## Review-status contract

`Needs Review` is reserved for deterministic validation errors or explicit AI conflicts after the deterministic gate. It is not a normal deterministic-extraction result.

Google Maps uncertainty is recorded as an issue but does not itself set `status = Needs Review`. `PARTIAL_MATCH`, `NEEDS_RUNTIME_VERIFICATION`, and `NOT_FOUND` may leave an otherwise valid deterministic record at `Pending`; downstream publication may separately require verified Maps data.

`intake_status = Processed` indicates Stage-2 processing completed. `status = Pending` is the expected result when deterministic validation passes and there is no AI conflict.

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

No conditional/row-dependent Sheet dropdown validation was observed for the inspected fields; their relationships are application/business dependencies.

## Stage-1/2 write boundary

Stage 1/2 writes are restricted to A:D, F:AO, and AU. E (`listing_state`), AP:AT (Housing/Meta downstream fields), and AV (`inventory_locked`) are protected.

## Verification boundary

Production Google Sheets access, the 48-column contract, write boundary, Google Maps access/application path, and live dropdown observations have been verified. Repository changes to deterministic rules must have regression coverage before live production extraction.
