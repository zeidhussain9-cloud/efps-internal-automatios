# EFPS Inventory Management

## Live mirror acceptance note — 2026-11-13 (recovery hardening)

The direct Housing Listings mirror is deployed with Supabase Edge Function v9 and the isolated Lambda. Full reconciliation confirms 104 active Notion pages and 104 matching Supabase snapshots, with no missing/orphaned/duplicate rows or semantic field mismatches. All 104 intake events are processed and contain the correct Listing ID. The reserved `source_group` and `inventory_locked` fields are blank; 43 populated `inventory_locked` values were cleared.

A 15-minute EventBridge reconciler checks all active Notion pages, queues only changed/restored pages, repairs event-to-listing mappings, and soft-deletes missing projections. Empty source results fail closed. A soft-deleted rented listing was successfully reactivated by the reconciler. Actual Notion `page.undeleted` delivery remains unobserved, but missed restore delivery is covered by the fallback. Async failures are retried and then retained in a 14-day SQS failure queue; structured Lambda logs retain 30 days.

The production dashboard remains at 104 listings (87 Available / 17 Rented Out). See `docs/NOTION_PROPERTY_INTAKE.md` for the live evidence and remaining separate raw-intake credential boundary.
- Source media gap (not a sync failure): 99/104 listings have Cloudinary image URLs. Five Rented Out pages have no image URL in Notion: `EF-2609-608J`, `EF-2609-22H0`, `EF-2609-VDWH`, `EF-2609-7JGF`, `EF-2609-MECJ`. The CRM mirrors the blank source values; no substitute images were invented.

## Intake entry points

- Existing Slack intake: /efps add-property collects details in a thread and writes through the canonical pipeline; /efps photos start associates operator-uploaded thread photos with the same Sheet row.
- Existing WhAPI intake: messages from the two configured inventory sender numbers are accumulated until the next exact NEW boundary; the canonical pipeline closes and processes the prior property session. The runtime allowlist comes from INVENTORY_SENDERS, with the two verified sender numbers as fallback.
- Canonical editor: Notion Housing Listings. Signed Page events mirror pages directly into the existing dashboard Supabase inventory. Supabase schema and Edge Function v9 and the isolated Lambda are deployed; the user confirms the existing webhook and all eight Page events remain selected. The backfill populated 104 active Notion-owned rows; see docs/NOTION_PROPERTY_INTAKE.md.
- Raw Notion Property Intake remains a compatibility pipeline that uses the existing Sheet/Cloudinary/Maps credentials and creates/updates Housing Listings pages. No AWS secret values are rotated or duplicated.

## Review-status boundary

`Needs Review` is not a normal result of deterministic extraction. A valid deterministic extraction remains `Pending` after `intake_status = Processed`.

`Needs Review` is used for deterministic validation errors, explicit AI conflicts, or a supplied Maps URL that cannot be VERIFIED. Unverified Maps candidates never supply locality/pincode and do not overwrite source values. A VERIFIED Maps locality/place name overrides conflicting source locality/society.

## Canonical Stage-2 pipeline

```text
raw_message_text
  -> source segmentation
  -> deterministic extraction
  -> canonical field resolution
  -> normalization/business rules
  -> validation
  -> Maps enrichment/verification
  -> optional AI verification/wording
```

`src/pipeline.py:deterministic()` is the authoritative deterministic processing boundary. `src/field_resolution.py` is the canonical resolver for BHK, maintenance, and internal property type. `normalize.py` consumes the resolved property type and does not independently classify it.

Existing Sheet Stage-2 values are never used as deterministic source evidence.

## Deterministic field contracts

- `BHK`: preserve integer and decimal values; later explicit BHK source corrections supersede earlier explicit values.
- `maintenance`: accept only maintenance-specific source context or the specific rent-plus-maintenance form; normalize K/lakh; preserve qualifiers such as `+ Water`; evaluate `maintenance_included` independently. `Included + Water` resolves to `0 + Water` and `Yes`.
- `internal_property_type`: exactly `Gated Community`, `Semi Gated`, or `Standalone`. Explicit source evidence is authoritative; explicit negative gating resolves to `Standalone`; specific/generic gating wording is used when present; known adjudicated communities may provide an explicit registry resolution. Absence of authoritative gating/standalone evidence remains unresolved/blank and must not be fabricated as `Standalone`.
- `balconies`: accept explicit numeric singular/plural balcony forms; bare `Balcony` is one balcony.
- `pet_friendly`: explicit no-pet wording such as `Pets: Not Allowed` is authoritative and resolves to `No`; absent restriction retains the established `Yes` fallback.
- `google_maps_url`: deterministic source URLs are extracted independently of network Maps enrichment.
- `landmark`: a `📍 Landmark:` marker followed only by a Maps URL remains blank; the URL belongs to `google_maps_url` and locality is never inherited into landmark.

## Dependency contract

- `internal_property_type -> society_amenities`
- `internal_property_type -> covered_parking` (blank-only default)
- `furnish_type -> flat_furnishings` (blank-only default)
- `preferred_tenant_type -> bachelor_preference`
- `maintenance -> maintenance_included`
- `built_up_area -> carpet_area` (blank-only fallback)
- `monthly_rent -> security_deposit` (month-based source form)

These are application/business dependencies; explicit source evidence for a dependent field remains authoritative where the contract permits it.

## Canonical source boundary

Stage 2 first segments `raw_message_text` into source-message units using `src/source_segments.py`. All labelled extraction operates inside those units. A recurring source-shape defect must be fixed at the canonical boundary or field contract and must include a regression fixture.

## Deterministic normalization/business rules

- `internal_property_type` determines the default exact Sheet-compatible `society_amenities` combination.
- Gated Community and Semi Gated default covered parking to `1` when blank.
- Semi/fully furnished receive default furnishing bundles only when explicit furnishings are blank.
- Family/open-for-all tenant variants normalize to live Sheet vocabulary; bachelor preference is handled by its declared dependency.
- `servant_room` defaults to `No` when not explicitly `Yes`.
- `pet_friendly` defaults to `Yes` only when no explicit no-pet restriction is present.
- `property_subtype`, title, highlights, location fallback, and property age follow the canonical source/data contracts.

## Stage-1/2 Sheets boundary

The inventory contract is 48 columns A:AV. Recurring Stage 1/2 updates are restricted to A:D and F:AO. The initial Stage-1 row insertion currently bootstraps E (`listing_state`) as `Available`; subsequent Stage-1/2 projections protect E. AP:AT are downstream-owned. AU and AV are reserved and must remain blank.

## Notion intake adapter

`src/notion_intake.py` has two paths. Raw Property Intake still claims in Supabase `crm_inventory_intake_events`, processes text/photos through the existing deterministic pipeline, writes the compatibility Housing_Listings Sheet row, and creates/updates the Housing Listings page. When a Housing Listings page is created or edited, the new path claims the same source page idempotently, allocates a stable Listing ID when needed, and upserts or soft-deletes the existing `public.crm_inventory_snapshot` row directly. The dashboard now includes `housing_notion` rows, and the compatibility Sheet sync cannot overwrite those rows. Long Maps URLs are omitted from captions and flagged; pet policy is not inferred. No WhatsApp message is sent.

The adapter does not operate on AU/AV or send WhatsApp messages. Its SAM endpoint and secret contract are documented in `docs/NOTION_PROPERTY_INTAKE.md`. The existing AWS stack/Lambda/API route and Supabase `notion-inventory-state` v9 are deployed. Full 104-page source/projection reconciliation and event-to-Listing-ID mapping passed. The user-confirmed eight Page event selections were not changed. Existing AWS secret ARNs were reused; no secret values were displayed or changed. The Notion path has no DynamoDB dependency. A 15-minute scheduled reconciler repairs missed changes/restores and soft-deletes missing pages; fallback restoration was live-tested. Actual Notion `page.undeleted` delivery remains unobserved. The signed-in dashboard showed the 104-row projection.

## Verification

Regression coverage includes canonical source segmentation, multi-candidate resolution, later corrections, decimal BHK, maintenance unit normalization/qualifiers/inclusion, positive/negative property-type evidence, singular/decimal balcony source forms, explicit pet negatives, Sheet-independence, dependent defaults, normalized maintenance validation, and Notion intake projection/idempotency boundaries. Production projection gating validates the committed deterministic path against rows 2–26 without Sheet-value feedback or writes; live external-system writes remain a separate acceptance boundary.
