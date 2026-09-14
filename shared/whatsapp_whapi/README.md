# WhatsApp / WhAPI Shared Service

Provides the reusable technical integration layer for EFPS WhatsApp connectivity through WhAPI.

## Responsibility

This shared layer owns technical integration capabilities only:

- WhAPI authentication and client setup
- HTTP/API request handling
- WhatsApp connection and health/status operations
- webhook registration, verification, and inbound event handling
- message send/receive primitives
- media send/receive primitives
- contact, group, channel, and community primitives when implemented
- configured WhatsApp connection metadata
- technical error handling and transport concerns

Business modules decide when and why WhatsApp actions occur, what a message means, which audience should be contacted, and what business workflow follows an event.

## Safety

Live WhAPI traffic must not happen implicitly. The implementation must use an explicit runtime gate for live network access, following the verified anti-hallucination/approval pattern from `efps-platform`.

Tokens, secrets, passwords, private keys, and production credentials must never be committed.

## Implementation state

The shared boundary is restored now. Concrete capabilities should be implemented from verified WhAPI behavior and references rather than guessed endpoints or payloads.
