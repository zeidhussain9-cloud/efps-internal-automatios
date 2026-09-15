# EFPS Internal Automations — Current Handoff

## Current state

The current authorized implementation target is **Inventory Management Phase 1**. The workflow has three top-level stages: Stage 1 Initial/Webhook, Stage 2 Deterministic Extraction/Property Processing, and Stage 3 downstream boundary reserved for later consumers.

## Stage-2 implementation

- `extract.py` performs deterministic extraction from completed `raw_message_text`.
- `source_segments.py` is the canonical source-message boundary parser for concatenated WhatsApp inventory messages.
- Labelled direct fields are extracted one source unit at a time and therefore cannot consume a value from a later timestamped message.
- Direct property type extraction is specific to property/gating classification labels; a generic `type:` match is intentionally avoided.
- `source_consistency.py` performs source-first reconciliation for `internal_property_type` using the same canonical source-unit boundary.
- `normalize.py` applies deterministic business rules for direct-field fallbacks, pets, servant room, covered parking, amenities, maintenance, furnishing, subtype, tenant/bachelor dependency, highlights, title, and conservative property age.
- `pipeline.py` orchestrates extraction → source reconciliation → normalization → Maps → validation → optional AI wording/verification.
- `Needs Review` is reserved for deterministic validation errors or explicit AI conflicts. Maps `PARTIAL_MATCH`, `NEEDS_RUNTIME_VERIFICATION`, and `NOT_FOUND` are recorded as issues but do not themselves create `Needs Review`.
- `ai.py` remains advisory and cannot replace deterministic facts or bypass validation.

## Deterministic business rules now implemented

- Explicit `internal_property_type` is preferred and normalized to `Gated Community`, `Semi Gated`, or `Standalone`; common source separators are accepted.
- Boolean gating labels are explicit evidence; negative values do not classify a property as gated.
- Source reconciliation recognizes labelled canonical property-type values and complete canonical phrases within source-message boundaries.
- `society_name` is direct when supplied; apartment/community/building-name aliases are accepted; placeholder-only values fall back to location/locality.
- `landmark` is direct when supplied; placeholder-only values fall back to location/locality.
- `pet_friendly` is `No` for explicit no-pet wording and `Yes` when no pet restriction is mentioned.
- `servant_room` is `Yes` only when explicitly stated; otherwise `No`.
- `covered_parking` defaults to `1` for Gated Community/Semi Gated when absent.
- `internal_property_type` controls exact Sheet-compatible default `society_amenities`.
- `property_subtype` is explicit/alias-normalized first; `Apartment` is only the normal floor-bearing fallback and is not invented for standalone wording.
- `property_highlights` and `catalog_title` remain deterministic and factual; no unsupported marketing facts are added.
- `age_of_property_years` is populated only from an explicit/authoritative fact and otherwise remains blank.
- Maintenance and month-based deposit rules remain deterministic. Mixed maintenance values such as `2777 + Water` are intentionally preserved as source facts.

## Recurring extraction-failure prevention

The repository no longer treats timestamp handling as a field-specific regex concern. Canonical segmentation is a shared Inventory extraction primitive and is used by both direct field extraction and property-type reconciliation. Any future production extraction defect must add a regression fixture for the actual source-message shape before the fix is considered complete.

## Model-run interpretation

The prior 25-row read-only run contained many blank-Sheet versus populated-model differences because Stage-2 projection is intentionally computed without writing the Sheet. Nonblank Sheet conflicts such as property type, maintenance, and BHK require raw-source evidence before being labelled model defects. The canonical source extraction contract now requires the model test/report to distinguish expected blank-cell projection differences, populated-cell conflicts, formatting-only differences, and Maps verification issues.

## Verification

Regression coverage includes bracketed timestamps, inline timestamp delimiters, source-boundary isolation, explicit semi/gated classification, negative gating values, canonical property-type labels, and mixed maintenance preservation. CI now executes the complete Inventory test directory in addition to the Sheet contract and pipeline tests.

## Current open pointers

See `docs/OPEN_POINTERS.md`. Current unresolved items remain limited to the already-recorded runtime/governance items; no future downstream Stage-3 feature is treated as an open pointer for Inventory Phase 1.

## Safety boundary

No production Sheet write, WhAPI setting change, or real inventory message was performed as part of these changes. The next step is local synchronization followed by the 25-row read-only model run; production extraction remains unauthorized until that verification is reviewed.
