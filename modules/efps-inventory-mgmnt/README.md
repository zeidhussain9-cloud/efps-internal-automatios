# EFPS Inventory Management

Owns EFPS property inventory business workflows and decisions.

## Responsibility

This module owns inventory intake, extraction, validation, inventory creation/update, duplicate handling, inventory state, and inventory-specific coordination with shared services.

The technical WhatsApp connection is not owned here. `shared/whatsapp_whapi/` supplies normalized webhook messages and the verified inventory-listener sender configuration. The current legacy listener numbers are `917975102130` and `919902024973`.

The module may use shared Google Sheets, Cloudinary, and WhatsApp/WhAPI capabilities, but those shared services do not contain inventory business rules.

## Housing_Listings

The canonical physical contract is provided by `shared/google_sheets/schema.py`: 48 columns, A:AV. The inventory module must address rows by immutable `listing_id` and must respect the shared column ownership contract.

## Status

Implementation will be added in small, verified steps. Live webhook/AWS integration must be established only after runtime verification of the deployed WhAPI connection and webhook state.
