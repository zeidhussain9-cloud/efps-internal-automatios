# EFPS Internal Automations — Architecture

This is the canonical cross-repository architecture reference.

## Core model

The repository has two primary capability layers:

- `shared/` — reusable technical capabilities and integrations.
- `modules/` — EFPS business capabilities and business decisions.

The governing boundary is:

> Shared services provide capabilities; modules decide when and why those capabilities are used.

Shared code must remain business-neutral. Business rules, publishing decisions, property decisions, and workflow decisions belong to the owning module.

## Established shared capabilities

### `shared/cloudinary/`

Reusable media-storage and upload capability. It provides deterministic media naming, uploads, stable media references, catalogue URL preparation, and image fingerprinting. The legacy `efps-platform` implementation demonstrates property-image storage under listing-derived paths and a separate `leads/` namespace for enquiry media. fileciteturn228file0L2-L2

Verified legacy AWS secret reference: `efps-whapi-panel-cloudinary`. fileciteturn315file0L2-L2

### `shared/google_sheets/`

Reusable Google Sheets technical access plus the canonical `Housing_Listings` contract/schema. The shared layer owns the physical sheet definition and technical access; business modules decide which business workflow causes a read/write.

Verified legacy spreadsheet: `1zdOLWklkWlnVECCtcH4SJj6vm6nEVjINpTT2U2UJEKc`, worksheet `Housing_Listings`. Verified legacy AWS secret: `efps-whapi-panel-sheet`. fileciteturn315file0L2-L2

The local canonical schema is `shared/google_sheets/schema.py`. The verified legacy source is `efps-platform/modules/efps-whapi-panel/src/schema.py`, with the machine-readable export in `efps-platform/docs/SHEET_CONTRACT.json`.

### `shared/whatsapp_whapi/`

Reusable WhAPI technical integration: connection, authentication, API transport, webhook registration/receiving/verification, message and media primitives, contact/group primitives, configured connection metadata, webhook configuration, and health/status. Business modules remain responsible for business workflow decisions.

Verified legacy AWS secret: `efps-whapi-panel-token`; verified base URL: `https://gate.whapi.cloud`. Live network access must remain behind the explicit runtime approval gate. fileciteturn315file0L2-L2 fileciteturn223file0L2-L2

## Business modules

### `modules/efps-inventory-mgmnt/`

Owns property inventory business logic, inventory workflows, validation, updates, duplicate handling, and inventory-specific coordination with shared services.

### `modules/efps-meta-catalogue-mgmnt/`

Owns Meta/WhatsApp catalogue business logic, catalogue content, publishing decisions, and catalogue-specific status handling.

### `modules/efps-housing-portal-mgmnt/`

Reserved for future Housing.com automation and portal-specific business workflows.

### `modules/efps-website-mgmnt/`

Dedicated exclusively to EasyFind website management and website automation.

## Shared-capability skill model

The three established shared capabilities each have a repository-specific Gemini skill:

- `.gemini/skills/cloudinary/`
- `.gemini/skills/google-sheets/`
- `.gemini/skills/whapi/`

These skills provide technical capability guidance. They do not move business decisions out of the owning modules.

## Data and ownership principle

Modules own business meaning. Shared services own technical access and reusable cross-module contracts where explicitly established. A shared service must not decide which property to publish, what a listing means, which customer communication should happen, or whether a business action is authorized.

Concrete runtime flows and contracts must only be documented after implementation establishes them. Capability boundaries may exist before every feature is complete, but status must be stated accurately.
