# Data Contracts

## Authoritative current verified state — 2026-11-13

This section is the current verified checkpoint. Older dated figures below are historical and must not be treated as current production metrics.

- **Repository:** `zeidhussain9-cloud/efps-internal-automatios`
- **Active branches:** `main` and `crm-ui-dashboard` only. Their tracked trees were verified identical before this task release; final reconciliation is part of this release close.
- **Render:** latest `crm-ui-dashboard` deployment is LIVE; production health smoke passed.
- **Housing inventory mirror:** 104 active rows in `crm_inventory_snapshot`; latest verified sync timestamp `2026-11-12 21:45:01 UTC`.
- **Inventory validation:** 118 inventory-module tests passed in the 2026-11-13 rerun (87 Notion-intake tests); 130 combined inventory/webhook-routing tests passed; isolated SAM template/build validation passed.
- **CRM validation:** 139 unit/server tests passed; browser regression 1/1 passed.
- **SAM validation:** template validation, clean build, generated-template validation, Python compilation, and Lambda dependency packaging passed.
- **Subtype:** mandatory supported value; Apartment fallback only when no subtype evidence exists; Penthouse -> Apartment; conflicting/unsupported candidates remain unresolved and require Needs Review.
- **Maps:** preserve the exact original source URL. Only VERIFIED Maps results may replace conflicting locality/place name; unverified candidates do not overwrite data and route to Needs Review.
- **WhAPI inventory intake:** deployed EFPSWebhook is Active with live flags enabled; deployed code was last updated 2026-10-04 and routes the two dedicated inventory sender numbers through the NEW delimiter. The current repository webhook handler now uses the explicit INVENTORY_SENDERS allowlist rather than a parser business-property. The shared stack was not redeployed.
- **Slack inventory intake:** the existing /efps add-property flow collects property details in a thread, writes through the canonical Inventory pipeline to Housing_Listings, and uploads associated thread photos to Cloudinary; /efps photos start handles rows still missing photos.
- **Notion intake:** isolated AWS stack efps-notion-property-intake is deployed (CREATE_COMPLETE); Lambda efps-notion-intake is Active. Invalid signatures return HTTP 401; a correctly signed malformed event reaches page-ID validation (HTTP 400); Notion API read-only access to both databases returns HTTP 200. End-to-end processing is blocked by the invalid Sheets/Cloudinary/Maps runtime credentials; subscription and controlled acceptance remain pending.
- **Supabase ownership:** the existing Sheet-to-`crm_inventory_snapshot` sync path is unchanged; the Notion adapter writes only the canonical Sheet and relies on that existing sync path.
- **WhatsApp:** `whatsapp_post` is generated for Notion from explicit/verified v7.1 facts. The adapter does not send WhatsApp messages.

## Inventory contract

`shared/google_sheets/schema.py` is the single physical `Housing_Listings` contract: 48 columns A:AV in the latest supplied order. Each column records owner, top-level population stage, allowed values where verified, and declared dependencies.

The latest physical order is:

`A listing_id, B status, C intake_status, D internal_property_type, E listing_state, F onboarded_on, G raw_message_text, H locality, I society_name, J landmark, K pincode, L google_maps_url, M furnish_type, N BHK, O bathrooms, P balconies, Q floor_number, R total_floors, S built_up_area, T carpet_area, U monthly_rent, V maintenance, W maintenance_included, X security_deposit, Y preferred_tenant_type, Z bachelor_preference, AA pet_friendly, AB servant_room, AC covered_parking, AD open_parking, AE society_amenities, AF flat_furnishings, AG property_highlights, AH catalog_title, AI cloudinary_image_urls, AJ age_of_property_years, AK whatsapp_contact_link, AL whatsapp_group_link, AM transaction_type, AN property_subtype, AO city, AP posted_url, AQ posted_at, AR error_notes, AS meta_catalog_id, AT meta_catalog_status, AU source_group, AV inventory_locked.`

## Stage-2 deterministic contract

The completed `raw_message_text` is the only extraction source. Existing Sheet values are not extraction input.

### Canonical execution boundary

`modules/efps-inventory-mgmnt/src/pipeline.py:deterministic()` is the authoritative deterministic processing entry point used by Stage 2. It performs source extraction, resolves `internal_property_type` through `field_resolution.py`, and passes that canonical result explicitly into normalization. `normalize.py` must not independently rediscover or reclassify `internal_property_type`.

### Direct fields

- `onboarded_on`: formatted as human-readable IST datetime ("19 Sep 2026, 4:55 AM"). Stage 1 captures WhAPI epoch timestamp from the "NEW" boundary message and formats it immediately. This is a presentation field, not an extraction field.
- `internal_property_type`: resolve explicit source gating evidence first. Explicit negative gating resolves to `Standalone`. Specific/generic gated wording is accepted after explicit labelled evidence. The current resolver does not call a community registry; only explicit labels, boolean gating evidence and generic gated/standalone wording are used. **No gating/standalone evidence is not proof of Standalone; unresolved type is represented as blank until an authoritative adjudication/enrichment source exists.**
- `society_name`: use the directly supplied society name. Also accept apartment/community/building-name labels. Structured `📍 Name:` markers are source anchors; `📍 Landmark:` and `📍 Location:` are not society names. Strip presentation-only markdown. Placeholder-only values such as `*` or `-` count as blank. If blank after source extraction/enrichment, use the resulting locality.
- `landmark`: use the directly supplied landmark. A `📍 Landmark:` marker followed only by a Maps URL remains blank. A Maps URL must never be stored as a landmark; the URL belongs to `google_maps_url`. Current Phase 1 fills a blank landmark with the resolved locality as a final fallback.
- `locality`: use explicit `Property Location`, `Location`, `Locality`, or `Area`. This is deterministic source extraction. A verified Maps locality may replace it later during the separate enrichment stage.
- `google_maps_url`: extract deterministic source URLs, including common short-link and Google Maps forms supported by the shared adapter. Read-only deterministic projection must not require network resolution.
- `pincode`: optional/enrichment-owned unless explicitly written in source. A blank pincode is a valid deterministic result and must not by itself create `Needs Review`.
- `property_subtype`: required canonical field. Apartment is the deterministic fallback only when no subtype evidence exists; Penthouse normalizes to Apartment. Unsupported or conflicting subtype evidence remains unresolved and fails validation, setting `Needs Review`.
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

`Needs Review` is reserved for deterministic validation errors or explicit AI conflicts after the deterministic gate. Google Maps uncertainty is recorded as an issue but does not by itself create `Needs Review`. Pincode absence alone is non-blocking. Unresolved internal property type is a data-quality/enrichment condition, not a fabricated `Standalone` value. Unresolved or conflicting `property_subtype` is a validation error because subtype is mandatory; use Apartment only as the established no-evidence fallback, and normalize Penthouse to Apartment.

## Projection audit contract

`tools/inventory_model_test.py` is read-only and observational. It must be run against the exact repository commit under review.

`tools/production_projection_gate.py` is the fail-closed contract gate for the recurring production range. It validates the 11 previously recurring audit fields against source-backed rules, checks dependency outputs, and guards selected previously-green fields against regression. It does not compare deterministic correctness to persisted Sheet values.

The 11-field review is no longer a manually inferred "PARTIAL" list. A field is only a failure when its contract is violated. Valid blanks are accepted where the field is optional/enrichment-owned, including pincode and property highlights when no source highlight exists. Historical Sheet mismatches are separately adjudicated and never treated as parser evidence.

## Community classification boundary

The reviewed branch does not contain or invoke a community property-type registry. `internal_property_type` is resolved only from source labels, boolean gating evidence and generic gated/standalone wording in `field_resolution.py`. A community/society name alone does not imply Gated Community. Unresolved type remains blank and requires review.

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

## intake_status lifecycle

Column C (`intake_status`) tracks property processing through the full pipeline:

| Value | Stage | Trigger | Next Action |
|-------|-------|---------|-------------|
| `Raw` | Stage 1 | Webhook receives "NEW" + property text | Phase-1 deterministic extraction |
| `Processed` | Stage 2 | Phase-1 extraction + validation complete | Manual photo upload via `/efps photos start` |
| `Catalogue Ready` | Stage 3 | Photos saved + qualifies for catalogue | Meta catalogue creation via `/efps catalogue start` |
| `Published` | Stage 3 | Meta catalogue created successfully | Terminal state |

**Auto-flip rules:**
- `Raw` → `Processed`: Automatic when next "NEW" message triggers `_close()` and Phase-1 runs.
- `Processed` → `Catalogue Ready`: Automatic when `/efps photos start` → `done` saves photos AND property qualifies (status=Pending, has cloudinary URLs, listing_state≠Rented Out, no existing meta_catalog_id).
- `Catalogue Ready` → `Published`: Manual via `/efps catalogue start` → `go` when WhAPI catalogue creation succeeds.

## Stage-1/2 write boundary

Stage 1/2 writes are restricted to A:D and F:AO. E (`listing_state`), AP:AT (Housing/Meta downstream fields), AU (`source_group`), and AV (`inventory_locked`) are protected/reserved. AU/AV must remain blank.

## CRM cross-domain data contract

### Inventory

CRM reads may project the canonical 48 `Housing_Listings` fields. Read access does not grant write authority.

The live spreadsheet currently has a physical header discrepancy at column L (`w` vs canonical `google_maps_url`). This remains a controlled reconciliation item.

`listing_state` is present in the inventory data and currently has live values, but current Phase-1 code does not own/populate it. CRM write ownership remains pending explicit approval.

### Leads

The historical Leads Tracker exposes:
- `Leads`: 25 fields
- `Conversations`: 17 fields
- `Events`: 9 fields
- `Extraction Log`, `Findings`, `Priority Sharing`: reference/operational tabs

The legacy SQLite model contains `leads`, `conversations`, and `lead_lifecycle_events`. The current master runtime separately contains the DynamoDB lead/interactions/audit tables.

The uploaded extraction audit reports 6,064 extracted messages versus 23,454 conversation rows in `leads.db`. This is a material source discrepancy and prevents declaring the legacy SQLite database a clean canonical message store until the rows are reconciled against stable source message identifiers.

### CRM provenance

UI values must retain conceptual provenance:
- Verified source-backed
- Human-edited CRM
- AI-derived
- System state
- Synthetic/illustrative

AI-derived values never overwrite human-authoritative fields without an explicit review action.

## Verification boundary

Production Google Sheets access, the 48-column contract, write boundary, Google Maps access/application path, and live dropdown observations have been verified. Repository changes to deterministic rules require regression coverage before live production extraction. The recurring production dataset must always be re-run from the commit that contains the fix under review; prior projection output is evidence of that earlier commit only.

## CRM fictional AI proposal contract — 2026-09-27

The dedicated root `steering.md` instructs the hosted CRM model to return one JSON object with `bhk`, `location`, `budget`, `pets` and `uncertainties`. Unknown scalar values are `null`; uncertainties are a string array. The current adapter parses JSON or fenced JSON and returns the proposal for human Accept/Reject; it does not persist AI-derived values or assert property facts. The provider receives only fixed fictional pilot fixtures. Historical SQLite customer data and Housing_Listings inventory are separate sources and are not added to model context.
