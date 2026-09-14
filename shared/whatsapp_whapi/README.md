# WhatsApp / WhAPI Shared Service

Provides the reusable technical integration layer for EFPS WhatsApp connectivity through WhAPI.

## Responsibility

This shared layer owns technical integration capabilities only:

- WhAPI authentication and client setup
- HTTP/API request handling
- explicit live-traffic safety gating
- webhook/transport foundations
- reusable message/media transport primitives
- connection/status handling
- technical error handling

Business modules decide when and why WhatsApp actions occur, what a message means, which audience should be contacted, and what business workflow follows an event.

## Implementation

`client.py` provides credential loading, GET/POST transport, bearer authentication, configurable base URL, injected transport testing, and an explicit `EFPS_WHAPI_LIVE=1` gate. The gate is deliberately disabled unless explicitly enabled at runtime.

The implementation does not claim endpoint-specific message/group/webhook behavior until those endpoints are verified from the current WhAPI reference. This avoids inventing API contracts.

## Safety

The verified legacy `efps-platform` implementation blocks live WhAPI traffic unless an explicit runtime flag is supplied. fileciteturn223file0L2-L2

Tokens, secrets, passwords, private keys, and production credentials must never be committed.
