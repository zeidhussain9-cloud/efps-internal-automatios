# Data Contracts

This is the canonical cross-module data ownership and contract reference for EFPS Internal Automations.

## Inventory contract

`shared/google_sheets/schema.py` is the single physical `Housing_Listings` contract: 48 columns A:AV in the latest supplied order. Each column records owner, top-level population stage, allowed values where verified, and declared dependencies. AU (`source_group`) and AV (`inventory_locked`) are reserved/dummy columns with no current owner or operational stage; both must remain blank.

The latest physical order is:

`A listing_id, B status, C intake_status, D internal_property_type, E listing_state, F onboarded_on, G raw_message_text, H locality, I society_name, J landmark, K pincode, L google_maps_url, M furnish_type, N BHK, O bathrooms, P balconies, Q floor_number, R total_floors, S built_up_area, T carpet_area, U monthly_rent, V maintenance, W maintenance_included, X security_deposit, Y preferred_tenant_type, Z bachelor_preference, AA pet_friendly, AB servant_room, AC covered_parking, AD open_parking, AE society_amenities, AF flat_furnishings, AG property_highlights, AH catalog_title, AI cloudinary_image_urls, AJ age_of_property_years, AK whatsapp_contact_link, AL whatsapp_group_link, AM transaction_type, AN property_subtype, AO city, AP posted_url, AQ posted_at, AR error_notes, AS meta_catalog_id, AT meta_catalog_status, AU source_group, AV inventory_locked.`

## Stage-2 deterministic contract

The completed `raw_message_text` is the only extraction source. Existing Sheet values are not extraction input.

### Canonical execution boundary

`modules/efps-inventory-mgmnt/src/pipeline.py:deterministic()` is the authoritative deterministic processing entry point used by Stage 2. It performs source extraction, resolves `internal_property_type` through `field_resolution.py`, and passes that canonical result explicitly into normalization. `normalize.py` must not independently rediscover or reclassify `internal_property_type`.

### Direct fields

- `internal_property_type`: resolve explicit source gating evidence first. Explicit negative gating resolves to `Standalone`. Specific/generic gated wording is accepted after explicit labelled evidence. Independently adjudicated community names may resolve through `src/community_property_types.py`. **No gating/standalone evidence is not proof of Standalone; unresolved type is represented as blank until an authoritative adjudication/enrichment source exists.**
- `society_name`: use the directly supplied society name. Also accept apartment/community/building-name labels. Structured `📍 Name:` markers are source anchors; `📍 Landmark:` and `📍 Location:` are not society names. Strip presentation-only markdown. Placeholder-only values such as `*` or `-` count as blank. If blank after source extraction/enrichment, use the resulting locality.
- `landmark`: use the directly supplied landmark. A `📍 Landmark:` marker followed only by a Maps URL remains blank. A Maps URL must never be stored as a landmark; the URL belongs to `google_maps_url`. Landmark does not inherit locality.
- `locality`: use explicit `Property Location`, `Location`, `Locality`, or `Area`. This is deterministic source extraction. A verified Maps locality may replace it later during the separate enrichment stage.
- `google_maps_url`: extract deterministic source URLs, including common short-link and Google Maps forms supported by the shared adapter. Read-only deterministic projection must not require network resolution.
- `pincode`: optional/enrichment-owned unless explicitly written in source. A blank pincode is a valid deterministic result and must not by itself create `Needs Review`.
- `property_subtype`: use explicit subtype and normalize supported aliases. `Duplex Villa` resolves to `Villa`; 1 RK/studio resolves to `Studio`; normal apartment-style records fall back to `Apartment`.
- `maintenance`: normalize explicit maintenance values and the specific `rent + maintenance` form. Preserve source qualifiers such as `+ Water`. `Included` means `0` plus `maintenance_included = Yes`; `Included + Water` means `0 + Water` plus `maintenance_included = Yes`.
- `property_highlights`: preserve explicit highlights. Otherwise construct only supported factual deterministic fragments. Blank is valid when no supported highlight is present.
- `balconies`: accept explicit numeric `Balcony`/`Balconies` forms; a bare singular `Balcony` is one balcony.
- `pet_friendly`: explicit no-pet wording is authoritative and resolves to `No`; explicit positive wording resolves to `Yes`; source silence uses the established `Yes` last-resort value.

### Canonical source-message parsing

Inventory sessions can concatenate multiple WhatsApp messages. `modules/efps-inventory-mgmnt/src/source_segments.py` is the canonical segmentation implementation. Labelled extraction operates inside source-message units so a field cannot consume a later source message.

### Canonical field resolution

`modules/efps-inventory-mgmnt/src/field_resolution.py` is the canonical candidate-resolution layer for BHK, maintenance, and internal property type. Extractors discover candidates; the resolver selects the authoritative source candidate; normalization canonicalizes that result. Existing Sheet values are never candidates.

For repeated source evidence, later explicit values supersede earlier explicit values. Explicit labelled/boolean evidence outranks generic wording. Explicit negative gating is authoritative against generic positive wording.

## Dependency graph

```text
raw_message_text
  |
  +--> BHK
  +--> maintenance --------> maintenance_included
  +--> internal_property_type --> society_amenities
  |                             |
  |                             +--> covered_parking (default only when blank)
  +--> furnish_type ----------> flat_furnishings (default only when blank)
  +--> built_up_area ----------> carpet_area (fallback only when blank)
  +--> monthly_rent -----------> security_deposit (when deposit is expressed in months)
  +--> preferred_tenant_type --> bachelor_preference
```

These are application/business dependencies. A dependent field may still have explicit source evidence; the parent controls only the documented fallback/default relationship.

## Review-status contract

`Needs Review` is reserved for deterministic validation errors or explicit AI conflicts after the deterministic gate. Google Maps uncertainty is recorded as an issue but does not by itself create `Needs Review`. Pincode absence alone is non-blocking. Unresolved internal property type is a data-quality/enrichment condition, not a fabricated `Standalone` value.

## Projection audit contract

`tools/inventory_model_test.py` is read-only and observational. It must be run against the exact repository commit under review.

`tools/production_projection_gate.py` is the fail-closed contract gate for the recurring production range. It validates the 11 previously recurring audit fields against source-backed rules, checks dependency outputs, and guards selected previously-green fields against regression. It does not compare deterministic correctness to persisted Sheet values.

The 11-field review is no longer a manually inferred "PARTIAL" list. A field is only a failure when its contract is violated. Valid blanks are accepted where the field is optional/enrichment-owned, including pincode and property highlights when no source highlight exists. Historical Sheet mismatches are separately adjudicated and never treated as parser evidence.

## Known community adjudications

`modules/efps-inventory-mgmnt/src/community_property_types.py` contains explicit community-level property-type facts that cannot be derived safely from a generic society-name pattern. The registry is deliberately small and evidence-driven. `Prima Hi-Life` is recorded as `Gated Community` based on independent project/property evidence; unknown communities must not be auto-classified as gated merely because they are apartments/societies.

## Verified live Sheet vocabulary

| Column | Field | Exact observed values |
|---|---|---|
| D | `internal_property_type` | `Gated Community`; `Semi Gated`; `Standalone` |
| M | `furnish_type` | `Fully Furnished`; `Semi Furnished` |
| Y | `preferred_tenant_type` | `Family`; `Open For All` |
| Z | `bachelor_preference` | `Female Only `; `Male Only`; `Open for both` |
| AE | `society_amenities` | `Security, Lift, CCTV, Power Backup`; `Club House, Lift, Gym, CCTV, Power Backup, Swimming Pool, Garden, Sports, Kids Area`; `-` |
| AF | `flat_furnishings` | `Wardrobe, Modular Kitchen, Geyser, Fan, Light`; `Wardrobe, Modular Kitchen, Geyser, Fan, Light, Fridge, Washing Machine, TV, Sofa, Bed, Dining Table` |

Column AA `pet_friendly` has no Sheet validation rule; observed/application values are `Yes` and `No`.

## Stage-1/2 write boundary

Stage 1/2 writes are restricted to A:D and F:AO. E (`listing_state`) and AP:AT (Housing/Meta downstream fields) are outside the Inventory write set. AU (`source_group`) and AV (`inventory_locked`) are reserved/dummy columns and are neither read as operational inputs nor written by Inventory Stage 1/2. Both must remain blank.

## Verification boundary

Production Google Sheets access, the 48-column contract, write boundary, Google Maps access/application path, and live dropdown observations have been verified. Repository changes to deterministic rules require regression coverage before live production extraction. The recurring production dataset must always be re-run from the commit that contains the fix under review; prior projection output is evidence of that earlier commit only.

## Lead audit/dashboard contract

Lead audit records use UTC timestamps for storage. Audit descriptions render those timestamps in IST.

Lead history is represented by Slack message/thread history rather than a persisted history modal. Lost-stage handling does not require a lost-reason modal or separate reason-submission flow.

Lead dashboard identity is discovered through Slack history. Dashboard state is not persisted in `DDB_SESSIONS`, and newly created dashboards are not pinned. Digest behavior follows the same Slack-history discovery/update/post contract.
