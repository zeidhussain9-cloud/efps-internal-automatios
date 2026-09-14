# Cloudinary Shared Service

Provides the reusable technical media-storage capability used by EFPS modules.

## Responsibility

This layer handles the technical storage of images/media after a module decides that media must be stored. It provides:

- deterministic media storage paths
- image upload
- secure media URL retrieval
- idempotent uploads where the same logical media should not be duplicated
- separate namespaces for property photos and lead/enquiry media
- stable media references that can be stored by an owning module
- image fingerprinting when callers need stable duplicate detection

The business module decides **when**, **why**, and **which** media is uploaded. Cloudinary does not decide listing status, catalogue eligibility, customer workflow, or business rules.

## Verified AWS/runtime credential map

| Shared capability | Verified AWS secret | Verified local/runtime name |
|---|---|---|
| Cloudinary | `efps-whapi-panel-cloudinary` | `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`, `CLOUDINARY_URL` |

Secret values are never stored in GitHub.

## EFPS use case verified from `efps-platform`

The legacy `efps-whapi-panel` uploaded WhatsApp property media immediately because WhAPI media links can expire. Property images were stored under deterministic paths derived from the immutable listing ID, and stored URLs were used for catalogue media. The same legacy implementation separated customer/enquiry images under a `leads/` namespace keyed by phone and message ID.

## Implementation

The shared package contains a dependency-injected Cloudinary client plus deterministic property/lead media helpers, catalogue URL limiting, image fingerprinting, offline tests, package metadata, and an explicit runtime credential contract.

## Boundary

This folder owns Cloudinary technical access only. Business modules own media-selection rules, listing semantics, catalogue rules, and workflow decisions.
