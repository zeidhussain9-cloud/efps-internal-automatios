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

## Verified AWS/runtime credential map

| Shared capability | Verified AWS secret | Verified local/runtime name |
|---|---|---|
| Cloudinary | `efps-whapi-panel-cloudinary` | `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`, `CLOUDINARY_URL` |

`CLOUDINARY_CLOUD_NAME` is also accepted when the deployment supplies the cloud name separately. Secret values are never stored in GitHub.

## Legacy compatibility retained

The legacy implementation used deterministic property IDs in the form `properties/{listing_id}/photo_{n}` and a separate `leads/{phone}/...` namespace. The new shared helpers preserve that separation. Property image URLs can therefore be generated without putting any property workflow logic into this shared package.

## Usage boundary

A module supplies the bytes, immutable business identifier, and image index. The shared function uploads the media and returns the Cloudinary `secure_url` plus the deterministic public ID. The module decides how returned URLs are persisted or used.

## Runtime status

The package is statically implemented and testable with dependency injection. Actual Cloudinary account access and credentials remain runtime verification items; repository code alone cannot prove the live account is reachable.
