# EFPS Inventory Management

## Intake entry points

- Existing Slack intake: /efps add-property collects details in a thread and writes through the canonical pipeline; /efps photos start associates operator-uploaded thread photos with the same Sheet row.
- Existing WhAPI intake: messages from the two configured inventory sender numbers are accumulated until the next exact NEW boundary; the canonical pipeline closes and processes the prior property session. The runtime allowlist comes from INVENTORY_SENDERS, with the two verified sender numbers as fallback.
- Notion intake: a separate signed Connection webhook queues a Notion page for the same canonical pipeline. The endpoint is deployed but currently blocked by invalid Sheets/Cloudinary/Maps runtime credentials; see docs/NOTION_PROPERTY_INTAKE.md.

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

`src/notion_intake.py` is the Notion intake adapter. It fetches the submitted Notion page, claims it idempotently in Supabase `crm_inventory_intake_events` through the `notion-inventory-state` Edge Function, persists the raw record to the canonical Housing_Listings Sheet, downloads supported Notion-hosted photo attachments, uploads them through the shared Cloudinary helper, and delegates all property processing to `pipeline.process_closed_session()`. It then generates the v7.1 `whatsapp_post` from explicit/verified facts, creates/updates the Housing Listings Notion page, and writes intake status, Listing ID, notes, processed timestamp, and relation back to the intake page. Long Maps URLs are omitted from captions and flagged; pet policy is not inferred. No WhatsApp message is sent.

The adapter does not implement a second extraction engine, operate on AU/AV, or send WhatsApp messages. Its SAM endpoint and required secret contract are documented in `docs/NOTION_PROPERTY_INTAKE.md`. The isolated AWS stack is deployed (`efps-notion-property-intake`, `ap-southeast-2`) and the Lambda/API route is active. The Notion path has no DynamoDB dependency. Supabase idempotency claim/replay is verified. Notion read/write probes for both databases passed. Valid Sheets, Cloudinary, and Maps credentials were verified in local Keychain, but the AWS Secrets Manager copies are still `{}`/placeholders; the Notion Connection webhook subscription and full controlled acceptance test remain pending. See `docs/NOTION_PROPERTY_INTAKE.md` for the exact endpoint and remaining gates.

## Verification

Regression coverage includes canonical source segmentation, multi-candidate resolution, later corrections, decimal BHK, maintenance unit normalization/qualifiers/inclusion, positive/negative property-type evidence, singular/decimal balcony source forms, explicit pet negatives, Sheet-independence, dependent defaults, normalized maintenance validation, and Notion intake projection/idempotency boundaries. Production projection gating validates the committed deterministic path against rows 2–26 without Sheet-value feedback or writes; live external-system writes remain a separate acceptance boundary.