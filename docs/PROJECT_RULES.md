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

`modules/efps-inventory-mgmnt/src/field_resolution.py` is the sole deterministic candidate-resolution layer for BHK, maintenance, and internal property type. Extractors discover candidates; the resolver chooses the authoritative source candidate; normalization canonicalizes the chosen result. No downstream normalization function may independently reclassify a resolved deterministic field. Existing Sheet values are never candidates.

Later explicit source corrections supersede earlier explicit values. Explicit negative gating is authoritative against generic positive wording.

### Dependency contract

The established Inventory application dependency graph is:

```text
internal_property_type -> society_amenities
internal_property_type -> covered_parking (blank-only default)
furnish_type -> flat_furnishings (blank-only default)
preferred_tenant_type -> bachelor_preference
maintenance -> maintenance_included
built_up_area -> carpet_area (blank-only fallback)
monthly_rent -> security_deposit (month-based source form)
```

`internal_property_type` has exactly three business values: `Gated Community`, `Semi Gated`, and `Standalone`.

Maintenance is a normalized numeric amount with an optional source qualifier; `maintenance_included` is evaluated independently. Explicit child source evidence remains authoritative where the child contract permits it.

## Cloudinary

`shared/cloudinary/` provides technical media storage/upload capabilities. Business modules decide which media is stored and why. The shared implementation uses deterministic property/lead namespaces, non-overwriting uploads, stable secure URLs, and optional media fingerprints.

## Google Sheets

`shared/google_sheets/` owns the technical Sheets client and the canonical physical `Housing_Listings` contract. Full-row operations must use the 48-column A:AV schema; ownership and business workflow remain outside the shared client. Verified Inventory Phase-1 Stage-1/2 write ranges are A:D and F:AO; E, AP:AT, AU, and AV are protected/reserved. AU and AV must remain blank.

## Google Maps

`shared/google_maps/` is a reusable technical adapter. Inventory decides when Maps is required. The adapter uses `GOOGLE_MAPS_API_KEY` or the approved local Keychain credential, resolves through the Google Geocoding API, and returns a structured `MapsResolution`. `resolve()` is keyword-only. Inventory accepts only `VERIFIED` as a successful Maps enrichment; `PARTIAL_MATCH`, `NEEDS_RUNTIME_VERIFICATION`, and `NOT_FOUND` are recorded as informational issues and do not by themselves convert an otherwise valid deterministic extraction to `Needs Review`.

## WhatsApp / WhAPI

`shared/whatsapp_whapi/` must retain an explicit live-traffic gate. No live WhAPI network operation should happen without the deliberate runtime approval mechanism. Webhook event names must be discovered from the current allowed-events endpoint rather than guessed from historical configuration.

## Credentials

`shared/credentials/` is the canonical local macOS Keychain provider. Secret values must never be committed.

## Documentation

- `docs/` is the canonical home for permanent business and system knowledge.
- Every implementation must review every maintained root document and every document inside `docs/` against resulting repository reality.
- Update every affected document in the same work session.
- Update `HANDOFF.md` whenever current working state changes.
- Use `DOCUMENT_UPDATE_MATRIX.md` and `DOCUMENT_GOVERNANCE.md` for document ownership and routing.
- Do not create duplicate authoritative documents.

## CRM workstream

- The canonical CRM implementation repository is this repository, `efps-internal-automatios`.
- Legacy CRM planning/extraction repositories are evidence only unless their contents are explicitly migrated and reconciled.
- D01–D04 are approved design decisions; D05 is proposed until the owner approves it.
- Figma is the working visual design environment; Canva remains the visual reference.
- Prototype work uses synthetic data and must not mutate live CRM/inventory records until a later explicit integration gate.
- Do not declare one universal lead source of truth while historical backups, legacy `leads.db`, the live Leads Tracker, and current DynamoDB lead domains remain unreconciled.

## Security

- Never commit secrets, API tokens, passwords, private keys, or production authentication material.
- Do not expose production data merely to simplify implementation.
- Document verified resource identifiers without storing secret values.

## Validation

A change is complete only when implementation, verification, validation, and documentation checks are complete and there are no known contradictions with repository truth. The read-only model audit must distinguish expected projections from populated source conflicts and protected-column changes. Populated conflicts are not resolved by changing deterministic rules to match historical Sheet values.
