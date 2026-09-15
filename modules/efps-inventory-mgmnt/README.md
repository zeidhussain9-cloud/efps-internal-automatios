# EFPS Inventory Management

## Inventory Phase-1 workflow

Inventory Phase 1 uses three top-level stages:

### Stage 1 — Initial / Webhook
The dedicated inventory listener receives the normalized WhAPI message. `NEW` opens a property session; subsequent messages from that listener are collected until the next `NEW`, which closes the property. A canonical `listing_id` is created for the property row, and the raw record is persisted with the source text and intake metadata.

### Stage 2 — Deterministic Extraction / Property Processing
The completed `raw_message_text` is the authoritative extraction source. The actual Stage-2 entry point is `process_closed_session()` in `src/pipeline.py`.

Its sequence is:

1. deterministic extraction
2. deterministic normalization/business rules
3. Google Maps resolution when a Maps URL is supplied/extracted
4. deterministic validation
5. optional AI verification/wording-only beautification after the deterministic gate

AI cannot replace deterministic source facts or bypass a deterministic validation failure.

Google Maps is a Stage-2 processing sub-step, not a separate top-level stage. Google Sheets persistence is transport/output, not a top-level stage.

### Stage 3 — Downstream Operations
Stage 3 is the downstream boundary for later consumers. It is not part of the current Inventory Phase-1 publishing implementation. Future Housing Portal and Meta Catalogue work requires explicit implementation requirements and authorization.

## Deterministic business-rule boundary

Deterministic processing is source-preserving and uses explicit EFPS rules rather than guessing property facts.

### Direct fields

- `internal_property_type`: read the explicit source field when supplied; normalize to `Gated Community`, `Semi Gated`, or `Standalone`. If absent, explicit semi-gated wording wins, explicit gated-community/society wording maps to Gated Community, and the fallback is Standalone.
- `society_name`: take the directly supplied society name. If missing, use the resulting location/locality as the fallback.
- `landmark`: take the directly supplied landmark. If missing, use the resulting location/locality as the fallback.
- `locality`: take explicit `Location`, `Locality`, or `Area` text when available. A verified Maps result may replace it with the verified locality; the society/landmark fallbacks are then reapplied if still blank.
- `property_subtype`: take the explicit source subtype and normalize supported aliases. If absent, default to `Apartment` only for a normal floor-bearing apartment-style record; standalone-property wording does not invent Apartment.
- `property_highlights`: preserve explicit source highlights. Otherwise generate only factual deterministic fragments supported by the source, such as Utility area, supported subtype alias wording, multiple-unit/floor availability, or RK wording.
- `catalog_title`: when blank, use a factual deterministic fallback from available furnishing type, BHK, and location. Optional AI beautification may rewrite only title/highlights under the wording-only AI boundary.
- `age_of_property_years`: only populate from an explicit/authoritative age fact. Do not infer age from Maps; blank is valid.

### Core rules

- `2.5 BHK` remains `2.5 BHK`; decimal BHK values are not truncated.
- Ground-floor `G`/`Ground` normalizes to `0`.
- Carpet area defaults to 90% of built-up area when carpet area is blank.
- Maintenance is read directly from source. Numeric `k`/lakh values are normalized to rupees; mixed values such as `2777 + Water` preserve the numeric amount and stated suffix. `Included` means maintenance `0` and `maintenance_included = Yes`.
- Deposit expressed in months is calculated from monthly rent.
- `Semi Furnished` and `Fully Furnished` receive deterministic furnishing defaults only when explicit furnishings are blank.
- Unfurnished source wording leaves `furnish_type` and `flat_furnishings` blank because the live Sheet has no Unfurnished dropdown value.
- `servant_room` is `Yes` only when explicitly stated; otherwise `No`.
- `pet_friendly` is `No` when pets are explicitly not allowed/not permitted/prohibited or equivalent no-pet wording is present. If no pet restriction is mentioned, the established last-resort value is `Yes`.
- `covered_parking` defaults to `1` for Gated Community and Semi Gated when no covered-parking value is supplied. Standalone does not receive this default.
- Preferred tenant variants normalize to the live Sheet vocabulary: family variants → `Family`; anyone/open-for-all variants → `Open For All`.
- `bachelor_preference` comes only from explicit source preference or the established female-bachelor rule; family without an explicit bachelor preference remains blank.
- `internal_property_type` deterministically controls default `society_amenities`: Gated Community → exact gated Sheet combination; Semi Gated → exact semi-gated Sheet combination; Standalone → `-` when amenities are blank.
- Explicit source values are not silently overwritten when they are valid and compatible with the canonical contract.

## Canonical Sheet-controlled fields

Live read-only verification established these exact current contracts:

| Column | Field | Contract |
|---|---|---|
| D | `internal_property_type` | `Gated Community`; `Semi Gated`; `Standalone` |
| M | `furnish_type` | `Fully Furnished`; `Semi Furnished` |
| Y | `preferred_tenant_type` | `Family`; `Open For All` |
| Z | `bachelor_preference` | `Female Only `; `Male Only`; `Open for both` |
| AA | `pet_friendly` | no Sheet dropdown; canonical application values `Yes`, `No` |
| AE | `society_amenities` | `Security, Lift, CCTV, Power Backup`; `Club House, Lift, Gym, CCTV, Power Backup, Swimming Pool, Garden, Sports, Kids Area`; `-` |
| AF | `flat_furnishings` | `Wardrobe, Modular Kitchen, Geyser, Fan, Light`; `Wardrobe, Modular Kitchen, Geyser, Fan, Light, Fridge, Washing Machine, TV, Sofa, Bed, Dining Table` |

D, M, Y, Z, AE, and AF use strict `ONE_OF_LIST` validation with custom UI enabled. No conditional/row-dependent dropdown validation was observed. The field relationships are application/business dependencies.

## Business field dependencies

- `internal_property_type` → `society_amenities`: Gated Community → exact gated combination; Semi Gated → exact semi-gated combination; Standalone → `-` when blank.
- `internal_property_type` → `covered_parking`: Gated Community/Semi Gated → `1` when blank.
- `furnish_type` → `flat_furnishings`: deterministic furnishing defaults when furnishings are blank.
- `preferred_tenant_type` → `bachelor_preference`: canonical tenant normalization plus explicit bachelor/female-bachelor handling; no invalid `Not Allowed` value is generated.
- `maintenance_included` ↔ `maintenance`: included means maintenance `0`.
- `monthly_rent` → `security_deposit`: month-based deposits are calculated from rent.

## Maps integration

`shared/google_maps` is the reusable technical Maps capability. Inventory consumes verified Maps results for `locality`, `pincode`, and canonical `google_maps_url`. A verified Maps locality is also used to complete blank society/landmark fallbacks.

The Stage-2 pipeline fails closed for Maps states other than `VERIFIED`: `PARTIAL_MATCH`, `NEEDS_RUNTIME_VERIFICATION`, `NOT_FOUND`, and unrecognized states cause `Needs Review`.

## Property boundary

`NEW` is the property-session delimiter. Every text message until the next `NEW` belongs to that property. Media are recognized/countable but their binary payloads are not downloaded or serialized into `raw_message_text` in the current Phase-1 implementation.

## Raw source

Text messages are preserved in `raw_message_text`, in arrival order with timestamp/message-id metadata when available. Duplicate webhook deliveries carrying the same message ID are ignored within the active session.

## Stage-1/2 Sheets boundary

The canonical inventory sheet is 48 columns A:AV. Stage 1/2 writes are restricted to A:D, F:AO, and AU. `listing_state` (E), Housing fields AP:AR, Meta fields AS:AT, and `inventory_locked` (AV) are protected from this path.

## Package layout

The implementation package is `modules/efps-inventory-mgmnt/src/` and contains `__init__.py`; `pipeline.py` uses package-relative imports. When running direct verification from the repository root, add `modules/efps-inventory-mgmnt` to `PYTHONPATH` and import `src.pipeline` rather than inventing an underscored package name from the hyphenated directory.

## Current verification state

- Deterministic rules validated against the current inventory sample before this contract pass: verified.
- Direct-field extraction, pet fallback, covered-parking default, tenant normalization, Standalone amenity default, subtype fallback, and deterministic title/highlight fallback now have regression coverage in `src/test_deterministic_contracts.py`.
- Google Sheets production read/write boundary: verified without unauthorized Stage-3 writes.
- Live Sheet dropdown/populated-value inspection: verified for D, M, Y, Z, AA, AE, AF.
- Google Maps direct API access and application path: previously verified.
- External AI runtime remains a separate runtime acceptance boundary when enabled.
