# Cloudinary Shared Service

Provides the reusable technical media-storage capability used by EFPS modules.

## Responsibility

This layer handles technical media storage after a module decides that media must be stored. It provides:

- deterministic media public IDs
- image/media upload
- secure media URL retrieval from the Cloudinary response
- non-overwriting uploads (`overwrite=False`)
- separate namespaces for property photos and lead/enquiry media
- stable media references that an owning module can persist
- SHA-256 media fingerprints when callers need deterministic duplicate detection
- a catalogue URL helper limited to the verified ten-image legacy limit

The business module decides **when**, **why**, and **which** media is uploaded. Cloudinary does not decide listing status, catalogue eligibility, customer workflow, or business rules.

## Credential resolution

| Item | Current value |
|---|---|
| Keychain service | `efps-whapi-panel-cloudinary` |
| Keychain account | `efps` |
| Historical AWS source | `efps-whapi-panel-cloudinary` |
| Accepted environment fallback | `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`, `CLOUDINARY_URL` |

The current repository resolves the canonical local macOS Keychain service before using environment fallback. Secret values are never stored in GitHub.

## Legacy compatibility retained

The legacy implementation used deterministic property IDs in the form `properties/{listing_id}/photo_{n}` and a separate `leads/{phone}/...` namespace. The new shared helpers preserve that separation. Property image URLs can therefore be generated without putting any property workflow logic into this shared package.

## Usage boundary

A module supplies the bytes, immutable business identifier, and image index. The shared function uploads the media and returns the Cloudinary `secure_url` plus the deterministic public ID. The module decides how returned URLs are persisted or used.

For Inventory Phase 1, media recognition/counting occurs during Stage 1, while binary media upload is a downstream technical operation performed through this shared capability. The current inventory webhook path does not automatically upload every received media item into Cloudinary; live upload acceptance therefore validates the shared Cloudinary path and deterministic property namespace, not an end-to-end automatic media trigger from the WhAPI webhook.

## Live Inventory Phase-1 acceptance

Live runtime acceptance has been verified through the actual application credential path. A temporary in-memory 1x1 PNG was uploaded successfully using the canonical local Keychain credentials and the real Cloudinary account.

Verified acceptance facts:

- credentials loaded through `CloudinaryClient()` application path
- one real media upload succeeded
- deterministic property public ID was `properties/EFPS-LIVE-CLOUDINARY-TEST/photo_1`
- returned upload index was `1`
- returned `secure_url` was present and HTTPS
- upload used the shared `overwrite=False` safety behavior
- no Google Sheet write was performed by the acceptance test

This proves live Cloudinary account access and the shared upload contract. It does not by itself prove automatic media download/association from the Inventory WhAPI webhook or persistence into `cloudinary_image_urls`; those remain separate integration concerns unless explicitly implemented and verified.

## Runtime status

The shared Cloudinary technical path and live account access are verified. The Inventory Phase-1 automatic media-to-Cloudinary association path remains unverified because the current webhook implementation recognizes/counts media but does not download or upload its binary payload automatically.
