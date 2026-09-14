# Open Pointers

This is the canonical list of unresolved decisions and verified unknowns. Unknowns are never guessed.

## Resolved
- `Housing_Listings` is a 48-column A:AV contract using the latest supplied physical column order; `shared/google_sheets/schema.py` is the canonical implementation.
- WhAPI inventory listener sender numbers are `917975102130` and `919902024973`.
- Inventory has three top-level stages: **Stage 1 Initial / Webhook**, **Stage 2 Deterministic Extraction / Property Processing**, and **Stage 3 Downstream Operations**. Stage-2 extraction, normalization, Maps, validation, AI verification and AI beautification are sub-steps, not additional top-level stages.
- Stage-1/2 inventory writes protect `listing_state` (E), Housing downstream fields AP:AR, Meta downstream fields AS:AT, and `inventory_locked` (AV).
- `shared/google_maps/` is implemented; `shared/slack/` is a placeholder only.

## Runtime verification required
- Actual AWS secret values remain unavailable by design.
- Exact live WhAPI channel/connected number, deployed webhook URL, event subscription state, and live webhook test require runtime/WhAPI verification.
- Google Sheets authorization and safe live access require runtime verification.
- Google Maps API access requires `GOOGLE_MAPS_API_KEY` at runtime; the code reports unverified state instead of guessing.
- Vertex/Gemini access requires the configured Google service account and AI enable flags at runtime.

## Unverified sheet controls
- Exact Google Sheet dropdown vocabularies for `preferred_tenant_type`, `bachelor_preference`, and `pet_friendly` are not claimed from repository source.
- Exact `inventory_locked` sheet control vocabulary is not claimed from repository source.

## Deferred by Phase boundary
- Production WhAPI media downloads and Cloudinary association.
- Inventory lifecycle/locking implementation.
- Batch/live orchestration beyond the explicit intake path.
- Meta Catalogue, Housing.com, website, and Slack runtime integrations.

## Governance
When any pointer is resolved, update this document and affected architecture/contracts/handoff in the same implementation session.
