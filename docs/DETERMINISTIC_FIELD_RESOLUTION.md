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

Recognize integer and decimal BHK values, bedroom-labelled forms, and Studio/RK forms according to the Inventory source contract. Preserve decimal BHK values. Later explicit BHK messages supersede earlier explicit BHK values. Existing Sheet BHK values are never used as source evidence.

### Maintenance

Only maintenance-labelled values or the specific `rent + maintenance` form can create maintenance candidates. Normalize `K`/lakh amounts to rupees. Preserve a source qualifier such as `+ Water` and `Water Charges` because it is part of the source fact. `Included` maps to maintenance `0` and `maintenance_included = Yes`. A numeric maintenance amount by itself does not imply inclusion.

The production validation contract permits a normalized numeric maintenance amount with an optional source qualifier, e.g. `2777 + Water`. This keeps extraction source fidelity while maintaining a predictable stored shape.

### Internal property type

`internal_property_type` has exactly three allowed values:

- `Gated Community`
- `Semi Gated`
- `Standalone`

This is a business-field value set, not a dependency classification.

The field has one authoritative deterministic resolver in `src/field_resolution.py`. Its result is consumed by normalization; normalization must not independently rediscover or reclassify property type.

Source evidence precedence is:

- explicit property-type labels;
- explicit boolean gating labels;
- specific canonical phrases;
- explicit standalone wording;
- declared `Standalone` fallback only when no source evidence exists.

Explicit negative gating resolves to `Standalone` and remains authoritative against later generic positive wording.

`internal_property_type` drives the default `society_amenities` bundle and the covered-parking default; therefore it is a parent business decision with downstream dependencies.

## Dependency graph

The verified Inventory application dependency graph is:

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

`tools/inventory_model_test.py` is read-only. It compares deterministic Stage-2 projections against existing Sheet values without feeding those values back into extraction.

A populated Sheet mismatch is a **source conflict**, not proof that the model is wrong. It must be adjudicated against `raw_message_text` and the established contract. Blank Stage-2 cells becoming populated are expected projections. Lifecycle changes, formatting-only differences, populated conflicts, and protected-column changes remain separate categories.

The audit must fail closed while populated source conflicts or protected-column changes remain. It must never modify the production Sheet.

## Regression contract

Every production extraction/resolution defect must have a fixture for the exact triggering source shape. Regression coverage must include:

- source-message boundaries;
- multiple candidates and later explicit corrections;
- decimal BHK;
- maintenance unit normalization and qualifiers;
- maintenance inclusion with an amount;
- positive and negative gating evidence;
- Sheet-independence;
- dependent-value generation;
- validation of the normalized output shape.

## Non-goals

This layer does not write Google Sheets, resolve Maps, call AI, or own downstream publication state.
