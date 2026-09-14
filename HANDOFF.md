# EFPS Internal Automations — Current Handoff

## Current state

Phase 1 of `efps-inventory-mgmnt` is implemented in the new repository, using the legacy `efps-platform` inventory as a source of business rules while keeping reusable technical capabilities in `shared/`.

Phase 1 boundary: dedicated two-number WhAPI intake → `NEW` to `NEW` property session → raw text → deterministic extraction → normalization → shared Google Maps resolution → validation → optional Vertex/Gemini verification → wording-only AI beautification.

## Phase-1 implementation

- `modules/efps-inventory-mgmnt/src/intake.py` implements the explicit `NEW` boundary and ignores media binary downloads.
- `extract.py` migrates the deterministic prescan contract.
- `normalize.py` migrates safe legacy normalization/default rules.
- `validate.py` enforces the canonical Phase-1 row rules.
- `listing_id.py` preserves `EF-YYMM-XXXX` immutable IDs.
- `pipeline.py` orchestrates Phase 1 without touching downstream-owned AK:AO fields.
- `ai.py` provides advisory contradiction verification and wording-only beautification, both fail-safe.
- `webhook.py` connects the dedicated listener to the Phase-1 pipeline.

## Shared additions

- `shared/google_maps/` is implemented as the reusable Maps technical capability.
- `shared/slack/` exists as a Phase-1 placeholder only; no Slack runtime is implemented.
- `shared/google_sheets/schema.py` now records all 48 columns plus owner, first-population stage, allowed values, and declared dependencies.

## Canonical sheet

`Housing_Listings` is 48 columns A:AV. `listing_id` is immutable row identity. The deterministic extractor reads only `raw_message_text` for property facts. On a new property, downstream-owned AK:AO are left untouched/blank.

## Runtime verification still required

Actual AWS secrets, live WhAPI event subscription/webhook deployment, Google Maps API access, Google Sheets authorization, and Vertex/Gemini runtime access cannot be proven from source alone. Missing runtime state is treated as `NOT VERIFIED`, never guessed.

## Phase boundary

Phase 1 does not implement production media downloads/Cloudinary association, lifecycle/locking, duplicate governance, batch/live orchestration beyond the explicit intake path, Meta catalogue publishing, Housing.com publishing, website integration, or Slack integration.

## Next development rule

Do not enter Phase 2 until explicitly authorized. At the end of each implementation, review and update all maintained root/docs guidance and this handoff against repository reality.
