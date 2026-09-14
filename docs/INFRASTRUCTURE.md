# Infrastructure Registry

This is the canonical registry for external systems and verified resource identifiers used by EFPS Internal Automations. Never store secrets, tokens, passwords, or private keys here.

## Current repository

- GitHub repository: `zeidhussain9-cloud/efps-internal-automatios`
- Default branch: `main`

## Active shared capability

- `shared/cloudinary/` — currently active shared technical capability for Cloudinary media operations.

## External service boundaries

Future integration boundaries may include:

- Google Sheets
- Cloudinary
- WhatsApp / WhAPI
- Meta / WhatsApp Catalogue
- Housing.com
- EFPS website infrastructure

Except for the explicitly active Cloudinary shared capability, these remain reserved boundaries until their implementation is actually established and verified.

## Secret policy

Secret names may be documented when useful. Secret values must never be stored in this file or committed to the repository.
