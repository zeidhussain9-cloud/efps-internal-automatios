# EFPS Internal Automations — Current Handoff

## Current state

The current authorized implementation target is **Inventory Management Phase 1**. The workflow has three top-level stages: Stage 1 Initial/Webhook, Stage 2 Deterministic Extraction/Property Processing, and Stage 3 downstream boundary reserved for later consumers.

## Stage-2 implementation

- `extract.py` discovers deterministic source facts from completed `raw_message_text`.
- `source_segments.py` is the canonical source-message boundary parser for concatenated WhatsApp inventory messages.
- `field_resolution.py` is the canonical candidate-resolution layer for BHK, maintenance, and internal property type.
- `pipeline.py` is the authoritative deterministic processing boundary and passes resolved internal property type explicitly into normalization.
- `normalize.py` consumes canonical resolved property type and must not independently reclassify it.
- BHK preserves decimals and later explicit corrections.
- Maintenance requires maintenance-specific context, normalizes K/lakh units, independently evaluates inclusion, and preserves source qualifiers such as `+ Water`.
- Internal property type has exactly three business values: Gated Community, Semi Gated, and Standalone. Explicit negative gating is authoritative against generic positive wording, while absence of evidence does not prove Standalone.
- Numeric balcony extraction covers explicit singular/plural source forms, including bare `Balcony` as one balcony.
- Explicit no-pet source wording is authoritative during final normalization.
- `📍 Landmark:` followed only by a Maps URL remains a blank landmark; the URL belongs to `google_maps_url`.
- Existing Sheet Stage-2 values are never deterministic extraction input.
- `Needs Review` is governed by `docs/NEEDS_REVIEW_CONTRACT.md`; non-blocking field gaps do not become property-processing blockers by themselves.

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

Explicit child source evidence remains authoritative where the field contract permits it.

## Google Maps state

`shared/google_maps/` is the dedicated reusable Maps capability. It owns deterministic URL grammar, short-link expansion, and normalized Maps resolution.

Supported source URL forms include `maps.app.goo.gl`, `goo.gl`, `maps.google.com`, `www.google.com/maps`, and `share.google`.

The latest 25-row projection provides direct acceptance evidence for the formerly failing Maps case: row 10 / `EF-2609-JCN1` contains `https://share.google/oo7aBEUjVMGWUQzPm` in the raw source and projects the exact same URL into `google_maps_url`; `SM ART Apartments` is simultaneously retained as `society_name`. The production gate no longer reports a Maps failure.

Do not re-open the Maps or society contracts unless a new projection demonstrates an actual regression against their contracts.

## Current deterministic blocker

The latest production gate reports 19 row failures, all from one dependency contract: `preferred_tenant_type = Open For All` with blank `bachelor_preference`. This is one field-level blocker, not 19 independent property-field defects.

The correct resolution is not to invent a bachelor preference. Either the source must contain a valid dependent value or the business contract must explicitly authorize a deterministic default. Until that rule is established, the dependent field remains unresolved and blocking.

## Verification status

The current main branch contains the Maps source-preservation hardening, regression coverage, and the canonical Needs Review contract. Local acceptance still requires the complete test suite and the 25-row read-only projection/gate to be run from this exact merged commit.

## Safety boundary

No production Sheet write is part of the read-only projection audit. External Maps runtime verification and deterministic source projection are separate acceptance boundaries.
