# Cloudinary Shared Service

Provides the reusable technical media-storage capability used by EFPS modules.

## What Cloudinary achieves

This layer handles the technical storage of images/media after a module decides that media must be stored. It provides:

- deterministic media storage paths
- image upload
- secure media URL retrieval
- idempotent uploads where the same logical media should not be duplicated
- separate namespaces for property photos and lead/enquiry media
- stable media references that can be stored by an owning module
- image fingerprinting when callers need stable duplicate detection

The business module still decides **when**, **why**, and **which** media is uploaded. Cloudinary does not decide listing status, catalogue eligibility, customer workflow, or business rules.

## EFPS use case verified from `efps-platform`

The legacy `efps-whapi-panel` uploaded WhatsApp property media to Cloudinary immediately because WhAPI media links can expire. Property images were stored under deterministic paths derived from the immutable listing ID, and stored URLs were used for catalogue media. fileciteturn228file0L2-L2

The same legacy implementation separated customer/enquiry images under a `leads/` namespace keyed by phone and message ID, preventing enquiry media from colliding with property media. fileciteturn228file0L2-L2

## Implementation

The shared package currently contains a dependency-injected Cloudinary client plus deterministic property/lead media helpers, catalogue URL limiting, image fingerprinting, offline tests, package metadata, and an explicit runtime credential contract.

## Credentials

Cloudinary credentials are runtime secrets/configuration and must never be committed. The legacy implementation resolved Cloudinary credentials from AWS Secrets Manager with environment-variable fallback during local development. fileciteturn229file0L2-L2

The current shared package expects:

- `CLOUDINARY_CLOUD_NAME`
- `CLOUDINARY_API_KEY`
- `CLOUDINARY_API_SECRET`

The actual values must be supplied only at runtime through the approved secret/configuration mechanism.

## Boundary

This folder owns Cloudinary technical access only. Business modules own media-selection rules, listing semantics, catalogue rules, and workflow decisions.
