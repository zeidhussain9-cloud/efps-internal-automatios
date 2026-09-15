# Deterministic Extraction Review — 2026-09-15

## Historical review record

This file records the deterministic hardening cycle that culminated in the merged 2026-09-15 contract state. The earlier intermediate RED/YELLOW classifications below are historical findings and must not be mistaken for current repository status.

## Final accepted deterministic state for this review cycle

At the end of the hardening cycle, the repository's deterministic scope was:

- 35 deterministic-scope fields
- 35 GREEN
- 0 YELLOW
- 0 RED
- 13 SYSTEM / OUT OF SCOPE

The exact live bachelor dropdown contract is:

- `Female Only ` — intentional trailing space
- `Male Only`
- `Open for both`

`Family` clears `bachelor_preference`; `Open For All` defaults exactly to `Open for both`; explicit valid bachelor source evidence overrides the default.

## Findings closed during the cycle

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
- Google Maps source URL extraction and exact source preservation, including the observed `share.google` source form;
- exact bachelor dropdown vocabulary and dependency behavior.

These findings are closed. They should not be reclassified unless a future projection demonstrates an actual regression against the maintained contracts.

## Historical projection conflicts

The read-only projection also exposed populated historical Sheet differences in fields such as `BHK`, `maintenance`, `internal_property_type`, and `property_highlights`. Those are adjudicated as historical/source/display conflicts rather than parser failures because `raw_message_text` is the deterministic source of truth. Deterministic rules must not be changed merely to reproduce stale persisted Sheet values.

## Verification evidence

The final merged hardening state was validated by the repository regression suite and the 25-row read-only production projection/contract gate. The gate is observational and performs zero Sheet writes. Live extraction/write execution remains a separate runtime acceptance boundary.

## Regression controls

The repository contains:

- `tools/test_deterministic_edge_cases.py` for exact source-shape regressions;
- `tools/projection_regression_check.py` for deterministic regression assertions;
- `tools/production_projection_gate.py` for the live 25-row source-backed contract gate;
- `tools/inventory_model_test.py` for the read-only full 48-field projection dump;
- `tools/repository_audit.py` for repository-wide text line counts and selected contract-drift checks.

## Governance

This is a dated review record, not the canonical field contract. Current field semantics belong in `docs/DETERMINISTIC_FIELD_RESOLUTION.md`, source-boundary rules belong in `docs/INVENTORY_SOURCE_EXTRACTION.md`, cross-module semantics belong in `docs/DATA_CONTRACTS.md`, and current unresolved items belong in `docs/OPEN_POINTERS.md`.
