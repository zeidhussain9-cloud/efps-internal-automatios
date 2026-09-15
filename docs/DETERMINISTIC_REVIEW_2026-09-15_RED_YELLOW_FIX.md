# Deterministic Extraction Review — 2026-09-15

## Current evidence state

The 2026-09-15 audit reviewed the 25-row Inventory projection for rows 2:26 and classified the 48 canonical fields. The current code-level acceptance state is:

- 35 deterministic-scope fields
- `google_maps_url`: **GREEN by current projection evidence**
- `society_name`: **GREEN by current projection evidence**
- `bachelor_preference`: **RED** for `Open For All` rows with no valid dependent value
- 0 deterministic YELLOW fields in the current targeted gate
- 13 SYSTEM / OUT OF SCOPE

Historical spreadsheet classifications that still show `google_maps_url` or `society_name` as RED/PARTIAL are stale relative to the current merged repository and latest projection evidence. They must not be used as current code truth.

## Closed deterministic findings

The audit cycle permanently hardened:

- explicit negative pet wording;
- bare singular `Balcony` and numeric/decimal balcony forms;
- maintenance inclusion and `+ Water` semantics;
- explicit positive and negative internal-property-type evidence;
- unresolved internal-property-type handling without inventing `Standalone`;
- community-name adjudication where independently established;
- society/property marker versus landmark separation;
- locality source extraction;
- dependent `society_amenities` and `covered_parking` behaviour;
- non-blocking pincode and property-highlight semantics;
- Sheet-independence of deterministic extraction;
- direct `Independent House` subtype resolution as a valid canonical subtype;
- Google Maps source URL extraction and exact source preservation, including `share.google`.

These findings are closed. They should not be reclassified unless a future projection demonstrates an actual regression against their contracts.

## Google Maps contract — GREEN

`google_maps_url` is source-owned during deterministic projection. A supported Maps URL present in `raw_message_text` must be captured without network access and preserved exactly apart from message wrappers or terminal punctuation that are not part of the URL.

The latest projection provides direct evidence for the formerly failing source form. Row 10 / `EF-2609-JCN1` contains the source URL `https://share.google/oo7aBEUjVMGWUQzPm` and the deterministic model projects that exact URL into `google_maps_url`. The same row preserves `SM ART Apartments` as `society_name`, proving the URL is not being swallowed by the marker parser.

The shared adapter remains the single recognizer, and regression coverage now includes supported host families, wrappers, terminal punctuation, and adjacent-text boundaries. Runtime short-link expansion/geocoding remains a separate network-dependent enrichment stage and is not required for deterministic URL capture.

## Society contract — GREEN

`society_name` resolution order is:

1. explicit society/apartment/community/building source evidence;
2. verified Maps/location enrichment when available;
3. ultimate fallback to the same resolved locality/location.

The latest row-10 evidence demonstrates that an explicit marker is preserved instead of falling back to locality.

## Remaining RED — `bachelor_preference`

`bachelor_preference` is a dependent field driven by `preferred_tenant_type`. Direct source evidence remains authoritative.

- `Family` → dependent value must be blank.
- `Open For All` → one of `Female Only`, `Male Only`, or `Open for both` is required.
- `Open For All` with a blank/invalid dependent value is a deterministic contract failure and is **RED**.

The current production gate reports 19 affected rows, but those failures represent one field-level dependency defect rather than 19 independent field defects. Do not invent a value merely to clear the gate.

## Property subtype adjudication

`Independent House` is a valid direct subtype result. It must remain `Independent House` when explicitly present in source text; it must not be overwritten by an Apartment fallback. `Duplex Villa` resolves to `Villa`.

## Dedicated Maps capability

`shared/google_maps/` is the canonical home for Maps-specific technical behaviour:

1. source URL extraction;
2. short-link expansion when runtime/network access exists;
3. Maps query derivation;
4. Geocoding resolution;
5. normalized resolution/confidence output.

Inventory remains responsible for business interpretation and field projection.

## Needs Review boundary

`docs/NEEDS_REVIEW_CONTRACT.md` is the canonical blocking-field contract. `Needs Review` is a property-truth gate, not a catch-all for optional, enrichment-owned, display, or downstream fields.

## Acceptance rule from this point

Do not reopen `google_maps_url` or `society_name` without fresh regression evidence. The next acceptance cycle should target the remaining `bachelor_preference` dependency and then rerun the complete suite plus the 25-row projection/gate from the exact merged `main` commit.

## Regression controls

The repository contains:

- `tools/test_deterministic_edge_cases.py` for exact source-shape regressions;
- `tools/projection_regression_check.py` for deterministic regression assertions;
- `tools/production_projection_gate.py` for the live 25-row contract gate;
- `tools/inventory_model_test.py` for the read-only full 48-field projection dump.
