# Deterministic Extraction Review — 2026-09-15

## Current evidence state

The 2026-09-15 audit reviewed the 25-row Inventory projection for rows 2:26 and classified the 48 canonical fields. The current control state is:

- 35 deterministic-scope fields
- 32 GREEN
- 0 YELLOW
- 3 RED: `google_maps_url`, `society_name`, `bachelor_preference`
- 13 SYSTEM / OUT OF SCOPE
- Production acceptance remains blocked until the current-commit contract gate passes

Historical Sheet-value differences were adjudicated against authoritative `raw_message_text`; they are not automatically deterministic defects.

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
- direct `Independent House` subtype resolution as a valid canonical subtype.

These findings are closed. They should not be reclassified unless a future projection demonstrates an actual regression against their contracts.

## RED: `society_name`

`society_name` is an interdependent required projection when a usable location exists. The resolution order is:

1. explicit society/apartment/community/building source evidence;
2. verified Maps/location enrichment when available;
3. ultimate fallback to the same resolved locality/location.

If the resulting location exists and `society_name` remains blank, that is a deterministic contract failure and is **RED**. A blank is not a permissible Yellow outcome in that situation.

## RED: `bachelor_preference`

`bachelor_preference` is a dependent field driven by `preferred_tenant_type`. Direct source evidence remains authoritative.

- `Family` → dependent value must be blank.
- `Open For All` → dependent value must be one of `Female Only`, `Male Only`, or `Open for both`.
- `Open For All` with a blank/invalid dependent value is a deterministic contract failure and is **RED**.

The validator and production gate now enforce this dependency rather than allowing an unjustified blank to pass silently.

## RED: `google_maps_url`

The remaining Maps failure is treated as an end-to-end source-preservation contract, not a temporary test adjustment.

The deterministic extractor must recognize the supported Google Maps URL families from `raw_message_text`, preserve the source URL through deterministic projection, and expose one canonical recognizer through `GoogleMapsClient.extract_url()`. Runtime short-link expansion/verification remains a separate network-dependent stage.

The shared Maps adapter has been hardened to handle source-message wrappers and terminal punctuation without changing the underlying URL. A regression test covers `share.google` and exact source preservation.

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

## Acceptance rule from this point

The control matrix is intentionally frozen around the current three-RED state until new evidence arrives. The next rows 2:26 read-only projection must use the current merged `main` commit.

Valid promotion requires all three RED contracts to pass without reopening unrelated GREEN fields:

- `google_maps_url`: exact source URL is projected from raw source;
- `society_name`: explicit source wins, otherwise the ultimate location fallback is populated when location exists;
- `bachelor_preference`: dependent contract is satisfied for the resolved preferred tenant type.

## Regression controls

The repository contains:

- `tools/test_deterministic_edge_cases.py` for exact source-shape regressions;
- `tools/projection_regression_check.py` for deterministic regression assertions;
- `tools/production_projection_gate.py` for the live 25-row contract gate;
- `tools/inventory_model_test.py` for the read-only full 48-field projection dump.

The primary next audit remains `inventory_model_test.py --start-row 2 --end-row 26`. It must be executed against the current merged `main` before changing any RED field to GREEN.
