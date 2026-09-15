# Deterministic Field Resolution

**Status:** Active

This document is the canonical Stage-2 contract for fields that require deterministic candidate discovery, precedence, resolution, and normalization.

## Pipeline contract

```text
raw_message_text
  -> canonical source segmentation
  -> candidate extraction
  -> deterministic field resolution
  -> business normalization
  -> deterministic validation
  -> Maps enrichment/verification
  -> optional AI verification
  -> wording-only AI beautification
```

Extraction discovers source candidates. Resolution selects the authoritative candidate. Normalization canonicalizes the selected result and applies declared business rules. Existing Sheet Stage-2 values are never extraction candidates. AI does not author deterministic facts.

## Source precedence

1. Explicit labelled source evidence.
2. Explicit boolean/negative evidence where the field supports it.
3. Specific deterministic wording.
4. Generic wording.
5. Declared fallback only when no source evidence exists.

When the same field is explicitly corrected in a later source message, the later explicit value wins. An explicit negative gating statement is authoritative and cannot be overridden by later generic positive wording.

## Field contracts

### BHK

Recognize integer and decimal BHK values, bedroom-labelled forms, and RK forms according to the Inventory source contract. Preserve decimal BHK values. A 1 RK listing normalizes to `1 RK`. Existing Sheet BHK values are never used as source evidence.

### Property subtype

The operational EFPS subtype vocabulary is:

- `Apartment` — normal apartment/flat/building inventory, including apartment properties whose internal property type is Gated Community or Semi Gated.
- `Villa` — villa inventory, including explicit compound wording such as `Duplex Villa`.
- `Studio` — reserved for 1 RK inventory.

The portal UI exposes additional categories (`Independent House`, `Duplex`, `Independent Floor`, `Penthouse`, `Farm House`), but EFPS normal operations primarily use Apartment, Villa, and Studio. Explicit supported subtype wording remains authoritative; aliases are canonicalized before fallback. A normal building must not be left blank merely because it lacks an explicit subtype label.

### Maintenance

Only maintenance-labelled values or the specific `rent + maintenance` form can create maintenance candidates. Normalize `K`/lakh amounts to rupees. If maintenance is included in rent, set `maintenance_included = Yes` and `maintenance = 0`. If maintenance is included and water charges are additional, set `maintenance_included = Yes` and `maintenance = Water Charges Additional`. A separately stated maintenance amount sets `maintenance_included = No`. Source qualifiers such as `+ Water` remain preserved for separately charged maintenance.

### Internal property type

`internal_property_type` has exactly three allowed values:

- `Gated Community`
- `Semi Gated`
- `Standalone`

Apartment subtype does not by itself choose between Gated Community and Semi Gated; the internal property type is resolved from explicit gating evidence or the declared standalone fallback. The field has one authoritative deterministic resolver in `src/field_resolution.py`. Its result is consumed by normalization; normalization must not independently rediscover or reclassify property type.

`Gated: Community` and `Semi Gated: Community` are valid positive source forms. Explicit negative gating is authoritative. If no gating or standalone evidence exists, the documented fallback remains `Standalone`; this is a declared business fallback, not a claim that the source explicitly said standalone.

`internal_property_type` drives the default `society_amenities` bundle and the covered-parking default; therefore it is a parent business decision with downstream dependencies.

### Society name, landmark, and Maps URL

EFPS source messages commonly use a structured marker such as:

```text
📍 Bren Avalon:
https://maps.app.goo.gl/...
```

The marker name is a society/property-name candidate and the URL is a `google_maps_url` candidate. A `📍 Landmark:` marker followed by a Maps URL must not store the URL as `landmark`; the URL belongs to `google_maps_url` and the landmark remains blank unless an actual landmark value is supplied.

`google_maps_url` is a deterministic source field because the URL is present in `raw_message_text`. Maps resolution is a separate enrichment step that may verify/replace locality and obtain pincode.

`society_name` may fall back to locality only after raw source extraction and Maps enrichment have had an opportunity to establish a society/property name. `landmark` never inherits locality.

### Parking

For `Gated Community` and `Semi Gated`, `covered_parking` defaults to `1` only when no covered-parking value is supplied. An explicit source value such as `2` remains authoritative. Standalone properties do not receive the covered-parking default. Open-parking values are populated from explicit source evidence; no unsupported parking inference is introduced.

### Pincode

Pincode is an enrichment field when it is not explicitly present in source text. A verified Maps result may supply it from the postal-code component. A blank pincode is non-blocking and must not by itself cause `Needs Review`.

## Dependency graph

```text
internal_property_type
        |
        +----> society_amenities
        |
        +----> covered_parking (default only when blank)

furnish_type
        |
        +----> flat_furnishings (default only when blank)

preferred_tenant_type
        |
        +----> bachelor_preference

maintenance
        |
        +----> maintenance_included

built_up_area
        |
        +----> carpet_area (fallback only when blank)

monthly_rent
        |
        +----> security_deposit (when deposit is expressed in months)
```

Dependency means downstream correctness depends on the parent decision; it does not mean the child can only ever be populated through the parent. Explicit child source evidence remains authoritative where the contract says so.

## Model audit contract

`tools/inventory_model_test.py` is read-only. It projects the exact deterministic Stage-2 path against existing Sheet rows without feeding Sheet values back into extraction and without writing to the Sheet.

A populated Sheet mismatch is a source conflict, not proof that the model is wrong. It must be adjudicated against `raw_message_text` and the established contract. Blank Stage-2 cells becoming populated are expected projections. Lifecycle changes, formatting-only differences, populated conflicts, and protected-column changes remain separate categories.

The audit must fail closed while unresolved source conflicts or protected-column changes remain. Pincode absence alone is not a validation failure.

## Regression contract

Every production extraction/resolution defect must have a fixture for the exact triggering source shape. Regression coverage must include:

- source-message boundaries;
- multiple candidates and later explicit corrections;
- decimal BHK and 1 RK;
- Apartment/Villa/Studio subtype rules;
- maintenance amount normalization;
- maintenance included and included-plus-water semantics;
- positive and negative gating evidence;
- `📍` society/property and landmark markers;
- Maps URL extraction without network access;
- Sheet-independence;
- dependent-value generation;
- non-blocking pincode absence;
- validation of the normalized output shape.

## Non-goals

This deterministic layer does not write Google Sheets, call network Maps resolution during projection, call AI, or own downstream publication state.
