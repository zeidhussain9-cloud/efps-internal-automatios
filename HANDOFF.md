# EFPS Internal Automations — Current Handoff

## Current state

The current authorized implementation target is **Inventory Management Phase 1**. The workflow is organized into three top-level stages:

1. **Stage 1 — Initial / Webhook**: dedicated inventory listener → `NEW` property-session boundary → raw capture → initial row.
2. **Stage 2 — Deterministic Extraction / Property Processing**: deterministic extraction → normalization/business rules → Maps resolution → validation → optional AI verification → wording-only AI beautification.
3. **Stage 3 — Downstream Operations boundary**: reserved for later consumers; not part of the current Inventory Phase-1 publishing implementation.

Stage-2 items are processing sub-steps, not separate top-level stages. Google Sheets persistence is a transport/output operation, not an additional stage.

## Stage-1/2 implementation

- `intake.py` implements the explicit `NEW` boundary, dedicated-listener filtering, and message-ID idempotency within an active session.
- `extract.py` performs deterministic extraction from completed `raw_message_text`, including direct source fields for internal property type, society name, landmark, location/locality, subtype, and explicit highlights.
- `normalize.py` contains deterministic normalization/business rules, including direct-field fallbacks, pet-friendly last-resort handling, covered-parking default, furnishing defaults, carpet derivation, maintenance handling, property subtype normalization, internal property type/amenity rules, tenant/bachelor dependency, and factual title/highlight fallback.
- `validate.py` enforces the canonical 48-field shape, fixed values, deterministic validation, verified Sheet vocabularies, and downstream write protection.
- `listing_id.py` preserves immutable `EF-YYMM-XXXX` IDs.
- `pipeline.py` orchestrates Stage 2 and writes only Stage-1/2-owned fields. Verified Maps locality is reapplied to blank society/landmark fallbacks before persistence.
- When a Maps URL is supplied/extracted, `process_closed_session()` calls `GoogleMapsClient.resolve(maps_url=...)`. Only `VERIFIED` resolution populates `google_maps_url`, `locality`, and `pincode`; incomplete/unrecognized states fail closed to `Needs Review`.
- `ai.py` remains advisory: it cannot replace deterministic facts or bypass a failed validation gate.
- `webhook.py` connects the normalized WhAPI inventory message to the Stage-1/2 pipeline and persists raw text at current column G.
- `batch.py` provides a deterministic-first Phase-1 batch path for existing canonical rows with `intake_status = Raw` and populated `raw_message_text`.

## Verified deterministic findings

- Decimal BHK such as `2.5 BHK` is preserved and is not reduced to an integer.
- Ground-floor `G`/`Ground` normalizes to `0`.
- Carpet area derives to 90% of built-up area when carpet is blank.
- Maintenance is read from source; numeric k/lakh values normalize to rupees and mixed values such as `2777 + Water` preserve their stated suffix. Included means maintenance `0`.
- Month-based deposits are calculated from monthly rent.
- `Fully Furnished` and `Semi Furnished` have deterministic furnishing defaults only when explicit furnishings are absent.
- Unfurnished source wording leaves `furnish_type` and `flat_furnishings` blank.
- Direct source values for internal property type, society name, landmark, location/locality, subtype, and explicit highlights are preferred over inference.
- Missing society name and missing landmark fall back to the resulting locality/location. Verified Maps locality is also used to complete those fallbacks.
- Internal property type is limited to `Gated Community`, `Semi Gated`, and `Standalone`. Explicit direct values are normalized first; otherwise explicit semi-gated/gated wording is used and the fallback is Standalone.
- Gated Community defaults to the exact live Sheet amenity combination `Club House, Lift, Gym, CCTV, Power Backup, Swimming Pool, Garden, Sports, Kids Area`; Semi Gated defaults to `Security, Lift, CCTV, Power Backup`; Standalone defaults to `-` when amenities are blank.
- Gated Community and Semi Gated default `covered_parking` to `1` when the source does not provide a covered-parking value; Standalone does not.
- `servant_room` is `Yes` only when explicitly stated and `No` otherwise.
- `pet_friendly` is `No` when explicit no-pet wording is present; when no pet restriction is mentioned, the established last-resort value is `Yes`.
- Preferred tenant variants normalize to the live Sheet vocabulary. Family variants become `Family`; anyone/open-for-all variants become `Open For All`; the female-bachelor rule preserves the exact `Female Only ` Sheet value.
- Property subtype uses explicit source value/alias first; `Apartment` is only the normal floor-bearing fallback and is not invented for standalone-property wording.
- Property highlights preserve explicit source highlights; otherwise only factual deterministic fragments are constructed.
- Catalog title has a factual deterministic fallback using available furnishing, BHK, and location; optional AI may rewrite title/highlights without adding facts.
- `age_of_property_years` is populated only from an explicit/authoritative age fact and otherwise remains blank.

## Canonical sheet

`Housing_Listings` is exactly 48 columns A:AV in the latest supplied order. `shared/google_sheets/schema.py` is the canonical physical contract. Stage-1/2 writes are restricted to A:D, F:AO, and AU. E (`listing_state`), AP:AT, and AV (`inventory_locked`) are protected from this path.

The production read and write boundary have been verified. No Stage-3 field is permitted through the Stage-1/2 writer.

### Verified live dropdown/value contract

Read-only production inspection established:

- D `internal_property_type`: `Gated Community`, `Semi Gated`, `Standalone`.
- M `furnish_type`: `Fully Furnished`, `Semi Furnished`.
- Y `preferred_tenant_type`: `Family`, `Open For All`.
- Z `bachelor_preference`: exact observed values `Female Only `, `Male Only`, `Open for both`.
- AA `pet_friendly`: no Sheet data-validation rule; populated values observed are `Yes` and `No`.
- AE `society_amenities`: `Security, Lift, CCTV, Power Backup`; `Club House, Lift, Gym, CCTV, Power Backup, Swimming Pool, Garden, Sports, Kids Area`; `-`.
- AF `flat_furnishings`: `Wardrobe, Modular Kitchen, Geyser, Fan, Light`; `Wardrobe, Modular Kitchen, Geyser, Fan, Light, Fridge, Washing Machine, TV, Sofa, Bed, Dining Table`.

D, M, Y, Z, AE, and AF use strict `ONE_OF_LIST` validation with custom UI enabled. No conditional/row-dependent dropdown validation was observed; the relationships among these fields are application/business dependencies.

### Verified business dependencies

- `internal_property_type` → `society_amenities`: Gated Community/Semi Gated/Standalone map to the exact verified amenity choices when blank.
- `internal_property_type` → `covered_parking`: Gated Community/Semi Gated → `1` when blank.
- `furnish_type` → `flat_furnishings` for deterministic furnishing defaults when furnishings are blank.
- `preferred_tenant_type` → `bachelor_preference`: canonical tenant normalization plus explicit bachelor/female-bachelor handling; no invalid `Not Allowed` value is generated.
- `maintenance_included` ↔ `maintenance` and `monthly_rent` → `security_deposit` are deterministic dependencies.

## Google Maps verified state

`shared/google_maps/` is the reusable technical Maps capability. The current Inventory Phase-1 credential is loaded through local macOS Keychain service `efps-google-maps-api-key` or the `GOOGLE_MAPS_API_KEY` environment override. The adapter uses the Google Geocoding API and returns a structured `MapsResolution`.

Verified application-path results remain established for address resolution, Maps URL resolution, and Stage-2 consumption. A verified Maps locality now also completes blank society/landmark fallback fields.

`GoogleMapsClient.resolve()` is keyword-only.

## WhAPI verified live state

The connected WhAPI account and deployed webhook were verified with read-only/live diagnostics. The successful Cloudflare diagnostic required explicit `User-Agent: EFPS-Inventory-Phase1/1.0`; the canonical `WhApiClient` has not yet been modified to add that header. Permanent client transport compatibility remains a follow-up.

A direct synthetic JSON POST to the deployed webhook returned HTTP 200 with `{"ok": true, "queued": 1}` using a non-inventory sender. No real inventory-listener message acceptance test has been performed.

## Credential migration state

The current repository uses the shared macOS Keychain provider under `shared/credentials/`. Seven baseline local services were independently hash-verified against their historical AWS source values as exact matches. The current Maps API credential is separately maintained under `efps-google-maps-api-key` and has independently passed live Google Geocoding verification. Secret values are never stored in the repository.

## Cloudinary verified state

The shared Cloudinary application path has passed live Inventory Phase-1 upload acceptance through the canonical local Keychain credential path. The acceptance returned the deterministic property public ID and an HTTPS `secure_url`. The temporary test asset remains a runtime artifact unless separately removed.

## Slack Phase-1 boundary

- `shared/slack/` is the canonical shared Slack capability.
- Slack is an operational interface; `Housing_Listings` remains the source of truth.
- Phase-1 Slack includes batch control/reporting, property verification, runtime/bug reporting, and the temporary manual bulk-photo path.
- The current webhook does not reliably persist inbound photo binaries with property association. Therefore photos are temporarily associated through the exact Slack property thread and then uploaded to Cloudinary.
- Society approval is explicitly obsolete and excluded. Do not add society approval commands, queues, cards, or a society approval state.
- The shared Slack capability is source-implemented, but production Slack deployment/live verification remains a separate acceptance step.

## Current open pointers

See `docs/OPEN_POINTERS.md`. The deterministic inventory contract follow-ups from the 25-row model run are now implemented and regression-covered. Current unresolved items are:

1. Slack production runtime acceptance.
2. Exact `inventory_locked` sheet control vocabulary.
3. Decide and verify whether the explicit WhAPI user-agent required by the successful Cloudflare diagnostic should become part of the canonical `WhApiClient` transport contract.
4. Analyze the 17 `PARTIAL_MATCH` Google Maps cases from the 25-row dry run before live extraction; the current fail-closed behavior remains intentional.

Future Meta Catalogue, Housing Portal, and website production integrations are outside the current Inventory Phase-1 pointer list.

## Next development rule

Do not enter future downstream publishing phases beyond the authorized Inventory Phase-1 boundary until explicitly authorized. At the end of each implementation, review all maintained root/docs guidance and this handoff against repository reality.
