# EFPS Lead Management

Owns EFPS lead/enquiry business workflows and decisions.

## Boundary

This module is intentionally separate from `efps-inventory-mgmnt`.

- `efps-inventory-mgmnt` owns property inventory workflows.
- `efpd-lead-mgmnt` owns lead/enquiry workflows.
- `shared/whatsapp_whapi/` owns WhatsApp/WhAPI transport, webhook receiving, connection configuration, and normalized inbound message delivery.
- `shared/google_sheets/` owns reusable Google Sheets access and the canonical `Housing_Listings` contract.
- `shared/cloudinary/` owns reusable media storage/upload.

The shared layers must not classify, score, assign, or otherwise decide lead business outcomes.

## Legacy webhook flow being separated

The reviewed `efps-platform` webhook routed a direct message from either configured inventory-listener number (`917975102130`, `919902024973`) to inventory handling. Other direct messages entered the lead path. The lead path recorded the conversation by normalized phone number, retained inbound/outbound direction and message identity, and refreshed the lead representation. fileciteturn377file0L2-L2

The legacy lead worker also consumed the `efps-leads` DynamoDB stream: meaningful lead changes caused the corresponding lead card to be redrawn, while a scheduled job generated the daily dashboard. fileciteturn425file0L2-L2

## New repository rule

Only the transport and webhook facts move into `shared/whatsapp_whapi/`. Lead storage, stages, actions, assignment, card behavior, follow-up logic, and all other lead business rules belong here.

## Status

Canonical home for future lead-management implementation. Inventory workflow is not duplicated here.
