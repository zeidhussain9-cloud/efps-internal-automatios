# EFPS Internal Automations — Architecture

This is the canonical cross-repository architecture reference.

## Core model

The repository has two primary capability layers:

- `shared/` — reusable technical capabilities and integrations.
- `modules/` — EFPS business capabilities and business decisions.

The governing boundary is:

> Shared services provide capabilities; modules decide when and why those capabilities are used.

Shared code must remain business-neutral. Business rules, publishing decisions, property decisions, and workflow decisions belong to the owning module.

## Shared capabilities

### `shared/google_sheets/`

Technical capability for Google Sheets access and reusable spreadsheet operations.

### `shared/cloudinary/`

Technical capability for media upload and media URL operations.

### `shared/whatsapp_whapi/`

Technical capability for WhatsApp/WhAPI connection, authentication, API access, webhooks, messages, media, contacts, groups, configured numbers, and connection health/status.

## Business modules

### `modules/efps-inventory-mgmnt/`

Owns property inventory business logic, inventory workflows, validation, updates, duplicate handling, and inventory-specific coordination with shared services.

### `modules/efps-meta-catalogue-mgmnt/`

Owns Meta/WhatsApp catalogue business logic, catalogue content, publishing decisions, and catalogue-specific status handling.

### `modules/efps-housing-portal-mgmnt/`

Reserved for future Housing.com automation and portal-specific business workflows.

### `modules/efps-website-mgmnt/`

Dedicated exclusively to EasyFind website management and website automation.

## Data and ownership principle

Modules own business meaning. Shared services own technical access. A shared service must not decide which property to publish, what a listing means, which customer communication should happen, or whether a business action is authorized.

Exact runtime flows and contracts will be added only when implementation establishes them. This document must not claim workflows that do not exist.
