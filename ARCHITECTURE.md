# EFPS Internal Automations — Architecture

## Repository model

The repository has two primary layers:

- `shared/` — reusable technical capabilities and integrations.
- `modules/` — EFPS business capabilities and business decisions.

Shared capabilities provide capabilities; modules decide when and why those capabilities are used.

## Shared services

### `shared/google_sheets/`
Technical capability for Google Sheets access and reusable spreadsheet operations.

### `shared/cloudinary/`
Technical capability for media upload and media URL operations.

### `shared/whatsapp_whapi/`
Technical capability for WhatsApp/WhAPI connection, authentication, API access, webhooks, messages, media, contacts, groups, configured numbers, and health/status.

## Modules

### `modules/efps-inventory-mgmnt/`
Business owner for property inventory workflows, inventory validation, inventory updates, duplicate handling, and inventory-specific coordination with shared services.

### `modules/efps-meta-catalogue-mgmnt/`
Business owner for Meta/WhatsApp catalogue workflows, catalogue content, publishing decisions, and catalogue-specific status handling.

### `modules/efps-housing-portal-mgmnt/`
Reserved for Housing.com automation and portal-specific business workflows.

### `modules/efps-website-mgmnt/`
Dedicated business module for EasyFind website management and automation.

## Cross-module rule

A shared integration must remain business-neutral. It must not decide which property should be published, which listing status means what, or which customer communication should happen. Those decisions belong to the owning module.

## Data flow

Exact runtime flows will be documented when concrete implementations are built. This skeleton deliberately does not claim workflows that do not yet exist in the new repository.