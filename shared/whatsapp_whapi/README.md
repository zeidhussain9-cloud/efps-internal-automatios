# WhatsApp / WhAPI Shared Service

Repository-specific shared integration layer for EFPS WhatsApp connectivity through WhAPI.

## Responsibility

This shared layer owns technical integration capabilities only:

- Bearer-token credential loading from the verified AWS secret or local environment.
- Authenticated GET/POST/PATCH transport with an explicit live-traffic gate.
- Neutral channel health/settings/event-discovery primitives.
- Neutral text-message and webhook-test primitives.
- Webhook payload parsing and normalized incoming-message objects.
- Constant-time validation of the legacy `?t=` webhook secret.
- Verified inventory-listener source numbers exposed as configuration data only.

Business modules decide what a message means and what action to take. This layer must not own inventory workflow, lead classification, catalogue behavior, persistence workflow, AI extraction, or posting logic.

## Verified AWS/runtime credential map

| Shared capability | Verified AWS secret | Verified local/runtime name |
|---|---|---|
| WhAPI | `efps-whapi-panel-token` | `WHAPI_API_TOKEN` |

The legacy secret accepts the token payload keys `api_token`, `token`, `value`, or `WHAPI_API_TOKEN`. The actual token is never copied into this repository.

## Verified connection facts from the legacy repository

- Base URL: `https://gate.whapi.cloud`
- Authentication: `Authorization: Bearer <token>`
- Live traffic gate: `EFPS_WHAPI_LIVE=1`
- Webhook shared-token variable: `EFPS_WEBHOOK_TOKEN`
- Legacy webhook query parameter: `t`
- Retained inventory-listener sender numbers: `917975102130`, `919902024973`

The legacy auth model records one token/channel/connected-number relationship. The two numbers above are therefore source-number configuration, not evidence of two WhAPI channels.

## Current API boundary

The current WhAPI documentation exposes these connection/configuration endpoints used by this shared layer:

- `GET /health` — health/channel launch check.
- `GET /settings` — current channel settings.
- `GET /settings/events` — allowed webhook events; callers must discover events instead of guessing names.
- `PATCH /settings` — webhook/channel configuration; the shared package can construct the payload but does not mutate it automatically.
- `POST /settings/webhook_test` — webhook delivery test.
- `POST /messages/text` — neutral outbound text-message primitive.

The exact live channel identity, current webhook URL, subscribed events, and deployed endpoint remain runtime facts and must be verified before production traffic is enabled.

## Webhook boundary

The shared parser normalizes common text, link-preview, location, image, video, document, and audio message shapes. It does not persist, classify, deduplicate, enrich, or route business objects.

The webhook registration builder requires the caller to supply explicitly verified event definitions. It deliberately does not retain a guessed/default event list.

## Safety

Every live API request must pass `EFPS_WHAPI_LIVE=1`. The flag is never enabled automatically. Live settings mutation must be an explicit operational action after current state is recorded and verified.

Never commit production tokens, webhook secrets, passwords, private keys, or other credentials.
