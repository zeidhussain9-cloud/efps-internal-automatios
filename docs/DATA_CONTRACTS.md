# Data Contracts

This is the canonical cross-module data ownership and contract reference for EFPS Internal Automations.

## Inventory contract

The inventory module is the business owner of canonical inventory data and inventory-specific decisions.

Any future spreadsheet or external data store remains a technical capability only when explicitly established; the shared layer must not decide inventory business rules.

## Media contract

Cloudinary is a reusable shared media capability. The inventory or other owning module decides when property images are uploaded and how resulting media references are used. The verified legacy implementation used deterministic listing-derived property paths and a distinct lead/enquiry media namespace. fileciteturn228file0L2-L2

## Google Sheets contract

`shared/google_sheets/` provides technical spreadsheet access only. The owning module remains responsible for spreadsheet meaning, field ownership, validation, duplicate handling, and the decision to read or write a range. Exact field-level contracts are not claimed here until established by the module implementation.

## WhatsApp / WhAPI contract

`shared/whatsapp_whapi/` provides technical transport and integration primitives only. Business modules own message meaning, workflow decisions, recipients, and business authorization. Live traffic must remain explicitly gated. fileciteturn223file0L2-L2

## Catalogue contract

The Meta catalogue module consumes approved inventory information for catalogue purposes. Catalogue-specific titles, descriptions, and publication decisions belong to the catalogue module, not to shared services.

## Current shared-capability rule

The `shared/` folder contains the established `cloudinary`, `google_sheets`, and `whatsapp_whapi` capability boundaries. A boundary being present does not imply every runtime feature is complete; implementation status must be stated and verified accurately.

## Contract maturity

Exact field-level schemas, write ownership, validation requirements, and cross-project contracts must be added only when they are established from an owner-approved source or an implemented and verified capability. Do not invent contract details.
