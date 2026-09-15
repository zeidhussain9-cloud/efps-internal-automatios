# Project Rules

These are standing engineering and automation rules for EFPS Internal Automations.

## Truth and scope

1. Apply `CORE_STEERING.md` before every response or action.
2. Establish repository and runtime truth before implementation; never guess or silently infer missing facts.
3. Use the smallest safe change that satisfies the verified requirement.
4. Do not modify unrelated modules, shared capabilities, infrastructure, or documentation.
5. Preserve explicit business ownership boundaries.

## Architecture

- `modules/` owns EFPS business capabilities and business decisions.
- `shared/` owns reusable technical capabilities and must remain business-neutral.
- Shared services provide capabilities; modules decide when and why they are used.
- Established shared capability boundaries are `shared/cloudinary/`, `shared/google_sheets/`, `shared/whatsapp_whapi/`, `shared/google_maps/`, `shared/slack/`, and `shared/credentials/`.
- A shared boundary may exist before every runtime feature is complete; status must be explicit and verified.

## Inventory Phase 1

Inventory uses three top-level stages only:

1. Stage 1 — Initial / Webhook.
2. Stage 2 — Deterministic Extraction / Property Processing.
3. Stage 3 — Downstream Operations boundary.

Maps resolution, validation, AI verification, and wording-only AI beautification are Stage-2 sub-steps. Google Sheets persistence is transport/output, not a top-level stage.

The completed `raw_message_text` is the authoritative deterministic extraction source. Existing canonical Sheet values must not become replay/extraction inputs. Deterministic rules must preserve explicit source facts and fail closed rather than invent missing facts.

### Source-message extraction boundary

Inventory raw sessions can contain multiple concatenated WhatsApp messages. `modules/efps-inventory-mgmnt/src/source_segments.py` is the canonical segmentation primitive. Labelled-field extraction must operate on one source unit at a time so a field cannot consume a later message. A recurring extraction defect must be fixed at the canonical source-boundary or field-contract level and must include a regression fixture for the triggering source shape; isolated one-off regex patches are not sufficient.

### Canonical field-resolution boundary

`modules/efps-inventory-mgmnt/src/field_resolution.py` is the sole deterministic candidate-resolution layer. Extractors discover candidates; the resolver chooses the authoritative source candidate; normalization canonicalizes the chosen result. No downstream normalization function may independently reclassify a resolved deterministic field. Existing Sheet values are never candidates. Later explicit source corrections supersede earlier values; explicit negative gating cannot be overridden by generic positive wording.

The three fields that previously produced recurring populated conflicts are governed explicitly: BHK preserves decimals and resolves later explicit corrections; maintenance requires maintenance-specific context and preserves qualifiers such as `+ Water`; internal property type has one canonical resolver for Gated Community, Semi Gated, and Standalone.

## Cloudinary

`shared/cloudinary/` provides technical media storage/upload capabilities. Business modules decide which media is stored and why. The shared implementation uses deterministic property/lead namespaces, non-overwriting uploads, stable secure URLs, and optional media fingerprints.

## Google Sheets

`shared/google_sheets/` owns the technical Sheets client and the canonical physical `Housing_Listings` contract. Full-row operations must use the 48-column A:AV schema; ownership and business workflow remain outside the shared client. Verified Inventory Phase-1 Stage-1/2 write ranges are A:D, F:AO, and AU; E, AP:AT, and AV are protected.

## Google Maps

`shared/google_maps/` is a reusable technical adapter. Inventory decides when Maps is required. The adapter uses `GOOGLE_MAPS_API_KEY` or the approved local Keychain credential, resolves through the Google Geocoding API, and returns a structured `MapsResolution`. `resolve()` is keyword-only. Inventory accepts only `VERIFIED` as a successful Maps enrichment; `PARTIAL_MATCH`, `NEEDS_RUNTIME_VERIFICATION`, and `NOT_FOUND` are recorded as informational issues and do not by themselves convert an otherwise valid deterministic extraction to `Needs Review`. The current Inventory Phase-1 direct and application-path Maps verification has passed.

## WhatsApp / WhAPI

`shared/whatsapp_whapi/` must retain an explicit live-traffic gate. No live WhAPI network operation should happen without the deliberate runtime approval mechanism. Webhook event names must be discovered from the current allowed-events endpoint rather than guessed from historical configuration.

## Credentials

`shared/credentials/` is the canonical local macOS Keychain provider. Secret values must never be committed. Historical AWS Secret Manager values are migration sources only. The verified seven-service migration is recorded as a machine-level identity check; a separate dedicated Maps credential is documented where applicable.

## Documentation

- `docs/` is the canonical home for permanent business and system knowledge.
- Every implementation must review every maintained root document and every document inside `docs/` against resulting repository reality.
- Update every affected document in the same work session.
- Update `HANDOFF.md` whenever current working state changes.
- Use `DOCUMENT_UPDATE_MATRIX.md` and `DOCUMENT_GOVERNANCE.md` for document ownership and routing.
- Do not create duplicate authoritative documents.

## Security

- Never commit secrets, API tokens, passwords, private keys, or production authentication material.
- Do not expose production data merely to simplify implementation.
- Document verified resource identifiers without storing secret values.
- Cloudinary configuration/credentials, Google service-account credentials, WhAPI tokens, Maps API keys, and Slack secrets must remain outside version control.

## Validation

A change is complete only when the applicable implementation, verification, validation, and documentation checks are complete and there are no known contradictions with repository truth. The read-only model audit must report populated source conflicts separately from expected projections and must exit non-zero when true populated conflicts or protected-column changes remain.
