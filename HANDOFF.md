# EFPS Internal Automations — Current Handoff

## Current state

The current authorized implementation target is **Inventory Management Phase 1**. The workflow is organized into three top-level stages:

1. **Stage 1 — Initial / Webhook**: dedicated inventory listener → `NEW` property-session boundary → raw capture → initial row.
2. **Stage 2 — Deterministic Extraction / Property Processing**: deterministic extraction → normalization/business rules → Maps resolution → validation → optional AI verification → wording-only AI beautification.
3. **Stage 3 — Downstream Operations boundary**: reserved for later consumers; not part of the current Inventory Phase-1 publishing implementation.

Stage-2 items are processing sub-steps, not separate top-level stages. Google Sheets persistence is a transport/output operation, not an additional stage.

## Stage-1/2 implementation

- `intake.py` implements the explicit `NEW` boundary, dedicated-listener filtering, and message-ID idempotency within an active session.
- `extract.py` performs deterministic extraction from completed `raw_message_text`.
- `normalize.py` contains the migrated deterministic normalization/business rules, including furnishing defaults, carpet derivation, maintenance handling, property subtype normalization, internal property type/amenity rules, and tenant/bachelor dependency.
- `validate.py` enforces the canonical 48-field shape, fixed values, deterministic validation, and downstream write protection.
- `listing_id.py` preserves immutable `EF-YYMM-XXXX` IDs.
- `pipeline.py` orchestrates Stage 2 and writes only Stage-1/2-owned fields. The canonical processing entry point is `process_closed_session()`.
- When a Maps URL is supplied/extracted, `process_closed_session()` calls `GoogleMapsClient.resolve(maps_url=...)`. Only `VERIFIED` resolution populates `google_maps_url`, `locality`, and `pincode`; incomplete/unrecognized states fail closed to `Needs Review`.
- `ai.py` remains advisory: it cannot replace deterministic facts or bypass a failed validation gate.
- `webhook.py` connects the normalized WhAPI inventory message to the Stage-1/2 pipeline and persists raw text at current column G.
- `batch.py` provides a deterministic-first Phase-1 batch path for existing canonical rows with `intake_status = Raw` and populated `raw_message_text`.

## Verified deterministic findings

- Decimal BHK such as `2.5 BHK` is preserved and is not reduced to an integer.
- Ground-floor `G`/`Ground` normalizes to `0`.
- Carpet area derives to 90% of built-up area when carpet is blank.
- Maintenance included normalizes to `0`; stated nonnumeric maintenance text is preserved otherwise.
- Month-based deposits are calculated from monthly rent.
- Furnishing defaults and explicit-furnishing precedence are deterministic.
- Property subtype aliases normalize to the canonical subtype vocabulary.
- Internal property type is limited to `Gated Community`, `Semi Gated`, and `Standalone`, with classification driven by verified source wording and documented fallback behavior.
- Gated/semi-gated amenity defaults do not by themselves prove that a property is gated.
- Family/family-only tenant preference sets `bachelor_preference = Not Allowed` only when no explicit bachelor value is present.
- Deterministic extraction uses completed `raw_message_text`, not prior canonical Sheet values.

## Canonical sheet

`Housing_Listings` is exactly 48 columns A:AV in the latest supplied order. `shared/google_sheets/schema.py` is the canonical physical contract. Stage-1/2 writes are restricted to A:D, F:AO, and AU. E (`listing_state`), AP:AT, and AV (`inventory_locked`) are protected from this path.

The production read and write boundary have been verified. No Stage-3 field is permitted through the Stage-1/2 writer.

## Google Maps verified state

`shared/google_maps/` is the reusable technical Maps capability. The current Inventory Phase-1 credential is loaded through local macOS Keychain service `efps-google-maps-api-key` or the `GOOGLE_MAPS_API_KEY` environment override. The adapter uses the Google Geocoding API and returns a structured `MapsResolution`.

Verified application-path results:

- Address resolution for `Harlur, Bengaluru, Karnataka`: `VERIFIED` with coordinates.
- Google Maps search URL resolution: `VERIFIED`, resolved to HSR Layout, Bengaluru, pincode `560102`.
- Actual Inventory Stage-2 `process_closed_session()` consumption: `SUCCESS`, including canonical Maps URL, locality, and pincode.

`GoogleMapsClient.resolve()` is keyword-only. The inventory package itself is under the hyphenated filesystem directory `modules/efps-inventory-mgmnt/src/`, which contains `__init__.py`; direct verification must load that package layout correctly rather than inventing an underscored module name.

## WhAPI verified live state

The connected WhAPI account and deployed webhook were verified with read-only/live diagnostics:

- `GET /health`: HTTP 200.
- Connected display identity: `Easyfind Property Solutions`.
- Connected WhatsApp ID: `919148338801`.
- Business channel: `true`.
- Channel ID: `DRAXTH-J6HEU`.
- `GET /settings`: HTTP 200.
- A webhook is configured in `body` mode with `messages` / `POST` subscription.
- `GET /settings/events`: HTTP 200 and `messages` / `post` is an allowed event.
- A direct synthetic JSON POST to the configured deployed webhook returned HTTP 200 with `{"ok": true, "queued": 1}`.
- The synthetic probe used non-inventory sender `919000000000`, so it could not open an Inventory Phase-1 property session.
- The deployed webhook URL and its `?t=` authentication token are intentionally not recorded in repository documentation.
- No WhAPI settings were modified and no customer message was sent during the acceptance checks.

The initial `/health` request was blocked by Cloudflare browser-signature filtering. A subsequent single diagnostic request with explicit `User-Agent: EFPS-Inventory-Phase1/1.0` passed with HTTP 200. The current canonical `WhApiClient` has not yet been modified to add that header; therefore permanent client transport compatibility with the Cloudflare requirement remains an implementation follow-up.

The live WhAPI configuration and deployed endpoint are verified, but a real inventory-listener message acceptance test has not been performed because that would exercise the real `NEW` session and production Sheet persistence path.

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

See `docs/OPEN_POINTERS.md`. The current unresolved items are:

1. Slack production runtime acceptance.
2. Exact Google Sheet dropdown vocabularies for `preferred_tenant_type`, `bachelor_preference`, and `pet_friendly`.
3. Exact `inventory_locked` sheet control vocabulary.
4. Decide and verify whether the explicit WhAPI user-agent required by the successful Cloudflare diagnostic should become part of the canonical `WhApiClient` transport contract.

Future Meta Catalogue, Housing Portal, and website production integrations are outside the current Inventory Phase-1 pointer list.

## Next development rule

Do not enter future downstream publishing phases beyond the authorized Inventory Phase-1 boundary until explicitly authorized. At the end of each implementation, review all maintained root/docs guidance and this handoff against repository reality.
