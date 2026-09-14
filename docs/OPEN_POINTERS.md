# Open Pointers

This is the canonical list of unresolved decisions and verified unknowns for the new repository.

These are not instructions to guess or silently fix. An open pointer is a human-owned decision or a fact that still needs verification.

## Current pointers

- Exact implementation contracts for each module are not yet established.
- Exact Google Sheets inventory schema for any future implementation must be established from the current owner-approved source before module integration.
- Exact Cloudinary production resource configuration and approved runtime secret store must be verified before live integration work.
- Exact production WhatsApp / WhAPI connection/resource identifiers and current API behavior must be verified before live integration work.
- Cross-project ownership rules for any shared inventory sheet must be established before multiple modules write to the same dataset.
- Website technical stack and deployment contract must be established before website automation is implemented.

## Current shared-capability truth

The repository has established three shared capability boundaries:

- `shared/cloudinary/`
- `shared/google_sheets/`
- `shared/whatsapp_whapi/`

Their boundaries are established, but open pointers remain for production configuration, runtime credentials, and any behavior not yet verified. No agent may infer those values.

When a pointer is resolved, update this document during the same work session and update the relevant architecture, business, contract, or infrastructure documentation.
