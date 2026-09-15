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

Explicit child source evidence remains authoritative where the field contract permits it.

## Google Maps state

`shared/google_maps/` is the dedicated reusable Maps capability. It owns deterministic URL grammar, short-link expansion, and normalized Maps resolution.

Supported source URL forms include `maps.app.goo.gl`, `goo.gl`, `maps.google.com`, `www.google.com/maps`, and `share.google`.

The 2026-09-15 audit currently leaves exactly one RED deterministic field: `google_maps_url`. All other deterministic-scope fields are GREEN; there are no YELLOW deterministic fields. The next read-only rows 2:26 projection must be run from the current merged `main` commit. Its result is the acceptance evidence for this remaining RED.

Do not re-open previously closed deterministic findings unless a new projection demonstrates an actual regression against their contracts.

## Verification status

Current merged `main` includes the Google Maps `share.google` extraction and production-gate alignment fixes. The implementation change is complete; deterministic acceptance is intentionally evidence-gated. The same 25-row read-only projection is the authoritative next check.

The accepted outcome is binary for this field:

- **PASS:** `google_maps_url` is populated correctly from source and the field moves RED -> GREEN.
- **FAIL:** the projection still violates the Maps URL contract and the field remains RED for targeted diagnosis.

A failed Maps test must not cause unrelated deterministic fields to be reclassified without evidence of their own regression.

## Safety boundary

No production Sheet write is part of the read-only projection audit. External Maps runtime verification and deterministic source projection are separate acceptance boundaries.
