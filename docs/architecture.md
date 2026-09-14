# Architecture

This document is the cross-module architecture reference for EFPS Internal Automations.

## Core boundary

Shared services provide technical capabilities; modules decide when and why those capabilities are used.

## Shared capabilities

- `google_sheets` — Google Sheets access and reusable spreadsheet operations.
- `cloudinary` — media upload and URL/media capabilities.
- `whatsapp_whapi` — WhatsApp/WhAPI connection, webhook, messaging, media, contact, and group capabilities.

## Business modules

- `efps-inventory-mgmnt` — owns inventory business logic and inventory workflows.
- `efps-meta-catalogue-mgmnt` — owns catalogue business logic and publishing workflows.
- `efps-housing-portal-mgmnt` — reserved for future Housing.com automation.
- `efps-website-mgmnt` — owns EasyFind website management and automation.

Detailed flows are intentionally limited at skeleton stage and will be added when implementation establishes the actual data movement.