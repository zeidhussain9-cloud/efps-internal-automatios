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

## Verified live state — Inventory Phase 1

The following facts were verified against the connected WhAPI account using read-only/live diagnostic requests. The diagnostics used an explicit `User-Agent: EFPS-Inventory-Phase1/1.0` after the initial request was rejected by Cloudflare browser-signature filtering without an explicit user-agent.

- `GET /health`: HTTP 200.
- Connected display identity: `Easyfind Property Solutions`.
- Connected WhatsApp ID: `919148338801`.
- Business channel: `true`.
- Channel ID: `DRAXTH-J6HEU`.
- `GET /settings`: HTTP 200.
- A webhook is currently configured in `body` mode.
- The configured webhook subscribes to `messages` with `POST`.
- The configured endpoint is the deployed AWS Lambda URL already present in the live WhAPI settings. The URL, including its authentication query token, is intentionally not recorded in Git.
- `GET /settings/events`: HTTP 200 and the `messages`/`post` event is present in the allowed-events response.
- A direct synthetic JSON POST to the configured webhook endpoint returned HTTP 200 with `{"ok": true, "queued": 1}`.
- The synthetic probe used a non-inventory sender (`919000000000`), so it could not open an Inventory Phase-1 property session.
- No WhAPI settings were changed and no customer message was sent during these acceptance checks.

These checks verify the live WhAPI account, current webhook configuration, and deployed endpoint reachability. They do not constitute a production real-inventory message acceptance test.

## Important transport note

The successful Cloudflare diagnostic required an explicit user-agent. The current diagnostic proves that `gate.whapi.cloud` accepts the request with `EFPS-Inventory-Phase1/1.0`, but the repository's canonical `WhApiClient` transport has not yet been changed solely on the basis of this diagnostic. Do not claim that the current client transport is permanently Cloudflare-compatible until that implementation decision is explicitly made and tested.

## Current API boundary

The current WhAPI documentation exposes these connection/configuration endpoints used by this shared layer:

- `GET /health` — health/channel launch check.
- `GET /settings` — current channel settings.
- `GET /settings/events` — allowed webhook events; callers must discover events instead of guessing names.
- `PATCH /settings` — webhook/channel configuration; the shared package can construct the payload but does not mutate it automatically.
- `POST /settings/webhook_test` — webhook delivery test.
- `POST /messages/text` — neutral outbound text-message primitive.

## Webhook boundary

The shared parser normalizes common text, link-preview, location, image, video, document, and audio message shapes. It also exposes a neutral `listener` value of `inventory` or `lead` for each normalized inbound message according to the two-listener configuration.

It does not persist, create, classify beyond the listener boundary, deduplicate, enrich, match, assign, or route business objects.

The webhook registration builder requires the caller to supply explicitly verified event definitions. It deliberately does not retain a guessed/default event list.

The Inventory Stage-1 adapter applies the business boundary after normalization: only the two configured inventory sender numbers qualify, `NEW` opens/closes property sessions, and non-inventory senders cannot create Inventory Phase-1 property sessions.

## Safety

Every live API request must pass `EFPS_WHAPI_LIVE=1`. The flag is never enabled automatically. Live settings mutation must be an explicit operational action after current state is recorded and verified.

Never commit production tokens, webhook secrets, passwords, private keys, or other credentials. In particular, never copy the live webhook URL when it contains the `?t=` authentication token.
