# Data Contracts

This document records cross-module data ownership and contracts that are established for the repository.

## Inventory contract

The inventory module is the business owner of canonical inventory data and inventory-specific decisions.

Google Sheets is a shared technical capability under `shared/google_sheets/`; the shared layer must not decide inventory business rules.

## Media contract

Cloudinary is a shared technical capability under `shared/cloudinary/`. The inventory module decides when property images are uploaded and how resulting media references are used.

## WhatsApp / WhAPI contract

WhatsApp/WhAPI is a shared technical capability under `shared/whatsapp_whapi/`. Modules decide why and when WhatsApp actions are used.

## Catalogue contract

The Meta catalogue module consumes approved inventory information for catalogue purposes. Catalogue-specific titles, descriptions, and publication decisions belong to the catalogue module, not to shared services.

Exact field-level schemas will be added when the relevant implementation establishes them.