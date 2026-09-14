# EFPS Business Context

This document is the business brain of EFPS Internal Automations. It records established EFPS business rules and domain context that automation must defer to.

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