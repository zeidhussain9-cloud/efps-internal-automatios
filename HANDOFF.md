# EFPS Internal Automations — Current Handoff

## Current state

The inventory workflow in the new repository is organized into three top-level stages:

1. **Stage 1 — Initial / Webhook**: dedicated inventory listener → `NEW` property-session boundary → raw capture → initial row.
2. **Stage 2 — Deterministic Extraction / Property Processing**: deterministic extraction → normalization/business rules → Maps resolution → validation → optional AI verification → wording-only AI beautification.
3. **Stage 3 — Downstream Operations**: Housing Portal, Meta Catalogue, and lifecycle/control consume the processed inventory record and own their fields.

Stage-2 items are processing sub-steps, not separate top-level stages. Google Sheets persistence is a transport/output operation, not an additional stage.

## Stage-1/2 implementation

- `modules/efps-inventory-mgmnt/src/intake.py` implements the explicit `NEW` boundary, dedicated-listener filtering, and message-ID idempotency within an active session.
- `extract.py` performs deterministic extraction from completed `raw_message_text`.
- `normalize.py` contains the migrated deterministic normalization/business rules, including furnishing defaults, carpet derivation, maintenance handling, property subtype normalization, internal property type/amenity rules, and tenant/bachelor dependency.
- `validate.py` enforces the canonical 48-field shape, fixed values, deterministic validation, and downstream write protection.
- `listing_id.py` preserves immutable `EF-YYMM-XXXX` IDs.
- `pipeline.py` orchestrates Stage 2 and writes only Stage-1/2-owned fields.
- `ai.py` remains advisory: it cannot replace deterministic facts or bypass a failed validation gate.
- `webhook.py` connects the normalized WhAPI inventory message to the Stage-1/2 pipeline and persists raw text at its current column G.

## Canonical sheet

`Housing_Listings` is exactly 48 columns A:AV in the latest supplied order. `shared/google_sheets/schema.py` is the canonical physical contract. Current downstream boundary is AP:AT: Housing owns AP:AR and Meta owns AS:AT. Stage-1/2 inventory writes protect E (`listing_state`), AP:AT, and AV (`inventory_locked`).

## Current verified business-rule constraints

- Internal property type values: `Gated Community`, `Semi Gated`, `Standalone`.
- Gated-community defaults and semi-gated defaults are migrated from the legacy repository.
- Family/family-only tenant preference deterministically forces `Not Allowed` for bachelor preference unless an explicit source value is present.
- Exact preferred-tenant, bachelor-preference, and pet-friendly sheet dropdown vocabularies are not claimed because they are not verified in repository source.

## Runtime verification still required

Actual AWS secrets, live WhAPI event subscription/webhook deployment, Google Maps API access, Google Sheets authorization, and Vertex/Gemini runtime access cannot be proven from source alone. Missing runtime state remains `NOT VERIFIED` and is never guessed.

## Phase boundary

This implementation does not activate production media downloads/Cloudinary association, lifecycle writers, Meta Catalogue publishing, Housing.com publishing, website integration, or Slack runtime. Their schema ownership is defined and protected, but downstream implementations remain separate.

## Next development rule

Do not enter additional downstream/media phases until explicitly authorized. At the end of each implementation, review and update maintained root/docs guidance and this handoff against repository reality.
