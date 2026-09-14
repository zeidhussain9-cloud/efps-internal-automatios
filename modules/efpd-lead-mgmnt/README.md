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

## Legacy live-flow being separated

The previous `efps-platform` WhAPI webhook routed direct messages that were not from the two configured inventory-listener numbers into the lead path. The lead path recorded inbound/outbound conversation data and refreshed the lead representation. That business behavior belongs here; the shared WhAPI layer only supplies the verified webhook message and connection context.

## Status

This module is the canonical home for future lead-management implementation. No inventory workflow is duplicated here.
