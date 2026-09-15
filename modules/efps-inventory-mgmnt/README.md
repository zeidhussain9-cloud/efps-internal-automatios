# EFPS Inventory Management

## Review-status boundary

`Needs Review` is not a normal result of deterministic extraction. A valid deterministic extraction remains `Pending` after `intake_status = Processed`.

`Needs Review` is reserved for a deterministic validation error or an explicit AI conflict after the deterministic gate. Google Maps `PARTIAL_MATCH`, `NEEDS_RUNTIME_VERIFICATION`, or `NOT_FOUND` is recorded as an issue but does not by itself change `status` to `Needs Review`.

## Canonical source extraction boundary

Stage 2 first segments `raw_message_text` into source-message units using `src/source_segments.py`. All labelled direct-field extraction must operate inside those units. This prevents a field in one WhatsApp message from consuming a value from a later message and prevents fixes from depending on one particular timestamp/line representation.

The canonical detailed contract is `docs/INVENTORY_SOURCE_EXTRACTION.md`.

## Deterministic direct-field rules

- `internal_property_type`: read the explicit source field when supplied; accept common `:` or `-` label separators and normalize to `Gated Community`, `Semi Gated`, or `Standalone`. Boolean gating labels are explicit evidence; negative boolean values do not classify a property as gated. If absent, explicit semi-gated wording wins, explicit gated-community/society wording maps to Gated Community, otherwise Standalone.
- `society_name`: take the directly supplied society name. Markdown decoration and placeholder-only values such as `*` or `-` are treated as blank. If missing, use the resulting location/locality.
- `landmark`: take the directly supplied landmark. Markdown decoration and placeholder-only values such as `*` or `-` are treated as blank. If missing, use the resulting location/locality.
- `locality`: take explicit `Location`, `Locality`, or `Area`. Verified Maps locality may replace it.
- `property_subtype`: take explicit subtype and normalize supported aliases. If absent, default to `Apartment` only for a normal floor-bearing apartment-style record; standalone wording does not invent Apartment.
- `property_highlights`: preserve explicit highlights; otherwise generate only factual fragments supported by source, such as Utility area, subtype alias wording, multiple-unit/floor availability, or RK wording.
- `catalog_title`: when blank, construct a factual title from furnishing type, BHK, and location. AI may rewrite wording only.
- `age_of_property_years`: populate only from an explicit/authoritative age fact; otherwise blank.

## Core deterministic rules

- Decimal BHK such as `2.5 BHK` is preserved.
- `G`/`Ground` floor becomes `0`.
- Carpet area defaults to 90% of built-up area when blank.
- Maintenance is read directly; numeric `k`/lakh values become rupees; mixed values such as `2777 + Water` preserve the suffix. `Included` means maintenance `0` and `maintenance_included = Yes`.
- Month-based deposits are calculated from monthly rent.
- Semi/fully furnished receive deterministic furnishing defaults only when explicit furnishings are blank.
- Unfurnished source wording leaves furnish fields blank because the live Sheet has no Unfurnished value.
- `servant_room`: Yes only when explicitly stated; otherwise No.
- `pet_friendly`: explicit no-pet wording means No; silence means Yes as the established last-resort rule.
- `covered_parking`: default 1 for Gated Community/Semi Gated when not explicitly supplied; no default for Standalone.
- `internal_property_type` selects exact Sheet-compatible default `society_amenities`: Gated Community → `Club House, Lift, Gym, CCTV, Power Backup, Swimming Pool, Garden, Sports, Kids Area`; Semi Gated → `Security, Lift, CCTV, Power Backup`; Standalone → `-`.
- Preferred tenant variants normalize to `Family` or `Open For All`; bachelor preference is populated only from explicit source preference or the established female-bachelor rule.

## Stage-2 sequence

1. canonical source-message segmentation
2. deterministic extraction
3. deterministic normalization/business rules
4. Google Maps resolution when supplied/extracted
5. deterministic validation
6. optional AI verification/wording-only beautification

Maps is a Stage-2 sub-step, not a top-level stage. Google Sheets persistence is transport/output.

## Stage-1/2 Sheets boundary

The inventory contract is 48 columns A:AV. Stage 1/2 writes are restricted to A:D, F:AO, and AU. E, AP:AT, and AV remain protected.

## Verification

Source-boundary extraction, direct-field extraction, placeholder fallbacks, pet fallback, covered-parking default, tenant normalization, amenity defaults, subtype fallback, title/highlight fallback, and Maps status separation have regression coverage in the Inventory tests. The canonical source-shape rule requires a regression fixture for every production extraction defect. External AI runtime remains a separate acceptance boundary.
