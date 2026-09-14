# Data Contracts

This is the canonical cross-module data ownership and contract reference for EFPS Internal Automations.

## Inventory contract

`shared/google_sheets/schema.py` is the single physical `Housing_Listings` contract: 48 columns A:AV. Each column records owner, first-population stage, allowed values, and declared dependencies/interdependencies.

Verified legacy sources:
- `efps-platform/modules/efps-whapi-panel/src/schema.py` — older 47-column table.
- `efps-platform/docs/SHEET_CONTRACT.json` — newer verified 48-column A:AV contract.

The new repository follows the newer 48-column contract, including `inventory_locked` at AV. `listing_id` in A is immutable row identity.

## Population stages

- **intake:** listing identity, fixed company values, raw text, source metadata, and initial `Raw` state.
- **deterministic_extraction:** values read explicitly from `raw_message_text` only.
- **normalization:** safe formatting/default/mapping rules that do not invent property facts.
- **maps_resolution:** `locality`, `pincode`, and canonical `google_maps_url` from the shared Maps capability.
- **validation:** canonical structural/business safety gate; status becomes `Pending` or `Needs Review`.
- **ai_verification:** advisory contradiction check against exact source; conflicts cause `Needs Review` and never replace facts.
- **ai_beautification:** only `catalog_title` and `property_highlights` may be changed.
- **phase_2_media / phase_2_lifecycle:** intentionally not populated by Phase 1.
- **downstream:** AK:AO remain owned by Housing/Meta agents and are untouched by inventory Phase 1.

## Ownership
- `panel`: A–AJ plus AP–AV
- `housing_agent`: AK–AM
- `meta_catalog`: AN–AO

## Phase-1 raw contract

`NEW` opens a property session. All text messages until the next `NEW` are appended in order to `raw_message_text`, with timestamp/message-id metadata when available. Image/media binaries are not downloaded or serialized into raw text in Phase 1.

Deterministic extraction reads only that completed raw text. Existing canonical Sheet values are not extraction input, so replay cannot silently inherit stale values.

## Media / downstream

Cloudinary remains a reusable technical capability for Phase 2 media capture. Meta/Housing/website publishing is outside Phase 1.

## Documentation impact

Any change to the sheet contract requires synchronized review of the schema, affected module documentation, architecture/data contracts/infrastructure/open pointers, handoff, and all maintained root/docs guidance.
