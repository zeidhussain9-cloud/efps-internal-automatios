# Open Pointers

This is the canonical list of unresolved decisions and verified unknowns for the new repository.

These are not instructions to guess or silently fix. An open pointer is a human-owned decision or a fact that still needs verification.

## Current pointers

- Exact implementation contracts for each module are not yet established.
- Exact Google Sheets inventory schema for any future implementation must be established from the current owner-approved source before implementation.
- Exact Cloudinary production resource configuration must be verified before live integration work.
- Any future WhatsApp / WhAPI production connection/resource identifiers must be verified before live integration work; no WhatsApp/WhAPI shared implementation is currently active.
- Cross-project ownership rules for any shared inventory sheet must be established before multiple modules write to the same dataset.
- Website technical stack and deployment contract must be established before website automation is implemented.

## Current shared-scope truth

The only active shared implementation scope is `shared/cloudinary/`.

Any other shared capability is a reserved future boundary, not current implementation truth, until explicitly established and verified.

When a pointer is resolved, update this document during the same work session and update the relevant architecture, business, contract, or infrastructure documentation.
