# Open Pointers

This is the canonical list of unresolved decisions and verified unknowns for the current Inventory Management Phase 1 scope. Unknowns are never guessed. Future Meta Catalogue and Housing Portal additions are outside the current Phase-1 scope and are not treated as open pointers here.

## Resolved

- `Housing_Listings` is a 48-column A:AV contract using the latest supplied physical column order; `shared/google_sheets/schema.py` is the canonical implementation.
- The production Google Sheets read and Stage-1/2 write boundary have been verified. Stage-1/2 writes are restricted to A:D, F:AO, and AU; E, AP:AT, and AV are protected.
- WhAPI inventory listener sender numbers are `917975102130` and `919902024973`.
- Inventory has three top-level stages: **Stage 1 Initial / Webhook**, **Stage 2 Deterministic Extraction / Property Processing**, and the **Stage 3 Downstream Operations boundary**. Stage-2 extraction, normalization, Maps, validation, AI verification and AI beautification are sub-steps, not additional top-level stages.
- `shared/google_maps/` is implemented and its live direct API access, application-path resolution, and Inventory Stage-2 consumption have been verified.
- The verified Maps path uses the dedicated local Keychain service `efps-google-maps-api-key` and `GOOGLE_MAPS_API_KEY` as the environment override; raw key values are not stored in the repository.
- The deterministic Inventory Phase-1 rules have been validated against the current inventory sample and the Stage-2 end-to-end path.
- AWS-to-local-Keychain migration of the seven baseline services was locally hash-verified as exact matches; repository source records only service names and non-sensitive identifiers.
- `shared/credentials/` is the canonical local macOS Keychain provider.
- The shared Cloudinary application path has passed live Inventory Phase-1 upload acceptance using the canonical local Keychain credential path; a real temporary image uploaded successfully with the deterministic property namespace and an HTTPS `secure_url` returned.

## Runtime verification required

- WhAPI live channel identity, connected-number state, webhook URL, event subscription state, and live webhook test remain `NOT VERIFIED`.
- Slack app installation, bot membership, command registration, endpoint deployment, signature verification in the target runtime, and live API probe remain `NOT VERIFIED`.
- Exact Google Sheet dropdown vocabularies for `preferred_tenant_type`, `bachelor_preference`, and `pet_friendly` remain `NOT VERIFIED`.
- Exact `inventory_locked` sheet control vocabulary remains `NOT VERIFIED`.

## Deferred by current Phase-1 boundary

- Production WhAPI media downloads and direct Cloudinary association beyond the currently authorized temporary photo workflow.
- Inventory lifecycle/locking implementation beyond the current protected-column boundary.
- Additional batch/live orchestration beyond the explicit Phase-1 intake and processing paths.
- Future Meta Catalogue, Housing Portal, and website production integrations until their implementation requirements are explicitly authorized and established. These are future additions, not current open pointers.

## Governance

When any pointer is resolved, update this document and the affected architecture/contracts/handoff in the same implementation session.
