# EFPS Business Context

This document is the canonical business reference for EFPS Internal Automations. It records established EFPS business rules, domain terminology, operating context, and business decisions that automation must defer to.

## Business purpose

EasyFind Property Solutions (EFPS) is a real-estate brokerage business operating primarily in East Bangalore, with strong activity around rental properties and related property services.

The automation exists to reduce repetitive operational work without silently changing EFPS business decisions.

Core business areas include rental brokerage, resale, property management, and additional property-related services.

Established website positioning:

> Find, Owner, Manager all under one roof.

## Core principles

- Business correctness takes precedence over technical capability.
- Preserve source facts; do not invent missing property information.
- Technical access is not business authorization.
- When a business rule is unclear, keep the decision with a human rather than inventing policy.
- Public-facing information must follow the intended EFPS disclosure rules.
- Prefer simple, controlled automation over unnecessary complexity.

## Inventory Phase-1 deterministic rules

Inventory property processing uses deterministic extraction and normalization before any optional AI step. The completed `raw_message_text` is the source of truth for extraction; existing Sheet values are not replay/extraction input.

### Direct source fields

- `internal_property_type` is extracted from an explicit source field when present and normalized only to `Gated Community`, `Semi Gated`, or `Standalone`. If no explicit value is supplied, the deterministic gating wording rule is used: explicit gated wording → Gated Community; explicit semi-gated wording → Semi Gated; otherwise → Standalone.
- `society_name` is taken directly from the source when supplied. If no society name is supplied, use the extracted `locality`/`Location` value as the fallback.
- `landmark` is taken directly from the source when supplied. If no landmark is supplied, use the extracted `locality`/`Location` value as the fallback.
- `locality` is extracted from an explicit `Location`/`Locality`/`Area` source field when available. A verified Google Maps result may then replace it with the verified Maps locality.
- `property_subtype` is taken directly from an explicit subtype/property-subtype source field when supplied and normalized through the canonical alias map. If absent and a normal floor-bearing apartment-style record has a floor, the fallback is `Apartment`. Standalone-property wording does not invent `Apartment`; the subtype remains blank unless explicitly supplied or mapped from a supported alias.

### Core deterministic rules

- Decimal BHK values such as `2.5 BHK` are preserved as `2.5 BHK`.
- `G`/`Ground` floor normalizes to `0`.
- When carpet area is blank and built-up area is known, carpet area is derived as 90% of built-up area.
- Maintenance is read directly from the source. Numeric `k`/lakh values are normalized to rupees; mixed values such as `2777 + Water` preserve the numeric amount and stated suffix rather than discarding the suffix. `Maintenance: Included` means maintenance `0` and `maintenance_included = Yes`.
- Deposit expressed in months is calculated from monthly rent.
- Semi Furnished and Fully Furnished have deterministic default furnishing sets; explicit source furnishings are preserved.
- Property subtype aliases normalize to the canonical subtype vocabulary.
- Society amenities are selected deterministically from `internal_property_type` when the source does not provide an explicit compatible amenity selection: Gated Community → the exact verified gated combination; Semi Gated → the exact verified semi-gated combination; Standalone → `-`. No unsupported amenity claims are invented.
- `covered_parking` defaults to `1` for Gated Community and Semi Gated when no covered-parking value is explicitly supplied. Standalone properties do not receive this default.
- `servant_room` is `Yes` only when the source explicitly states it; otherwise it defaults to `No`.
- `pet_friendly` uses the established last-resort rule: explicit `pets not allowed`/equivalent restriction → `No`; otherwise, including when the source is silent about pets, → `Yes`.
- Preferred tenant variants normalize to the live Sheet vocabulary: family variants → `Family`; anyone/open-for-all variants → `Open For All`. Specific `Family & Female`/female-bachelor wording also preserves the female-bachelor dependency by setting `preferred_tenant_type = Open For All` and `bachelor_preference = Female Only `.
- `bachelor_preference` is populated only from an explicit source preference or the established female-bachelor rule; no invalid `Not Allowed` value is generated.
- `property_highlights` remains deterministic and factual. Explicit source highlights are preserved. When blank, the fallback may include directly supported facts such as `Utility area`, supported subtype alias wording, multiple-unit/floor availability, or RK wording. It must not add unsupported marketing claims.
- `catalog_title` receives a deterministic factual fallback only when blank, based on available BHK/furnishing/location facts. Optional AI beautification may rewrite it later under the wording-only AI boundary.
- `age_of_property_years` is populated only from an explicit/authoritative property-age fact when available. It is not guessed from Maps, and otherwise remains blank.
- Deterministic processing fails closed rather than guessing missing property facts.

Google Maps is a technical Stage-2 capability, not a separate business stage. When a Maps URL is supplied/extracted, only a `VERIFIED` resolution is accepted for location fields; incomplete or failed resolution sends the property to review. Verified Maps locality also feeds the society/landmark fallback when those fields are blank.

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

## Domain terms

| Term | Meaning |
|---|---|
| EFPS | EasyFind Property Solutions |
| EasyFind | Common short form for EasyFind Property Solutions |
| Inventory | Structured EFPS property information used for operations and listings |
| Marketplace | Facebook Marketplace property listings |
| Ready To Occupy | Property immediately available |
| Open For All | Listing wording used when preferred tenants are anyone |
| Brokerage applicable | Required Marketplace disclosure |
| Property Listing | Public-facing property advertisement |
| WhatsApp Catalogue | EFPS catalogue organized by BHK rental categories |
| WhatsApp Group | `Flat & Flatmates – EasyFind Bangalore` |

## Geographic context

EFPS is primarily associated with East Bangalore. Repeatedly discussed areas include Harlur, Sarjapur Road, Outer Ring Road, Bellandur, Kasavanahalli, and HSR Layout. Relevant commercial/technology locations include Prestige Tech Park, RMZ Ecoworld, Ecospace, Cessna, Vaishnavi Tech Park, and Zepto HQ.

These are context, not an exclusive or permanent geographic boundary.

## Operational channels and systems

Known EFPS business/operational systems include Facebook Marketplace, Housing.com, MagicBricks, 99acres, MyGate, WhatsApp, Google Sheets, WhatsApp Catalogue, the EFPS website, and related automation infrastructure.

These systems are context. Their existence does not automatically authorize an agent to perform every available action.

## Current automation implementation scope

The repository has established shared technical capability boundaries for Cloudinary, credentials, Google Maps, Google Sheets, Slack, and WhatsApp/WhAPI. Inventory Phase 1 currently establishes the inbound/property-processing path through deterministic Stage 2 processing, Maps resolution, validation, and protected Sheet persistence boundaries. Future portal/catalogue publishing requires separate explicit implementation requirements and authorization.

## Open business decisions

Do not invent or silently resolve these until EFPS establishes them:

- complete approval matrix
- negotiation authority
- financial approval thresholds
- owner/client/tenant communication rules
- autonomous-vs-approval-required action boundaries
- complete geographic service area
- permanent posting-profile/contact mapping
- formal escalation hierarchy
- data-retention policy

## Canonical principle

EFPS Automations is an automation system serving the business, not an independent business operator.

When a rule exists, follow it. When a fact is known, preserve it. When a fact is missing, do not invent it. When authority is unclear, keep the decision with a human.
