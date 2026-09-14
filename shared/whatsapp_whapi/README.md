# WhatsApp / WhAPI Shared Service

Repository-specific shared integration layer for EFPS WhatsApp connectivity through WhAPI.

## Responsibility

This shared layer owns technical integration capabilities only:

- Bearer-token credential loading from the canonical local Keychain service.
- Authenticated GET/POST/PATCH transport with an explicit live-traffic gate.
- Neutral channel health/settings/event-discovery primitives.
- Neutral text-message and webhook-test primitives.
- Webhook payload parsing and normalized incoming-message objects.
- Constant-time validation of the legacy `?t=` webhook secret.
- Two-listener source routing: exactly two dedicated sender numbers are the inventory listener; all other inbound traffic follows the lead listener path.
- Neutral listener configuration metadata for inventory, lead, groups, and promotions.

Business modules decide what a message means and what action to take. This layer must not own inventory workflow, lead creation, catalogue behavior, persistence workflow, AI extraction, matching, deduplication, or posting logic.

## Two-listener configuration

### Inventory listener

The inventory listener accepts only direct inbound messages from these exact verified source numbers:

- `917975102130`
- `919902024973`

Group messages are not inventory-listener messages. Messages sent by the account itself are not inbound listener messages.

### Lead listener

The lead listener is the default inbound path for everything that is not one of the two dedicated inventory direct-message sources. The shared layer records the routing boundary only; the owning lead module decides how the resulting message is handled.

The configuration explicitly reserves `inventory`, `groups`, and `promotions` as non-lead business paths. The shared layer does not create, update, deduplicate, or assign any business object for these paths.

## Credential resolution

| Item | Current value |
|---|---|
| Token Keychain service | `efps-whapi-panel-token` |
| Webhook Keychain service | `efps-whapi-panel-webhook` |
| Keychain account | `efps` |
| Historical token AWS source | `easyfind/whatsapp-api-credentials` |
| Historical webhook AWS source | `easyfind/whatsapp-webhook-credentials` |
| Environment token fallback | `WHAPI_API_TOKEN` |

The current repository resolves the canonical local Keychain service and does not require AWS Secrets Manager access at runtime. The actual token and webhook secret are never copied into this repository.

## Verified connection facts from the legacy repository

- Base URL: `https://gate.whapi.cloud`
- Authentication: `Authorization: Bearer <token>`
- Live traffic gate: `EFPS_WHAPI_LIVE=1`
- Webhook shared-token variable: `EFPS_WEBHOOK_TOKEN`
- Legacy webhook query parameter: `t`
- Retained inventory-listener sender numbers: `917975102130`, `919902024973`

The legacy auth model records one token/channel/connected-number relationship. The two numbers above are therefore source-number routing configuration, not evidence of two WhAPI channels.

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

The shared parser normalizes common text, link-preview, location, image, video, document, and audio message shapes. It also exposes a neutral `listener` value of `inventory` or `lead` for each normalized inbound message according to the two-listener configuration.

It does not persist, create, classify beyond the listener boundary, deduplicate, enrich, match, assign, or route business objects.

The webhook registration builder requires the caller to supply explicitly verified event definitions. It deliberately does not retain a guessed/default event list.

## Safety

Every live API request must pass `EFPS_WHAPI_LIVE=1`. The flag is never enabled automatically. Live settings mutation must be an explicit operational action after current state is recorded and verified.

Never commit production tokens, webhook secrets, passwords, private keys, or other credentials.
