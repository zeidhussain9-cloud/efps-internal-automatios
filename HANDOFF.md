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
- Maintenance requires maintenance-specific context, normalizes K/lakh units, independently evaluates inclusion, and preserves source qualifiers such as `+ Water`. `Included + Water` is represented as `0 + Water` with `maintenance_included = Yes`.
- Internal property type has exactly three business values: Gated Community, Semi Gated, and Standalone. Explicit negative gating is authoritative against generic positive wording.
- Numeric balcony extraction now covers explicit singular/plural source forms, including bare `Balcony` as one balcony.
- Explicit no-pet source wording is authoritative during final normalization; `Pets: Not Allowed` resolves to `No`.
- `📍 Landmark:` followed only by a Maps URL remains a blank landmark; the URL belongs to `google_maps_url`.
- Existing Sheet Stage-2 values are never deterministic extraction input.
- `Needs Review` is reserved for deterministic validation errors or explicit AI conflicts. Maps uncertainty remains informational under the current contract.

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

## Projection audit findings and fixes

The 2026-09-15 read-only projection against rows 2:26 established the following source-driven defects:

- Explicit `Pets: Not Allowed` was reaching projection as `No` only inconsistently because the extraction label regex and final normalization needed delimiter-safe negative handling. The final normalization now owns the source-grounded negative decision and covers `Not Allowed`/`Not Permitted`/`Prohibited`/`Banned` and equivalent no-pet forms.
- Singular `Balcony` was not matched by the numeric balcony extractor. The extractor now accepts integer/decimal counts and plural/singular spellings; normalization retains the bare-singular fallback to `1`.
- `Maintenance: Included` and `Maintenance: Included + Water` are handled by the canonical maintenance resolver; the latter now has an explicit regression assertion.
- Historical Sheet mismatches for `internal_property_type` are not automatically parser defects. Rows with explicit source gating evidence are expected to project that source-grounded value; rows without such evidence continue to use the declared `Standalone` fallback.
- `pincode` remains optional/non-blocking when Maps enrichment is not run by the read-only deterministic projection harness.
- `covered_parking` and `society_amenities` are dependent outputs of resolved `internal_property_type`, not independent extraction heuristics.

A pure regression harness is now at `tools/projection_regression_check.py` and is intended to run without production Sheet writes or live Maps calls.

## Verification status

The regression fix branch contains implementation, documentation, and source-shape regression coverage. It still requires local execution of the regression harness and the read-only production projection against the resulting merged `main` commit before production extraction is considered cleared.

## Safety boundary

No production Sheet write, WhAPI setting change, or real inventory message was performed as part of this fix cycle. Production extraction remains gated until the merged branch has been locally verified with the regression harness and the read-only model audit.