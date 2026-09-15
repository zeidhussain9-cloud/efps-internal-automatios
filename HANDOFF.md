# EFPS Internal Automations — Current Handoff

## Current state

The current authorized implementation target is **Inventory Management Phase 1**. The workflow has three top-level stages: Stage 1 Initial/Webhook, Stage 2 Deterministic Extraction/Property Processing, and Stage 3 downstream boundary reserved for later consumers.

## Stage-2 implementation

- `extract.py` performs deterministic extraction from completed `raw_message_text`.
- Direct source fields accept the established message label formats, including `:` and `-` separators. Presentation-only markdown is cleaned from direct values.
- `normalize.py` applies deterministic business rules for direct-field fallbacks, pets, servant room, covered parking, amenities, maintenance, furnishing, subtype, tenant/bachelor dependency, highlights, title, and conservative property age.
- `pipeline.py` orchestrates extraction → normalization → Maps → validation → optional AI wording/verification.
- `Needs Review` is reserved for deterministic validation errors or explicit AI conflicts. Maps `PARTIAL_MATCH`, `NEEDS_RUNTIME_VERIFICATION`, and `NOT_FOUND` are recorded as issues but do not themselves create `Needs Review`.
- `ai.py` remains advisory and cannot replace deterministic facts or bypass validation.

## Deterministic business rules now implemented

- Explicit `internal_property_type` is preferred and normalized to `Gated Community`, `Semi Gated`, or `Standalone`; common `:`/`-` source labels are accepted.
- `society_name` is direct when supplied; placeholder-only values fall back to location/locality.
- `landmark` is direct when supplied; placeholder-only values fall back to location/locality.
- `pet_friendly` is `No` for explicit no-pet wording and `Yes` when no pet restriction is mentioned.
- `servant_room` is `Yes` only when explicitly stated; otherwise `No`.
- `covered_parking` defaults to `1` for Gated Community/Semi Gated when absent.
- `internal_property_type` controls exact Sheet-compatible default `society_amenities`.
- `property_subtype` is explicit/alias-normalized first; `Apartment` is only the normal floor-bearing fallback and is not invented for standalone wording.
- `property_highlights` and `catalog_title` remain deterministic and factual; no unsupported marketing facts are added.
- `age_of_property_years` is populated only from an explicit/authoritative fact and otherwise remains blank.
- Maintenance and month-based deposit rules remain deterministic, including mixed maintenance suffix preservation and Included → maintenance `0`.

## Canonical sheet

`Housing_Listings` is exactly 48 columns A:AV. Stage-1/2 writes remain restricted to A:D, F:AO, and AU. E, AP:AT, and AV are protected.

## Verification

Regression coverage now includes direct fields with alternate separators, placeholder society/landmark fallback, and Maps partial-match status separation in `src/test_deterministic_regressions.py`.

The 25-row read-only model run showed 17 `Needs Review` rows caused solely by Maps `PARTIAL_MATCH`. This implementation removes that coupling: Maps uncertainty is now informational and does not turn a valid deterministic extraction into `Needs Review`.

## Current open pointers

See `docs/OPEN_POINTERS.md`. Current unresolved items are limited to Slack production runtime acceptance, exact `inventory_locked` vocabulary, and the decision/verification of the canonical WhAPI explicit User-Agent requirement.

## Safety boundary

No production Sheet write, WhAPI setting change, or real inventory message was performed as part of these code changes. The next step is local synchronization followed by the same 25-row read-only model run; production extraction remains unauthorized until that verification is reviewed.
