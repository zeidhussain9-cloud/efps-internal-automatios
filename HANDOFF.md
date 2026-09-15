# EFPS Internal Automations — Current Handoff

## Current state

The current authorized implementation target is **Inventory Management Phase 1**. The workflow has three top-level stages: Stage 1 Initial/Webhook, Stage 2 Deterministic Extraction/Property Processing, and Stage 3 downstream boundary reserved for later consumers.

## Stage-2 implementation

- `extract.py` performs deterministic extraction from completed `raw_message_text`.
- Direct source fields accept `:`, `-`, `|`, and `=` separators and stop at newline/HTML breaks or the next timestamped WhatsApp message marker.
- Direct property type extraction is specific to property/gating classification labels; a generic `type:` match is intentionally avoided because it can capture unrelated text.
- `source_consistency.py` now performs a second source-first reconciliation pass for `internal_property_type`. Labelled canonical values and complete canonical phrases are recognized before normalization; unrelated `type:` text cannot classify a property.
- `normalize.py` applies deterministic business rules for direct-field fallbacks, pets, servant room, covered parking, amenities, maintenance, furnishing, subtype, tenant/bachelor dependency, highlights, title, and conservative property age.
- `pipeline.py` orchestrates extraction → source reconciliation → normalization → Maps → validation → optional AI wording/verification.
- `Needs Review` is reserved for deterministic validation errors or explicit AI conflicts. Maps `PARTIAL_MATCH`, `NEEDS_RUNTIME_VERIFICATION`, and `NOT_FOUND` are recorded as issues but do not themselves create `Needs Review`.
- `ai.py` remains advisory and cannot replace deterministic facts or bypass validation.

## Deterministic business rules now implemented

- Explicit `internal_property_type` is preferred and normalized to `Gated Community`, `Semi Gated`, or `Standalone`; common source separators are accepted.
- Source reconciliation recognizes labelled canonical property-type values and complete canonical phrases before fallback inference.
- If explicit property type is absent, semi-gated wording wins, then gated community/society/property wording, then explicit standalone wording, otherwise Standalone.
- `society_name` is direct when supplied; apartment/community/building-name aliases are accepted; placeholder-only values fall back to location/locality.
- `landmark` is direct when supplied; placeholder-only values fall back to location/locality.
- `pet_friendly` is `No` for explicit no-pet wording and `Yes` when no pet restriction is mentioned.
- `servant_room` is `Yes` only when explicitly stated; otherwise `No`.
- `covered_parking` defaults to `1` for Gated Community/Semi Gated when absent.
- `internal_property_type` controls exact Sheet-compatible default `society_amenities`.
- `property_subtype` is explicit/alias-normalized first; `Apartment` is only the normal floor-bearing fallback and is not invented for standalone wording.
- `property_highlights` and `catalog_title` remain deterministic and factual; no unsupported marketing facts are added.
- `age_of_property_years` is populated only from an explicit/authoritative fact and otherwise remains blank.
- Maintenance and month-based deposit rules remain deterministic. Mixed maintenance values such as `2777 + Water` are intentionally preserved as source facts; a numeric-only existing Sheet value is not treated as a model defect solely because it omits the source suffix.

## Model-run findings addressed

The previous 25-row read-only run exposed repeated differences in two distinct categories. First, many differences were expected because the selected Sheet rows remained at the pre-processed `Raw` state with Stage-1/2 fields blank. Existing Stage-2 Sheet values are deliberately not extraction input, so blank-versus-populated output is not a deterministic extraction failure. Second, nonblank conflicts such as `internal_property_type` and maintenance require source-first comparison rather than treating every projection difference as a failed update.

The property-type recurrence is now addressed by an explicit source reconciliation layer placed between extraction and normalization. It accepts canonical labelled values such as `Property Type: Semi Gated`, `Property Type - Gated Community`, and `Property Type = Standalone`, plus complete canonical phrases, while continuing to reject unrelated `type:` text.

Maintenance differences such as `2777` vs `2777 + Water` and `5000` vs `5000 + Water` remain source-preserving behavior unless a raw-source conflict proves otherwise. Decimal BHK corrections likewise remain source-derived until raw evidence establishes a different canonical value.

## Verification

Regression coverage now includes timestamp-delimited direct fields, inline timestamp delimiters, explicit semi-gated classification, canonical property-type labels/phrases, unrelated `type:` rejection, and mixed maintenance preservation.

The previous 25-row model run showed 17 Maps `PARTIAL_MATCH` issues but no Maps-induced `Needs Review` status. The current implementation keeps valid deterministic records at `Pending` while recording Maps uncertainty as an issue.

## Current open pointers

See `docs/OPEN_POINTERS.md`. Current unresolved items remain limited to Slack production runtime acceptance, exact `inventory_locked` vocabulary, and the decision/verification of the canonical WhAPI explicit User-Agent requirement.

## Safety boundary

No production Sheet write, WhAPI setting change, or real inventory message was performed as part of these changes. The next step is local synchronization followed by the same 25-row read-only model run; production extraction remains unauthorized until that verification is reviewed.
