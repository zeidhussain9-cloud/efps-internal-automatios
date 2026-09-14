# EFPS Internal Automations — Current Handoff

## Current state

The inventory workflow in the new repository is organized into three top-level stages:

1. **Stage 1 — Initial / Webhook**: dedicated inventory listener → `NEW` property-session boundary → raw capture → initial row.
2. **Stage 2 — Deterministic Extraction / Property Processing**: deterministic extraction → normalization/business rules → Maps resolution → validation → optional AI verification → wording-only AI beautification.
3. **Stage 3 — Downstream Operations**: Housing Portal, Meta Catalogue, and lifecycle/control consume the processed inventory record and own their fields.

Stage-2 items are processing sub-steps, not separate top-level stages. Google Sheets persistence is a transport/output operation, not an additional stage.

## Stage-1/2 implementation

- `intake.py` implements the explicit `NEW` boundary, dedicated-listener filtering, and message-ID idempotency within an active session.
- `extract.py` performs deterministic extraction from completed `raw_message_text`.
- `normalize.py` contains the migrated deterministic normalization/business rules, including furnishing defaults, carpet derivation, maintenance handling, property subtype normalization, internal property type/amenity rules, and tenant/bachelor dependency.
- `validate.py` enforces the canonical 48-field shape, fixed values, deterministic validation, and downstream write protection.
- `listing_id.py` preserves immutable `EF-YYMM-XXXX` IDs.
- `pipeline.py` orchestrates Stage 2 and writes only Stage-1/2-owned fields.
- `ai.py` remains advisory: it cannot replace deterministic facts or bypass a failed validation gate.
- `webhook.py` connects the normalized WhAPI inventory message to the Stage-1/2 pipeline and persists raw text at current column G.
- `batch.py` provides a deterministic-first Phase-1 batch path for existing canonical rows with `intake_status = Raw` and populated `raw_message_text`.

## Canonical sheet

`Housing_Listings` is exactly 48 columns A:AV in the latest supplied order. `shared/google_sheets/schema.py` is the canonical physical contract. Housing owns AP:AR; Meta owns AS:AT. Stage-1/2 writes are restricted to A:D, F:AO, and AU. E (`listing_state`), AP:AT, and AV (`inventory_locked`) are protected from this path.

## Current verified business-rule constraints

- Internal property type values: `Gated Community`, `Semi Gated`, `Standalone`.
- Gated-community defaults and semi-gated defaults are migrated from the legacy repository.
- Family/family-only tenant preference deterministically forces `Not Allowed` for bachelor preference unless an explicit source value is present in source text.
- Exact preferred-tenant, bachelor-preference, pet-friendly, and inventory-lock sheet dropdown vocabularies are treated as runtime/documentation boundaries unless verified by the current canonical contract.

## Slack Phase-1 boundary

- `shared/slack/` is the canonical shared Slack capability.
- Slack is an operational interface; `Housing_Listings` remains the source of truth.
- Phase-1 Slack includes batch control/reporting, property verification, runtime/bug reporting, and the temporary manual bulk-photo path.
- The current webhook does not reliably persist inbound photo binaries with property association. Therefore photos are temporarily associated through the exact Slack property thread and then uploaded to Cloudinary.
- Society approval is explicitly obsolete and excluded. Do not add society approval commands, queues, cards, or a society approval state.
- The shared Slack capability is source-implemented, but production Slack deployment/live verification remains a separate acceptance step.

## Runtime verification still required

Actual AWS secrets, live WhAPI event subscription/webhook deployment, Google Maps API access, Google Sheets authorization, Vertex/Gemini runtime access, Cloudinary upload access, and Slack endpoint/installation state cannot be proven from source alone. Missing runtime state remains `NOT VERIFIED` and is never guessed.

## Phase-1 production target

The next acceptance target is a production-grade Inventory Phase-1 path capable of safely processing the existing `Housing_Listings` rows requested for deterministic migration/testing, including rows 2–26. The batch path must preserve downstream-owned fields, stop on required verification failures, and leave the canonical row explicitly reviewable rather than guessing missing facts.

See `shared/slack/RELEASE_GATE.md` for the complete Phase-1 acceptance gate and `shared/slack/PHASE1_BULK_PHOTOS.md` for the temporary photo workflow.

## Next development rule

Do not enter additional downstream publishing/media phases beyond the authorized Phase-1 photo path until explicitly authorized. At the end of each implementation, review maintained root/docs guidance and this handoff against repository reality.
