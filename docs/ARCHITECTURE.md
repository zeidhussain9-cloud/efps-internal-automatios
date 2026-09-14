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

Reusable media-storage and upload capability. It provides deterministic media naming, uploads, stable media references, catalogue URL preparation, and image fingerprinting. Verified legacy AWS secret: `efps-whapi-panel-cloudinary`.

### `shared/google_sheets/`

Reusable Google Sheets technical access plus the canonical `Housing_Listings` contract/schema. Verified spreadsheet: `1zdOLWklkWlnVECCtcH4SJj6vm6nEVjINpTT2U2UJEKc`, worksheet `Housing_Listings`; verified AWS secret: `efps-whapi-panel-sheet`.

The local canonical schema is `shared/google_sheets/schema.py`. The verified machine-readable legacy contract is 48 columns, A:AV, with `inventory_locked` at AV. The older legacy `src/schema.py` table stopped at AU; the generated `SHEET_CONTRACT.json` is the newer contract used for the correction.

### `shared/whatsapp_whapi/`

Reusable WhAPI technical integration: connection/authentication, API transport, webhook registration/receiving/verification, normalized message/media data, configured inventory-listener source numbers, and live-traffic safety controls. Verified AWS secret: `efps-whapi-panel-token`; base URL: `https://gate.whapi.cloud`.

The reviewed legacy flow is:

`WhatsApp → WhAPI channel → public Lambda Function URL webhook → query-token verification → payload normalization → inventory-listener or ordinary-direct-message routing → owning business module`.

The legacy deployment configured two inventory-listener sender numbers (`917975102130`, `919902024973`). The legacy auth documentation describes one token = one WhAPI channel = one connected WhatsApp number, so these two numbers are treated as sender-routing configuration, not two proven WhAPI channels. fileciteturn386file0L2-L2

The webhook acknowledged quickly and could hand slow processing to a separate asynchronous Lambda. fileciteturn377file0L2-L2 fileciteturn379file0L2-L2

## Business modules

### `modules/efps-inventory-mgmnt/`

Owns property inventory business logic, inventory workflows, validation, updates, duplicate handling, and inventory-specific coordination with shared services.

### `modules/efpd-lead-mgmnt/`

Owns lead/enquiry business logic, conversation workflow, lead state, assignment, and lead-specific processing. It is intentionally separate from inventory management.

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

## Data and ownership principle

Modules own business meaning. Shared services own technical access and reusable cross-module contracts where explicitly established. A shared service must not decide which property to publish, what a listing means, which customer communication should happen, or whether a business action is authorized.

Concrete live runtime state must be verified from the deployed AWS/WhAPI environment; GitHub source alone cannot prove the current production webhook URL or channel settings.
