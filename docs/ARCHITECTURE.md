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

### `shared/google_sheets/`

Reusable Google Sheets technical access: authenticated client setup plus worksheet/range read and write primitives. Modules remain responsible for what spreadsheet data means and which business operations trigger reads or writes.

### `shared/whatsapp_whapi/`

Reusable WhAPI technical access: authentication, API transport, webhook primitives, messaging/media primitives, connection/status handling, and related WhatsApp integration concerns. Business modules remain responsible for business workflow decisions. The legacy repository's WhAPI panel also used an explicit live-traffic gate so network calls could not happen without owner approval. fileciteturn223file0L2-L2

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

Concrete runtime flows and contracts must only be documented after implementation establishes them. Capability boundaries may exist before every feature is complete, but status must be stated accurately.
