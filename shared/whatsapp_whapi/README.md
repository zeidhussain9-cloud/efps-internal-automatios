# WhatsApp / WhAPI Shared Service

Repository-specific shared integration layer for EFPS WhatsApp connectivity through WhAPI.

## Responsibility

This shared layer owns technical integration capabilities only:

| Component | Functionality |
|---|---|
| Connection | WhAPI channel connection and connection state |
| Authentication | Bearer token and secure credential loading |
| API client | Common authenticated GET/POST/PATCH transport |
| Webhook registration | Canonical webhook settings payload construction |
| Webhook receiving | Delivery parsing and normalized message objects |
| Webhook verification | Constant-time `?t=` shared-token validation |
| Message/media primitives | Transport-level message and media data normalization |
| Configured listeners | Verified inventory-listener sender numbers exposed to owning modules |
| Connection health/status | Shared transport boundary; live health checks remain explicitly gated |

Business modules decide what a message means and what action to take. This layer must not decide inventory workflow, lead classification, catalogue behavior, or other EFPS business rules.

## Verified AWS/runtime credential map

| Shared capability | Verified AWS secret | Verified local/runtime name |
|---|---|---|
| WhAPI | `efps-whapi-panel-token` | `WHAPI_API_TOKEN` |

The legacy secret accepts the token payload keys `api_token`, `token`, `value`, or `WHAPI_API_TOKEN`. The actual token is never copied into this repository.

## Verified connection facts from `efps-platform`

- Base URL: `https://gate.whapi.cloud`
- Authentication: `Authorization: Bearer <token>`
- Live traffic gate: `EFPS_WHAPI_LIVE=1`
- Webhook shared-token variable: `EFPS_WEBHOOK_TOKEN`
- Webhook query parameter: `t`
- Inventory-listener sender numbers: `917975102130`, `919902024973`

The legacy auth documentation states one token = one WhAPI channel = one connected WhatsApp number. Therefore the two inventory-listener numbers above must not be described as two WhAPI channels without runtime verification; they are the two source numbers used by the legacy webhook's inventory routing. fileciteturn386file0L2-L2

## Legacy webhook flow reviewed

```text
WhatsApp message
      ↓
WhAPI channel
      ↓
HTTP POST to public EFPS webhook Function URL
      ↓
?t=<webhook secret> verification
      ↓
Webhook payload normalization
      ↓
┌───────────────────────────────┐
│ direct message from either    │
│ inventory-listener number     │ → inventory business module
└───────────────────────────────┘
                 OR
┌───────────────────────────────┐
│ other direct message          │ → lead business module
└───────────────────────────────┘
```

The legacy webhook acknowledged quickly and could hand the payload to a separate asynchronous Lambda because media download, sheet writes, and AI extraction could exceed WhAPI's webhook response window. fileciteturn377file0L2-L2 fileciteturn379file0L2-L2

## Webhook configuration

The verified legacy WhAPI skill uses `PATCH /settings` with:

- `webhooks[].url`
- `webhooks[].mode = "body"`
- `webhooks[].events[].type`
- `webhooks[].events[].method = "post"`

The shared package can construct this registration payload through `config.webhook_registration_payload()` / `webhook.build_registration_payload()`. It does **not** automatically mutate the live WhAPI account. The exact live webhook URL and current subscription state require runtime verification. fileciteturn384file0L2-L2

## Inventory-listener and lead separation

The previous webhook's business routing was:

1. A direct message from `917975102130` or `919902024973` was treated as inventory.
2. Inventory processing wrote property data to `Housing_Listings` and could immediately process media/AI extraction in the legacy live path.
3. A different direct message was treated as a lead and recorded conversation data before the lead representation was refreshed.
4. Group messages were not part of the live lead path; the legacy configuration had retired group inventory routing from the webhook.

Only the transport, sender configuration, and message normalization belong in `shared/whatsapp_whapi/`. Inventory and lead business behavior now belongs in their respective modules.

## Safety

Every live API request must pass `EFPS_WHAPI_LIVE=1`. Never enable that flag in code, and never commit production tokens, webhook secrets, passwords, or other credentials.
