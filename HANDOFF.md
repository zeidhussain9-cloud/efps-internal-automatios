# EFPS Internal Automations — Current Handoff

## Current state

The current authorized implementation target is **Inventory Management Phase 1**. The workflow has three top-level stages: Stage 1 Initial/Webhook, Stage 2 Deterministic Extraction/Property Processing, and Stage 3 downstream boundary reserved for later consumers.

## Stage-2 implementation

- `extract.py` discovers deterministic source facts from completed `raw_message_text`.
- `source_segments.py` is the canonical source-message boundary parser for concatenated WhatsApp inventory messages.
- `field_resolution.py` is the canonical candidate-resolution layer for BHK, maintenance, and internal property type.
- `pipeline.py` is the authoritative deterministic processing boundary and passes the resolved internal property type explicitly into normalization.
- `normalize.py` consumes canonical resolved property type and must not independently reclassify it.
- BHK preserves decimals and later explicit corrections.
- Maintenance requires maintenance-specific context, normalizes K/lakh units, independently evaluates inclusion, and preserves source qualifiers such as `+ Water`.
- Internal property type has exactly three business values: Gated Community, Semi Gated, and Standalone. Explicit negative gating is authoritative against generic positive wording.
- Existing Sheet Stage-2 values are never deterministic extraction input.
- `Needs Review` is reserved for deterministic validation errors or explicit AI conflicts. Maps uncertainty remains informational.

## Canonical dependency contract

```text
internal_property_type -> society_amenities
internal_property_type -> covered_parking (blank-only default)
furnish_type -> flat_furnishings (blank-only default)
preferred_tenant_type -> bachelor_preference
maintenance -> maintenance_included
built_up_area -> carpet_area (blank-only fallback)
monthly_rent -> security_deposit (month-based source form)
```

These are application/business dependencies. Explicit child source evidence remains authoritative where the field contract permits it.

## Model-run interpretation

`tools/inventory_model_test.py` is read-only. It separates expected blank projections, lifecycle projections, formatting-only differences, populated source conflicts, and protected-column changes. A populated Sheet mismatch is not by itself a parser defect; it must be adjudicated against `raw_message_text` and the canonical contract. The raw source remains authoritative for deterministic extraction.

## Historical 25-row conflict conclusion

The previously observed 17 populated conflicts are not a single parser failure:

- BHK conflicts contain explicit `2.5 BHK` source evidence while the existing Sheet contains `5 BHK`; these are source-vs-historical-Sheet conflicts.
- Maintenance conflicts include unit representation differences such as `3.7K` versus `3`, and intentional qualifier differences such as `2777` versus `2777 + Water`.
- Internal property type conflicts often occur because the existing Sheet contains a classification while the raw message does not state one; the deterministic contract therefore applies its declared fallback rather than importing the Sheet value.

No production Sheet values are silently overwritten by the deterministic model.

## Verification

Regression coverage includes source-boundary extraction, canonical resolution, later corrections, decimal BHK, maintenance units/qualifiers/inclusion, positive and negative gating, Sheet-independence, dependent defaults, and normalized maintenance validation.

## Safety boundary

No production Sheet write, WhAPI setting change, or real inventory message was performed as part of this implementation. Production extraction remains unauthorized until the complete repository test suite and the read-only model audit are verified against the final branch state.
