# Inventory Source Extraction Contract

**Status:** Active

## Purpose

This document is the canonical contract for deterministic extraction from `raw_message_text` in Inventory Management Stage 2. It defines source boundaries; `docs/DETERMINISTIC_FIELD_RESOLUTION.md` defines candidate precedence and resolution.

## Source-of-truth rule

`raw_message_text` is the authoritative Stage-2 extraction source. Existing Stage-2 Sheet values are never extraction evidence and are never used to manufacture a deterministic result.

## Canonical processing boundary

All Inventory Stage-2 labelled extraction first uses `modules/efps-inventory-mgmnt/src/source_segments.py` to divide concatenated WhatsApp traffic into source-message units. A field must never consume content from a later source message.

Supported transport forms include bracketed timestamps, ISO-like timestamps, slash-date timestamps, newline-delimited messages, and inline pipe-delimited timestamped messages. The segmentation module contains no business rules.

## Extraction contract

1. Segment the raw source into canonical source-message units.
2. Discover field candidates within those units.
3. Resolve recurring multi-candidate fields through `src/field_resolution.py`.
4. Normalize the resolved source fact.
5. Validate the normalized record.
6. Use Maps only for the documented Stage-2 enrichment/verification step.
7. Treat unresolved ambiguity as a validation/runtime state rather than inventing a fact.

## Property-type evidence

`internal_property_type` supports exactly `Gated Community`, `Semi Gated`, and `Standalone`.

Accepted explicit evidence includes property-type labels and boolean gating labels. Negative boolean gating evidence is explicit evidence for `Standalone`. Specific canonical phrases may classify the field when no stronger explicit evidence exists. When no property-type evidence exists, the declared deterministic fallback is `Standalone`.

`internal_property_type` is resolved once by `src/field_resolution.py`. Normalization consumes the resolved value and does not independently classify the property.

## Maintenance evidence

Only maintenance-specific labels or the specific `rent + maintenance` pattern can create maintenance candidates. Numeric values with `K`/lakh units are normalized to rupees. Source qualifiers such as `+ Water` and `Water Charges` are preserved. `Included` is represented by maintenance `0` and `maintenance_included = Yes`; an amount alone does not imply inclusion.

## Other source rules

- Decimal BHK values such as `2.5 BHK` are preserved.
- Later explicit source corrections supersede earlier explicit values for recurring multi-candidate fields.
- Society, landmark, locality, subtype, highlights, age, tenant preference, bachelor preference, pet status, and servant-room source facts are extracted within source-message boundaries.
- Placeholder-only values are blank for normalization purposes.

## Regression requirement

Every production extraction/resolution defect must have a regression fixture for the exact triggering source shape. Current regression coverage must exercise segmentation, multi-candidate resolution, corrections, positive/negative gating, decimal BHK, maintenance units/qualifiers/inclusion, Sheet-independence, and normalized validation.

## Model-test interpretation

The read-only model audit compares deterministic Stage-2 projection with persisted Sheet values. Blank Stage-2 cells becoming populated are expected projections. A populated Sheet mismatch is a source conflict requiring adjudication; it is not permission to alter deterministic source rules to match historical values. The audit never writes the production Sheet.
