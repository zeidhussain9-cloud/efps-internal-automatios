# Deterministic Field Resolution

**Status:** Active

This document is the canonical Stage-2 contract for fields that require deterministic candidate discovery, precedence, resolution, and normalization.

## Pipeline contract

```text
raw_message_text
  -> canonical source segmentation
  -> candidate extraction
  -> deterministic field resolution
  -> business normalization
  -> deterministic validation
  -> Maps enrichment/verification
  -> optional AI verification
  -> wording-only AI beautification
```

Extraction discovers source candidates. Resolution selects the authoritative candidate. Normalization canonicalizes the selected result and applies declared business rules. Existing Sheet Stage-2 values are never extraction candidates. AI does not author deterministic facts.

## Source precedence

1. Explicit labelled source evidence.
2. Explicit boolean/negative evidence where the field supports it.
3. Specific deterministic wording.
4. Generic wording.
5. Declared fallback only when the contract explicitly permits a fallback.

When the same field is explicitly corrected in a later source message, the later explicit value wins. An explicit negative gating statement is authoritative and cannot be overridden by later generic positive wording.

## Field contracts

### BHK

Recognize integer and decimal BHK values, bedroom-labelled forms, and RK forms according to the Inventory source contract. Preserve decimal BHK values. A 1 RK listing normalizes to `1 RK`. Existing Sheet BHK values are never used as source evidence.

### Property subtype

The operational EFPS subtype vocabulary is:

- `Apartment` — normal apartment/flat/building inventory, including apartment properties whose internal property type is Gated Community or Semi Gated.
- `Villa` — villa inventory, including explicit compound wording such as `Duplex Villa`.
- `Studio` — reserved for 1 RK inventory.

The portal UI exposes additional categories (`Independent House`, `Duplex`, `Independent Floor`, `Penthouse`, `Farm House`), but EFPS normal operations primarily use Apartment, Villa, and Studio. Explicit supported subtype wording remains authoritative; aliases are canonicalized before fallback. A normal building must not be left blank merely because it lacks an explicit subtype label.

### Maintenance

Only maintenance-labelled values or the specific `rent + maintenance` form can create maintenance candidates. Normalize `K`/lakh amounts to rupees. If maintenance is included in rent, set `maintenance_included = Yes` and `maintenance = 0`. If maintenance is included and water charges are additional, set `maintenance_included = Yes` and `maintenance = Water Charges Additional`. A separately stated maintenance amount sets `maintenance_included = No`. Source qualifiers such as `+ Water` remain preserved for separately charged maintenance.

### Internal property type

`internal_property_type` has exactly three business output values:

- `Gated Community`
- `Semi Gated`
- `Standalone`

The primary source contract is an explicit classification line using `Community`, for example:

```text
Community: Gated Community
Community: Semi Gated
Community: Standalone
```

The `Community` label and classification value are matched case-insensitively and tolerate ordinary whitespace and hyphenation variants such as `community:gated`, `semi-gated`, and `stand-alone`. Equivalent explicit labels such as `Property Type:` and `Gating Type:` remain supported. Canonical output is always exactly `Gated Community`, `Semi Gated`, or `Standalone`.

Explicit gating wording is authoritative. Absence of gating evidence is not evidence of `Standalone`. An invalid or absent classification remains unresolved rather than being invented. Society/community names are never used to infer the internal property type.

`internal_property_type` drives the default `society_amenities` bundle and the covered-parking default; therefore it is a parent business decision with downstream dependencies.

### Society name, landmark, and Maps URL

EFPS source messages commonly use a structured marker such as:

```text
📍 Bren Avalon:
https://maps.app.goo.gl/...
```

The marker name is a society/property-name candidate and the URL is a `google_maps_url` candidate. A `📍 Landmark:` marker followed by a Maps URL must not store the URL as `landmark`; the URL belongs to `google_maps_url` and the landmark remains blank unless an actual landmark value is supplied.

`google_maps_url` is a deterministic source field because the URL is present in `raw_message_text`. Maps resolution is a separate enrichment step that may verify/replace locality and obtain pincode.

`locality` is source-owned during deterministic extraction: explicit `Property Location`, `Location`, `Locality`, or `Area` text is authoritative for the projection. Verified Maps may replace it later during enrichment; absence of Maps enrichment must not downgrade correct raw-source locality extraction.

`society_name` may fall back to locality only after direct source parsing and enrichment have had an opportunity to establish a society/property name. `landmark` never inherits locality.

### Numeric balcony source forms

Balcony counts are deterministic source facts. Both singular and plural spellings are valid (`Balcony`, `Balconies`), and numeric counts may be integers or decimals when explicitly supplied. A bare singular `Balcony` means `1`. No value is invented from other room/property wording.

### Pet preference

Pet status is source-grounded during deterministic normalization. Explicit negative forms including `Pets: Not Allowed`, `Pets: Not Permitted`, `Pets: Prohibited`, `Pets: Banned`, `No pets`, and `Without pets` resolve to `No`. Explicit positive forms resolve to `Yes`. When no pet restriction is present, the established last-resort value remains `Yes`.

### Parking

For `Gated Community` and `Semi Gated`, `covered_parking` defaults to `1` only when no covered-parking value is supplied. An explicit source value such as `2` remains authoritative. Standalone properties do not receive the covered-parking default. Open-parking values are populated from explicit source evidence; no unsupported parking inference is introduced.

### Pincode

Pincode is an enrichment field when it is not explicitly present in source text. A verified Maps result may supply it from the postal-code component. A blank pincode is valid and non-blocking; it must not by itself create `Needs Review` or a deterministic extraction failure.

### Tenant eligibility dependency

`preferred_tenant_type` is the parent field and `bachelor_preference` is its dependent field. The live Sheet dropdowns are authoritative for exact values:

- `preferred_tenant_type` = `Family` or `Open For All`.
- `Family` -> `bachelor_preference` must be blank.
- `Open For All` -> `bachelor_preference` defaults exactly to `Open for both`.
- Explicit valid source evidence for `Female Only ` or `Male Only` overrides the default.

The canonical Sheet vocabulary is exactly `Female Only ` (with the trailing space present in the live dropdown), `Male Only`, and `Open for both`. The trailing space is intentional and is part of the exact Sheet contract. It must not be trimmed away when writing or validating the dependent dropdown value.

## Dependency graph

```text
internal_property_type
        |
        +----> society_amenities
        |
        +----> covered_parking (default only when blank)

furnish_type
        |
        +----> flat_furnishings (default only when blank)

preferred_tenant_type
        |
        +----> bachelor_preference

maintenance
        |
        +----> maintenance_included

built_up_area
        |
        +----> carpet_area (fallback only when blank)

monthly_rent
        |
        +----> security_deposit (when deposit is expressed in months)
```

Dependency means downstream correctness depends on the parent decision; it does not mean the child can only ever be populated through the parent. Explicit child source evidence remains authoritative where the field contract permits it.

## Model audit contract

`tools/inventory_model_test.py` is read-only. It projects the exact deterministic Stage-2 path against existing Sheet rows without feeding Sheet values back into extraction and without writing to the Sheet.

The projection artifact must record the exact Git commit used to execute it. A projection generated from an older commit is evidence of that older implementation only and must not be used to adjudicate a later fix.

A populated Sheet mismatch is a source/historical conflict, not proof that the model is wrong. It must be adjudicated against `raw_message_text` and the established contract. Blank Stage-2 cells becoming populated are expected projections. Lifecycle changes, formatting-only differences, populated conflicts, and protected-column changes remain separate categories.

## Regression contract

Every production extraction/resolution defect must have a fixture for the exact triggering source shape. Regression coverage must include:

- source-message boundaries;
- multiple candidates and later explicit corrections;
- decimal BHK and 1 RK;
- Apartment/Villa/Studio subtype rules;
- maintenance amount normalization;
- maintenance included and included-plus-water semantics;
- positive and negative gating evidence;
- case-insensitive and whitespace/hyphenation variants of the explicit `Community:` property-type source form;
- `📍` society/property and landmark markers;
- Maps URL extraction without network access;
- locality extraction from explicit source labels;
- singular/decimal balcony source forms;
- explicit positive and negative pet forms;
- Sheet-independence;
- dependent-value generation, including `Open For All -> Open for both`;
- exact live bachelor dropdown values, including the intentional trailing space on `Female Only `;
- non-blocking pincode absence;
- valid blank property highlights;
- validation of the normalized output shape.

## Non-goals

This deterministic layer does not write Google Sheets, call network Maps resolution during projection, call AI, or own downstream publication state.
