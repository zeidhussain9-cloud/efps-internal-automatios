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

Inventory property processing uses deterministic extraction and normalization before any optional AI step. The completed `raw_message_text` is the source of truth for extraction; existing Sheet values are not extraction input.

### Direct source fields

- `internal_property_type`: extract the explicit source field first. Common `:` and `-` label separators are accepted. Normalize to `Gated Community`, `Semi Gated`, or `Standalone`. If absent, explicit semi-gated wording wins, then gated-community/society wording, otherwise Standalone.
- `society_name`: use the directly supplied society name. Presentation-only markdown and placeholder-only values such as `*` or `-` are blank. If missing, use the resulting location/locality.
- `landmark`: use the directly supplied landmark. Presentation-only markdown and placeholder-only values such as `*` or `-` are blank. If missing, use the resulting location/locality.
- `locality`: use explicit `Location`, `Locality`, or `Area`; verified Maps locality may replace it.
- `property_subtype`: explicit subtype is authoritative after supported alias normalization. If absent, `Apartment` is used only for a normal floor-bearing apartment-style record; standalone-property wording does not invent Apartment.
- `property_highlights`: preserve explicit source highlights. Otherwise generate only factual supported fragments such as Utility area, subtype alias wording, multiple-unit/floor availability, or RK wording.
- `catalog_title`: when blank, construct a factual fallback from furnishing type, BHK, and location. Optional AI can rewrite wording only.
- `age_of_property_years`: populate only from an explicit/authoritative age fact. Do not infer age from Maps; blank is valid.

### Core deterministic rules

- Decimal BHK values such as `2.5 BHK` are preserved.
- `G`/`Ground` floor normalizes to `0`.
- When carpet area is blank and built-up area is known, carpet area is derived as 90% of built-up area.
- Maintenance is read directly from source. Numeric `k`/lakh values are normalized to rupees. Mixed values such as `2777 + Water` preserve the stated suffix. `Included` means maintenance `0` and `maintenance_included = Yes`.
- Deposit expressed in months is calculated from monthly rent.
- Semi Furnished and Fully Furnished receive deterministic furnishing defaults only when explicit furnishings are absent. Unfurnished source wording leaves furnish fields blank because the live Sheet has no Unfurnished value.
- `servant_room` is `Yes` only when explicitly stated; otherwise `No`.
- `pet_friendly` is `No` when source explicitly says pets are not allowed/not permitted/prohibited or equivalent no-pet wording. If no pet restriction is mentioned, the established last-resort value is `Yes`.
- `covered_parking` defaults to `1` for Gated Community and Semi Gated when no covered-parking value is explicitly supplied. Standalone does not receive this default.
- `preferred_tenant_type` normalizes family variants to `Family` and anyone/open-for-all variants to `Open For All`.
- `bachelor_preference` is populated only from an explicit source preference or the established female-bachelor rule.
- `internal_property_type` determines default `society_amenities`: Gated Community → exact gated Sheet combination; Semi Gated → exact semi-gated Sheet combination; Standalone → `-`.

## Review-status business rule

`Needs Review` is not a normal deterministic-extraction outcome. A valid deterministic extraction remains `Pending` after processing. `Needs Review` is reserved for deterministic validation errors or explicit AI conflicts. Google Maps `PARTIAL_MATCH`, `NEEDS_RUNTIME_VERIFICATION`, or `NOT_FOUND` is an informational processing issue and does not itself create a review state; downstream publication may separately require verified Maps data.

## Google Maps

Google Maps is a technical Stage-2 processing capability, not a separate business stage. When verified, Maps may supply locality, pincode, and canonical Maps URL. It may also complete blank society/landmark fallbacks through the verified locality.

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

Inventory Phase 1 currently establishes the inbound/property-processing path through deterministic Stage-2 processing, Maps resolution, validation, and protected Sheet persistence boundaries. Future portal/catalogue publishing requires separate explicit implementation requirements and authorization.

## Canonical principle

EFPS Automations is an automation system serving the business, not an independent business operator. When a rule exists, follow it. When a fact is known, preserve it. When a fact is missing, do not invent it. When authority is unclear, keep the decision with a human.
