# Cloudinary Shared Skill — EFPS

## Purpose

Use this repository-specific skill for all work involving `shared/cloudinary/`.

## Verified responsibility

Cloudinary is the reusable EFPS media infrastructure layer. It handles technical media storage and stable references after the owning module decides media should be stored.

Verified legacy patterns include:

- deterministic property media IDs such as `properties/{listing_id}/photo_{n}`
- separate lead/enquiry media namespace under `leads/`
- non-overwriting uploads for idempotent storage
- stable secure URLs returned to calling modules
- image fingerprinting for duplicate detection when required

The owning business module decides when, why, and which media is uploaded. Cloudinary does not decide business status, catalogue eligibility, or workflow.

## Credentials

Verified legacy AWS Secrets Manager secret:

`efps-whapi-panel-cloudinary`

Verified legacy supported runtime forms include Cloudinary cloud name, API key, API secret, or a `CLOUDINARY_URL` representation. Current shared environment names are:

- `CLOUDINARY_CLOUD_NAME`
- `CLOUDINARY_API_KEY`
- `CLOUDINARY_API_SECRET`

Never commit credential values.

## Verification

Before changing the shared contract, inspect `shared/cloudinary/` and the verified legacy media implementation. Use injected/offline tests before considering the capability validated. Live uploads require runtime credentials and explicit runtime verification.

## Documentation

For every implementation, review all maintained root documents and every document in `docs/`, updating all affected sources and `HANDOFF.md` as required.
