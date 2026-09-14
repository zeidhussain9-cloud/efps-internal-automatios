# Open Pointers

This is the canonical list of unresolved decisions and verified unknowns. Unknowns are never guessed.

## Resolved
- Housing_Listings spreadsheet/worksheet and 48-column A:AV contract are verified from the legacy repository.
- The older legacy `src/schema.py` was 47/AU; the newer `docs/SHEET_CONTRACT.json` is the verified 48/A:AV contract used by the new repository.
- WhAPI inventory listener sender numbers are `917975102130` and `919902024973`.
- Phase 1 now has a dedicated `NEW`→`NEW` inventory boundary, deterministic extraction, normalization, shared Maps capability, validation, AI verification, and wording-only beautification.
- `shared/google_maps/` is implemented; `shared/slack/` is a placeholder only.

## Runtime verification required
- Actual AWS secret values remain unavailable by design.
- Exact live WhAPI channel/connected number, deployed webhook URL, event subscription state, and live webhook test require runtime/WhAPI verification.
- Google Sheets authorization and safe live access require runtime verification.
- Google Maps API access requires `GOOGLE_MAPS_API_KEY` at runtime; the code explicitly reports unverified state instead of guessing.
- Vertex/Gemini access requires the configured Google service account and AI enable flags at runtime.

## Deferred by Phase boundary
- Production WhAPI media downloads and Cloudinary association.
- Inventory lifecycle/locking and duplicate governance.
- Batch/live orchestration beyond the explicit Phase-1 webhook path.
- Meta catalogue, Housing.com, website, and Slack integrations.

## Governance
When any pointer is resolved, update this document and affected architecture/contracts/handoff in the same implementation session.
