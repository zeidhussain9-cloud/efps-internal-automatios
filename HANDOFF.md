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
- `Needs Review` is governed by `docs/NEEDS_REVIEW_CONTRACT.md`; non-blocking field gaps do not become property-processing blockers by themselves, but they must still remain deterministic and contract-valid.

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

For tenant eligibility:

- `preferred_tenant_type` has exactly two live Sheet values: `Family` and `Open For All`.
- `Family` -> `bachelor_preference` is blank.
- `Open For All` -> `bachelor_preference` defaults exactly to the Sheet dropdown value `Open for both`.
- Explicit valid source evidence for `Female Only ` or `Male Only` overrides the default.
- `Female Only ` includes the intentional trailing space present in the live Sheet dropdown and that exact value is the canonical contract.

## Google Maps state

`shared/google_maps/` is the dedicated reusable Maps capability. It owns deterministic URL grammar, short-link expansion, and normalized Maps resolution.

Supported source URL forms include `maps.app.goo.gl`, `goo.gl`, `maps.google.com`, `www.google.com/maps`, and `share.google`.

The 25-row production projection now passes the source-preservation contract for the tested Maps cases, including row 10 / `EF-2609-JCN1`, where the raw `https://share.google/oo7aBEUjVMGWUQzPm` value is projected unchanged into `google_maps_url`. The production projection contract gate reports all rows as PASS.

Do not re-open the Maps or society contracts unless a new projection demonstrates an actual regression against their contracts.

## Current verification truth before this hardening change

The merged baseline `176fcaf3b52d9899309e90f7f3556f97cb6dcc8d` had 74 passing and 4 failing regression tests. The failures were caused by stale test expectations and one validator/schema mismatch around the intentional trailing-space `Female Only ` Sheet value. The 25-row production projection and production projection contract gate both passed, but the full regression suite exposed the remaining bachelor contract inconsistency.

## Permanent hardening change in progress

This branch synchronizes the code, tests, and canonical documentation to the live Sheet contract rather than deleting or weakening the failing tests. The intended invariant is:

- schema allowed value = `Female Only `, `Male Only`, `Open for both`;
- normalized explicit Female Only source = exact `Female Only `;
- validator accepts that exact value;
- `Family` clears the dependent field;
- `Open For All` defaults to `Open for both`;
- explicit valid Male/Female source overrides the default;
- regression tests assert the exact live dropdown semantics.

## Safety boundary

No production Sheet write is part of the read-only projection audit. External Maps runtime verification and deterministic source projection are separate acceptance boundaries. No production credentials or secrets are part of this change set.
