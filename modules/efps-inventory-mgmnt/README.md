# EFPS Inventory Management

## Inventory Phase-1 workflow

Inventory Phase 1 uses three top-level stages:

### Stage 1 — Initial / Webhook
The dedicated inventory listener receives the normalized WhAPI message. `NEW` opens a property session; subsequent messages from that listener are collected until the next `NEW`, which closes the property. A canonical `listing_id` is created for the property row, and the raw record is persisted with the source text and intake metadata.

### Stage 2 — Deterministic Extraction / Property Processing
The completed `raw_message_text` is the authoritative extraction source. The actual Stage-2 entry point is `process_closed_session()` in `src/pipeline.py`.

Its sequence is:

1. deterministic extraction
2. deterministic normalization/business rules
3. Google Maps resolution when a Maps URL is supplied/extracted
4. deterministic validation
5. optional AI verification/wording-only beautification after the deterministic gate

AI cannot replace deterministic source facts or bypass a deterministic validation failure.

Google Maps is a Stage-2 processing sub-step, not a separate top-level stage. Google Sheets persistence is transport/output, not a top-level stage.

### Stage 3 — Downstream Operations
Stage 3 is the downstream boundary for later consumers. It is not part of the current Inventory Phase-1 publishing implementation. Future Housing Portal and Meta Catalogue work requires explicit implementation requirements and authorization.

## Deterministic business-rule boundary

Deterministic processing is source-preserving and does not guess missing property facts. Current verified rules include:

- `2.5 BHK` remains `2.5 BHK`; decimal BHK values must not be corrupted by integer-only parsing.
- Ground-floor `G`/`Ground` normalizes to floor `0`.
- Carpet area defaults to 90% of built-up area when carpet area is blank.
- Maintenance included means maintenance is `0`; otherwise stated nonnumeric maintenance text is preserved.
- Deposit expressed as months is calculated from monthly rent.
- `Semi Furnished` and `Fully Furnished` receive deterministic furnishing defaults only when explicit furnishings are blank.
- Source text indicating `Unfurnished`, `un-furnished`, `not furnished`, or `empty` does not create an `Unfurnished` Sheet value; `furnish_type` and `flat_furnishings` remain blank.
- Explicit furnishings are not silently overwritten.
- Property subtype aliases are normalized to the canonical subtype vocabulary.
- Explicit `Gated Community` wording produces `Gated Community` internal property type; explicit semi-gated wording produces `Semi Gated`; independent-house/floor/farm-house wording produces `Standalone`; otherwise the documented fallback applies without inventing gating facts.
- Gated-community and semi-gated amenity defaults are deterministic and are not evidence that a property is gated when the source does not establish that fact. Exact Sheet dropdown reconciliation remains an open contract item.
- Family/family-only tenant preference forces the current internal bachelor fallback only when no explicit bachelor value is present. Its `Not Allowed` output is not currently a live Sheet dropdown value and remains an open contract item.

## Canonical Sheet-controlled fields

Live read-only verification established these exact current contracts:

| Column | Field | Contract |
|---|---|---|
| D | `internal_property_type` | `Gated Community`; `Semi Gated`; `Standalone` |
| M | `furnish_type` | `Fully Furnished`; `Semi Furnished` |
| Y | `preferred_tenant_type` | `Family`; `Open For All` |
| Z | `bachelor_preference` | `Female Only `; `Male Only`; `Open for both` |
| AA | `pet_friendly` | no Sheet dropdown; populated values observed: `Yes`, `No` |
| AE | `society_amenities` | `Security, Lift, CCTV, Power Backup`; `Club House, Lift, Gym, CCTV, Power Backup, Swimming Pool, Garden, Sports, Kids Area`; `-` |
| AF | `flat_furnishings` | `Wardrobe, Modular Kitchen, Geyser, Fan, Light`; `Wardrobe, Modular Kitchen, Geyser, Fan, Light, Fridge, Washing Machine, TV, Sofa, Bed, Dining Table` |

D, M, Y, Z, AE, and AF use strict `ONE_OF_LIST` validation with custom UI enabled. No conditional/row-dependent dropdown validation was observed. The field relationships are application/business dependencies, not conditional Sheet dropdowns.

## Business field dependencies

- `internal_property_type` → `society_amenities`: deterministic tier defaults when amenities are blank.
- `furnish_type` → `flat_furnishings`: deterministic furnishing defaults when furnishings are blank.
- `preferred_tenant_type` → `bachelor_preference`: family/bachelor normalization rule; Sheet vocabulary reconciliation remains open.
- `maintenance_included` ↔ `maintenance`: included means maintenance `0`.
- `monthly_rent` → `security_deposit`: month-based deposits are calculated from rent.

## Maps integration

`shared/google_maps` is the reusable technical Maps capability. Inventory decides when Maps is required and consumes verified results for `locality`, `pincode`, and canonical `google_maps_url`.

The Stage-2 pipeline fails closed for Maps states other than `VERIFIED`: `PARTIAL_MATCH`, `NEEDS_RUNTIME_VERIFICATION`, `NOT_FOUND`, and unrecognized states cause `Needs Review`.

The live application path has been verified using the local Keychain credential. A real address resolution and a real Google Maps URL resolution both returned `VERIFIED`; the actual `process_closed_session()` path consumed the Maps result and populated `locality`, `pincode`, and canonical `google_maps_url`.

## Property boundary

`NEW` is the property-session delimiter. Every text message until the next `NEW` belongs to that property. Media are recognized/countable but their binary payloads are not downloaded or serialized into `raw_message_text` in the current Phase-1 implementation.

## Raw source

Text messages are preserved in `raw_message_text`, in arrival order with timestamp/message-id metadata when available. Duplicate webhook deliveries carrying the same message ID are ignored within the active session.

## Stage-1/2 Sheets boundary

The canonical inventory sheet is 48 columns A:AV. Stage 1/2 writes are restricted to A:D, F:AO, and AU. `listing_state` (E), Housing fields AP:AR, Meta fields AS:AT, and `inventory_locked` (AV) are protected from this path.

## Package layout

The implementation package is `modules/efps-inventory-mgmnt/src/` and contains `__init__.py`; `pipeline.py` uses package-relative imports. When running direct verification from the repository root, add `modules/efps-inventory-mgmnt` to `PYTHONPATH` and import `src.pipeline` rather than inventing an underscored package name from the hyphenated directory.

## Current verification state

- Deterministic rules validated against the current inventory sample: verified.
- Google Sheets production read/write boundary: verified without unauthorized Stage-3 writes.
- Live Sheet dropdown/populated-value inspection: verified for D, M, Y, Z, AA, AE, AF.
- Google Maps direct API access: verified.
- Google Maps application path: verified.
- Stage-2 end-to-end deterministic + Maps + validation path: verified without a production Sheet write.
- External AI runtime remains a separate runtime acceptance boundary when enabled.
