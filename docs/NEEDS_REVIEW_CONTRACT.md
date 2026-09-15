# Deterministic Needs Review Contract

## Purpose

`Needs Review` is reserved for uncertainty or contradiction in property facts that can materially change the listing's identity, location, economics, or tenant eligibility. Non-critical extraction gaps remain manageable unless another contract explicitly makes them blocking.

## Blocking property-detail fields

The initial blocking set is:

| Field | Why blocking |
|---|---|
| `internal_property_type` | Determines Gated Community / Semi Gated / Standalone behavior and dependent outputs. |
| `property_subtype` | Identifies the property class; explicit subtype evidence must not be overwritten by a fallback. |
| `BHK` | Core inventory identity. |
| `society_name` | Property identity; explicit source evidence has priority, then verified/location fallback. |
| `locality` | Core property location. |
| `google_maps_url` | Property/location reference; when supplied in source it must be preserved exactly. |
| `monthly_rent` | Core commercial term. |
| `maintenance` | Core recurring commercial term. |
| `maintenance_included` | Changes the meaning of the rent/maintenance terms. |
| `security_deposit` | Core commercial term. |
| `preferred_tenant_type` | Core tenant eligibility constraint. |
| `bachelor_preference` | Dependent tenant eligibility field; its value is determined by the parent unless explicit source evidence overrides it. |
| `pet_friendly` | Tenant eligibility/property restriction. |
| `furnish_type` | Core listing classification where explicitly supplied. |
| `built_up_area` | Core property-size fact when supplied. |
| `carpet_area` | Core property-size fact when supplied or deterministically derived. |
| `bathrooms` | Core physical property fact when supplied. |
| `floor_number` | Core physical property fact when supplied. |
| `total_floors` | Core building fact when supplied. |

## Non-blocking / manageable fields

The following remain manageable unless a separate contract makes them blocking: `pincode`, `landmark`, `balconies`, `covered_parking`, `open_parking`, `servant_room`, `society_amenities`, `property_highlights`, catalog/display fields, and enrichment-owned fields.

A non-blocking field must still be deterministic and contract-valid; `manageable` does not mean `free to invent`.

## Status rule

A property-processing run may become `Needs Review` because of a blocking property-detail field, a protected lifecycle/downstream violation, or a structural processing failure. A non-blocking blank alone must not force `Needs Review`.

## Google Maps contract

`google_maps_url` is source-owned during deterministic projection. If a supported Maps URL exists in `raw_message_text`, the exact source URL must be projected unchanged apart from removal of message wrappers/terminal punctuation that are not part of the URL. Network expansion and geocoding are separate runtime enrichment operations and must never be required for deterministic URL capture.

`GoogleMapsClient.extract_url()` is the single recognizer used by extraction and the production gate. Regression coverage must include the supported host families, source wrappers, terminal punctuation, and adjacent text boundaries.

## Dependency rule

`bachelor_preference` is dependent on `preferred_tenant_type`:

- `Family` -> blank dependent value is valid.
- `Open For All` -> default exactly to the Sheet dropdown value `Open for both`.
- Explicit valid bachelor source evidence wins over the dependency default, so `Female Only` or `Male Only` remains authoritative when explicitly supplied.

The canonical dropdown vocabulary is exactly `Female Only`, `Male Only`, and `Open for both`. No alternate spelling, trailing-space variant, or invented value is permitted.

## Governance

This document defines the blocking-status contract. Field-level extraction definitions remain in `docs/DETERMINISTIC_FIELD_RESOLUTION.md` and `docs/INVENTORY_SOURCE_EXTRACTION.md`. Repository operating rules remain in `GEMINI.md` and `CORE_STEERING.md`.
