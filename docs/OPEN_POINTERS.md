# Open Pointers

This is the canonical list of unresolved decisions and verified unknowns. Unknowns are never guessed.

## Resolved
- `Housing_Listings` is a 48-column A:AV contract using the latest supplied physical column order; `shared/google_sheets/schema.py` is the canonical implementation.
- WhAPI inventory listener sender numbers are `917975102130` and `919902024973`.
- Inventory has three top-level stages: **Stage 1 Initial / Webhook**, **Stage 2 Deterministic Extraction / Property Processing**, and **Stage 3 Downstream Operations**. Stage-2 extraction, normalization, Maps, validation, AI verification and AI beautification are sub-steps, not additional top-level stages.
- Stage-1/2 inventory writes protect `listing_state` (E), Housing downstream fields AP:AR, Meta downstream fields AS:AT, and `inventory_locked` (AV).
- `shared/google_maps/` is implemented.
- `shared/slack/` is source-implemented as a reusable operational capability; production deployment and live verification remain separate acceptance steps.
- AWS Secrets Manager was removed from the current runtime credential path. Seven required local macOS Keychain services were migrated and locally hash-verified as exact matches; repository source records only service names and non-sensitive identifiers.

## Runtime verification required
- Google Sheets authorization and safe live read/write against the canonical spreadsheet remain `NOT VERIFIED`.
- Google Maps API access and a real resolution probe remain `NOT VERIFIED`.
- WhAPI live channel identity, connected-number state, webhook URL, event subscription state, and live webhook test remain `NOT VERIFIED`.
- Cloudinary account access and a safe live upload remain `NOT VERIFIED`.
- Slack app installation, bot membership, command registration, endpoint deployment, signature verification in the target runtime, and live API probe remain `NOT VERIFIED`.
- Housing Portal production integration remains `NOT IMPLEMENTED` in this repository and requires explicit implementation requirements before it can be completed.
- Meta Catalogue production integration remains `NOT IMPLEMENTED` in this repository and requires explicit implementation requirements before it can be completed.

## Unverified sheet controls
- Exact Google Sheet dropdown vocabularies for `preferred_tenant_type`, `bachelor_preference`, and `pet_friendly` are not claimed from repository source.
- Exact `inventory_locked` sheet control vocabulary is not claimed from repository source.

## Deferred by Phase boundary
- Production WhAPI media downloads and direct Cloudinary association.
- Inventory lifecycle/locking implementation.
- Batch/live orchestration beyond the explicit intake path.
- Meta Catalogue, Housing.com, and website production integrations until their implementation requirements are explicitly authorized and established.

## Governance
When any pointer is resolved, update this document and affected architecture/contracts/handoff in the same implementation session.
