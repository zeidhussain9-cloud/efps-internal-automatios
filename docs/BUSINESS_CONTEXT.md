# EFPS Business Context

This document is the canonical business reference for EFPS Internal Automations. It records established EFPS business rules, domain terminology, operating context, and business decisions that automation must defer to.

## Business purpose

EasyFind Property Solutions (EFPS) is a real-estate brokerage business operating primarily in East Bangalore, with strong activity around rental properties and related property services.

The automation exists to reduce repetitive operational work without silently changing EFPS business decisions.

## Core principles

- Business correctness takes precedence over technical capability.
- Preserve source facts; do not invent missing property information.
- Technical access is not business authorization.
- Prefer simple, controlled automation over unnecessary complexity.

## Inventory Phase-1 deterministic rules

Inventory property processing uses deterministic extraction and normalization before any optional AI step. The completed `raw_message_text` is the source of truth for deterministic extraction. Existing Sheet values are not extraction input.

### Canonical deterministic field boundary

Stage 2 first segments `raw_message_text`, discovers candidates, resolves multi-candidate fields through `modules/efps-inventory-mgmnt/src/field_resolution.py`, then normalizes the resolved values. `internal_property_type` has one canonical resolver and exactly three business values: `Gated Community`, `Semi Gated`, and `Standalone`.

### Core deterministic rules

- Decimal BHK values such as `2.5 BHK` are preserved; later explicit source corrections supersede earlier values.
- Maintenance is read only from maintenance-specific source context or the specific rent-plus-maintenance format. `K`/lakh units normalize to rupees. Qualifiers such as `+ Water` are preserved. `Included` means maintenance `0` and `maintenance_included = Yes`; an amount alone does not imply inclusion.
- `internal_property_type` uses explicit source evidence first, then specific/generic deterministic gating wording, then the independently adjudicated community registry when available. Explicit negative gating evidence resolves to `Standalone`; absence of authoritative property-type evidence remains blank/unresolved and is never fabricated as `Standalone`.
- `internal_property_type` drives dependent business defaults: `society_amenities`, and the covered-parking default when parking is blank.
- `furnish_type` drives default `flat_furnishings` only when explicit furnishings are absent.
- `preferred_tenant_type` drives the `bachelor_preference` fallback/interpretation; explicit bachelor source evidence remains authoritative.
- `built_up_area` drives the carpet-area fallback at 90% when carpet area is blank.
- `monthly_rent` is used to calculate month-based security deposits when the source expresses the deposit in months.
- `society_name` preserves explicit source evidence, then uses the documented Maps/location opportunity, and finally the resolved locality as the last-resort identity fallback. `landmark` is never populated from locality and never stores a Maps URL.
- `servant_room` defaults to `No` only when the source does not explicitly state `Yes`.
- `pet_friendly` is `No` for explicit no-pet wording; otherwise the established last-resort value is `Yes`.
- `property_subtype`, highlights, title, and age follow the canonical source and normalization contracts.

## Dependency graph

```text
internal_property_type -> society_amenities
internal_property_type -> covered_parking (blank-only default)
furnish_type -> flat_furnishings (blank-only default)
preferred_tenant_type -> bachelor_preference
maintenance -> maintenance_included
built_up_area -> carpet_area (blank-only fallback)
monthly_rent -> security_deposit (month-based source form)
```

Dependencies describe downstream business correctness. They do not authorize the child to ignore explicit source evidence.

## Review-status business rule

`Needs Review` is reserved for deterministic validation errors or explicit AI conflicts. Maps uncertainty is an informational processing issue and does not by itself create `Needs Review`.

## Google Maps

Google Maps is a technical Stage-2 processing capability, not a separate business stage. During deterministic projection the exact source Maps URL is preserved without network access. During the separate enrichment step, a verified Maps result may supply locality, pincode, and a canonical Maps URL. It may also give the system another opportunity to complete a blank society-name fallback through the resolved locality. Landmark does not inherit locality.

## Marketplace business rules

1. Do not disclose the society name in a Facebook Marketplace listing unless explicitly requested.
2. Use a location-led title when appropriate.
3. Do not put floor or square footage in the title.
4. Use one clear location in the heading.
5. Keep listings short, crisp, natural, and broker-like.
6. Avoid exaggerated or generic marketing language such as "prime connectivity."
7. Rotate listing wording instead of repeatedly publishing identical copy.
8. Use factual nearby location/landmark/tech-office keywords when relevant and verified.
9. Use `Rent: ₹XX,XXX + maintenance` and do not disclose the maintenance amount in the Marketplace listing.
10. Include `Brokerage applicable.`
11. Put the EFPS WhatsApp group link above the contact number.
12. Use the contact number associated with the active posting profile; never assume the mapping is permanent.
13. For immediate availability use `Ready To Occupy.`
14. Do not mention future availability dates in Marketplace copy unless specifically requested.
15. When preferred tenants are anyone, use `Open For All.`
16. Do not introduce unnecessary negative restrictions.
17. Do not say `Pets not allowed.`
18. Use `Pet Friendly` only when pets are actually permitted.
19. Do not invent missing property facts.
20. When location research is required, verify the location and nearby points rather than guessing.

## Current automation implementation scope

Inventory Phase 1 establishes the inbound/property-processing path through deterministic Stage-2 processing, Maps resolution, validation, and protected Sheet persistence boundaries. Future portal/catalogue publishing requires separate explicit implementation requirements and authorization.

## Canonical principle

EFPS Automations is an automation system serving the business, not an independent business operator. When a rule exists, follow it. When a fact is known, preserve it. When a fact is missing, do not invent it. When authority is unclear, keep the decision with a human.
