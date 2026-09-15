# Deterministic Extraction Review — 2026-09-15

## Evidence and version audit

The recurring 25-row projection artifact `Pasted markdown(20260915-094155).md` was executed from repository commit `98d657b`, not from the subsequently merged deterministic-fix commit `c096445` or current `main`. The artifact itself records `git rev-parse --short HEAD` as `98d657b` before the projection command. Therefore it cannot be used to judge the fixes that were later merged. This version mismatch explains why already-fixed source shapes kept reappearing in later manual classifications.

Current `main` is `60e167ad2d181f5444bb0f1df5b20e0f0ec84e0c`. The comparison from `98d657b` to current `main` contains 21 commits and includes changes to the deterministic extractor, resolver, normalizer, regression suite, and review documentation.

## Source-backed findings

### `pet_friendly`
The old projection at `98d657b` showed `Pets: Not Allowed` becoming `Yes`. Current normalization explicitly recognizes negative pet wording with `:`, `=`, or `-`, and negative evidence wins.

### `balconies`
Bare singular `Balcony` means one. Current normalization handles this when the extractor has no numeric count.

### `landmark` vs `google_maps_url`
A `📍 Landmark:` marker followed by a Maps URL must leave `landmark` blank and place the URL in `google_maps_url`. Current extraction and normalization implement that separation.

### `society_name` and `google_maps_url`
The structured EFPS marker grammar `📍 Name:` + Maps URL is now explicitly parsed. The marker name is the society/property candidate and the URL is the Maps candidate. Existing projection evidence already showed this working for records such as `Sonestaa Silver Oak` before the stale manual review was produced.

### `locality`
`Location:` is a deterministic source field. The 98d657b production artifact shows `Location: Thubarahalli, Whitefield` projecting to `locality = Thubarahalli, Whitefield`, so locality was not an extraction defect in that artifact. Maps replacement is a separate enrichment stage. Locality must not be downgraded merely because pincode/Maps enrichment was not run by the read-only projection harness.

### `pincode`
Pincode is enrichment-owned unless explicitly present in source. A blank value is valid and non-blocking. `validate.py` does not require a nonblank pincode, and the new production gate explicitly treats blank pincode as PASS.

### `maintenance`
The production projection already demonstrated correct numeric maintenance and `+ Water` preservation. Current resolver/normalizer also covers `Included` and `Included + Water` semantics. Maintenance should be graded against the source contract, not against historical Sheet formatting.

### `property_highlights`
Blank is valid when there is no explicit highlight and no supported deterministic fragment. A prior PARTIAL classification therefore did not establish a parser defect by itself.

## Genuine remaining defect found by this audit

### `internal_property_type`
The resolver previously ended with `return "Standalone"` when neither gating nor standalone evidence existed. That is a false fact: absence of evidence does not prove Standalone. This specifically misclassified `Prima Hilife`, whose raw source contains the community name but no gating keyword.

Independent current property evidence describes Prima Hi-Life as an exclusive gated community, and current rental inventory lists it with the `Gated Community` highlight. citeturn919629search0turn919629search6

**Permanent fix:**
1. Explicit source gating/standalone evidence remains highest priority.
2. Independently adjudicated community names are resolved through `src/community_property_types.py`.
3. `Prima Hi-Life`/`Prima Hilife` is explicitly registered as `Gated Community`.
4. Unknown/no-evidence communities now remain blank instead of being falsely labelled Standalone.
5. Downstream parking/amenity defaults do not invent a classification when the parent type is unresolved.

This preserves the three business values while separating an actual `Standalone` fact from an unresolved enrichment state.

## Regression-control fix

The old projection harness was observational: it dumped 48 fields but had no field-level assertion against the deterministic contract. This allowed a manually maintained 10/11-field classification to drift independently of code state.

Current repository adds:

- `tools/test_deterministic_edge_cases.py` for exact source-shape regressions;
- `tools/projection_regression_check.py` for pure deterministic regression assertions;
- `tools/production_projection_gate.py` for the live 25-row source-backed contract gate;
- CI execution of the deterministic regression tools.

The production gate treats valid blanks as valid results, including pincode and property highlights where the contract permits them, and checks selected previously-green fields for regression.

## Acceptance rule

The next live projection must be run from the actual fix commit/merged `main` SHA. Previous output from `98d657b` must not be reused as evidence for the current code. A clean result means the 11 previously recurring review labels are absent because their field contracts pass; it does **not** require every optional/enrichment field to be populated.
