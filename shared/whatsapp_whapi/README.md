# WhatsApp / WhAPI Shared Service

Provides the reusable technical integration layer for EFPS WhatsApp connectivity through WhAPI.

## Intended responsibilities

This shared layer will own the technical capabilities required to connect and communicate with configured WhatsApp numbers through WhAPI, including:

- connection and authentication handling
- API client capabilities
- webhook registration and receiving
- webhook verification
- message sending and receiving
- media handling
- contact handling
- group handling
- configured WhatsApp number and connection information
- webhook configuration and event handling
- connection health and status

The shared layer may maintain technical knowledge of which WhatsApp number uses which WhAPI connection, which webhooks are active, which events are being received, and connection health/status.

## Boundary

This folder must not contain EFPS business decisions. It provides capabilities only. Business modules decide when and why WhatsApp actions are performed.

For example, inventory intake rules belong to `modules/efps-inventory-mgmnt/`, not here.

## Security

WhAPI tokens, secrets, passwords, private keys, and production credentials must never be committed to the repository.

## Skeleton state

Only the shared boundary and responsibilities are defined now. Implementation subfolders should be introduced when an actual capability is built, rather than creating speculative structure.