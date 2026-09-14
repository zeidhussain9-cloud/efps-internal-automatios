# Infrastructure Registry

This is the canonical registry for external systems and verified resource identifiers used by EFPS Internal Automations. Never store secrets, tokens, passwords, or private keys here.

## Current repository

- GitHub repository: `zeidhussain9-cloud/efps-internal-automatios`
- Default branch: `main`

## Active shared capability

- `shared/cloudinary/` — the only active shared capability in the current repository scope.

## Reserved future boundaries

The following systems may be integrated later, but are **not active shared implementations in the current repository state** unless and until explicitly established and verified:

- Google Sheets
- WhatsApp / WhAPI
- Meta / WhatsApp Catalogue
- Housing.com
- EFPS website infrastructure

## Secret policy

Secret names may be documented when useful. Secret values must never be stored in this file or committed to the repository.
