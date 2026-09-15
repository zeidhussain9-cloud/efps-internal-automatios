# Deterministic Field Resolution

## Purpose

This document defines the permanent Stage-2 resolution architecture established after repeated Inventory Phase-1 model runs.

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

Extraction finds candidates. Resolution selects the authoritative source candidate. Normalization canonicalizes the selected value and applies only declared business rules. AI does not author deterministic facts.

## Source precedence

1. Explicit labelled source evidence.
2. Explicit boolean/negative evidence where the field supports it.
3. Specific deterministic wording.
4. Generic wording.
5. Declared fallback only when no source evidence exists.

When the same field is explicitly corrected in a later source message, the later explicit value wins. An explicit negative gating statement cannot be overridden by generic positive wording.

## Field contracts

### BHK

Recognize integer and decimal BHK values, bedroom-labelled forms, Studio, and RK. Preserve decimal BHK values. Later explicit BHK messages supersede earlier messages. Sheet values are never used as extraction input.

### Maintenance

Only maintenance-labelled values or the specific `rent + maintenance` source format can create maintenance candidates. Normalize `K`/lakh amounts to rupees. Preserve qualifiers such as `+ Water` and `Water Charges`. `Included` maps to maintenance `0` and `maintenance_included = Yes`. Unrelated numbers are never maintenance candidates.

### Internal property type

Use one canonical resolver for `Gated Community`, `Semi Gated`, and `Standalone`. Explicit property-type labels and boolean gating fields outrank generic text. Explicit negative gating resolves to `Standalone` and remains authoritative against later generic wording. If no explicit evidence exists, use the established deterministic fallback `Standalone`.

## Test contract

Regression tests must cover timestamp segmentation, multiple candidates, corrections, explicit negatives, decimal BHK, maintenance qualifiers, and Sheet-independence. The read-only model audit must distinguish expected blank projections, lifecycle projections, formatting-only differences, populated source conflicts, and protected-column changes.

## Non-goals

This layer does not write Google Sheets, resolve Maps, call AI, or own downstream publication state. Those remain separate responsibilities.
