# EFPS Inventory Management

## Review-status boundary

`Needs Review` is not a normal result of deterministic extraction. A valid deterministic extraction remains `Pending` after `intake_status = Processed`.

`Needs Review` is reserved for a deterministic validation error or an explicit AI conflict after the deterministic gate. Google Maps uncertainty is recorded as an issue but does not by itself change `status` to `Needs Review`.

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
- `internal_property_type`: exactly `Gated Community`, `Semi Gated`, or `Standalone`. Explicit source evidence is authoritative; explicit negative gating resolves to `Standalone`; the declared `Standalone` fallback applies only when no property-type evidence exists.
- `balconies`: accept explicit numeric singular/plural balcony forms; bare `Balcony` is one balcony.
- `pet_friendly`: explicit no-pet wording such as `Pets: Not Allowed` is authoritative and resolves to `No`; absent restriction retains the established `Yes` fallback.
- `google_maps_url`: deterministic source URLs are extracted independently of network Maps enrichment.
- `landmark`: a `📍 Landmark:` marker followed only by a Maps URL remains blank; the URL belongs to `google_maps_url`.

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

The inventory contract is 48 columns A:AV. Stage 1/2 writes are restricted to A:D, F:AO, and AU. E, AP:AT, and AV remain protected.

## Verification

Regression coverage includes canonical source segmentation, multi-candidate resolution, later corrections, decimal BHK, maintenance unit normalization/qualifiers/inclusion, positive/negative property-type evidence, singular/decimal balcony source forms, explicit pet negatives, Sheet-independence, dependent defaults, and normalized maintenance validation. Production extraction remains gated on repository verification plus the read-only live model audit.
