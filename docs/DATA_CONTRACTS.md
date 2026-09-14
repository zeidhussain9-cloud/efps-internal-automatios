# Data Contracts

This is the canonical cross-module data ownership and contract reference for EFPS Internal Automations.

## Inventory contract

The inventory module is the business owner of canonical inventory data and inventory-specific decisions.

Any future spreadsheet or external data store remains a technical capability only when explicitly established; the shared layer must not decide inventory business rules.

## Media contract

Cloudinary is the currently active shared technical capability under `shared/cloudinary/`. The inventory module decides when property images are uploaded and how resulting media references are used.

## Catalogue contract

The Meta catalogue module consumes approved inventory information for catalogue purposes. Catalogue-specific titles, descriptions, and publication decisions belong to the catalogue module, not to shared services.

## Current shared-scope rule

No other shared integration is treated as active repository structure until it is explicitly established and verified.

## Contract maturity

Exact field-level schemas, write ownership, validation requirements, and cross-project contracts must be added only when they are established from an owner-approved source or an implemented and verified capability. Do not invent contract details.
