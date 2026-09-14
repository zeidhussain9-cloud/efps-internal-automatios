# EFPS WhAPI / WhatsApp Skill

Use this skill whenever an agent changes `shared/whatsapp_whapi/` or integrates WhatsApp/WhAPI into a module.

## Mandatory truth rules

1. Read `shared/whatsapp_whapi/README.md` and the shared implementation before changing it.
2. Treat `shared/whatsapp_whapi/config.py` as the local source for verified integration configuration.
3. Never invent WhAPI endpoints, payload fields, webhook event names, channel IDs, connected numbers, or live URLs.
4. Live traffic requires deliberate `EFPS_WHAPI_LIVE=1`.
5. Never store the WhAPI token or webhook secret in Git.

## Verified credential boundary

- AWS secret: `efps-whapi-panel-token`
- Local/runtime token variable: `WHAPI_API_TOKEN`
- Base URL: `https://gate.whapi.cloud`
- Authentication: `Authorization: Bearer <token>`
- Webhook token variable: `EFPS_WEBHOOK_TOKEN`
- Webhook token query parameter: `t`

The legacy secret accepts `api_token`, `token`, `value`, or `WHAPI_API_TOKEN` payload keys.

## Verified inventory listener configuration

The legacy deployment configured these two sender numbers as inventory listeners:

- `917975102130`
- `919902024973`

They are source-number routing facts. Do not call them two WhAPI channels without runtime verification. The legacy WhAPI documentation states one token = one channel = one connected WhatsApp number.

## Webhook flow

```text
WhatsApp
  -> WhAPI channel
  -> public EFPS webhook Function URL
  -> ?t=... verification
  -> payload normalization
  -> owning module receives normalized message
```

The previous business routing sent messages from the two inventory-listener numbers to inventory handling and other direct messages to lead handling. That classification/action belongs to modules; this shared layer exposes the listener configuration and normalized message.

The legacy webhook could acknowledge immediately and asynchronously process slow media/sheet/AI work. Preserve that architecture when a module requires it.

## Webhook registration

The verified legacy registration shape is `PATCH /settings` with:

- `webhooks[].url`
- `webhooks[].mode = "body"`
- `webhooks[].events[].type`
- `webhooks[].events[].method = "post"`

`config.webhook_registration_payload()` constructs this payload. Do not execute a live settings mutation unless the user explicitly authorizes the live operation and the current WhAPI API/reference has been verified.

## Required verification after changes

Check:

- token loading works without logging secrets;
- live gate blocks network access when unset;
- webhook token verification rejects missing/wrong tokens;
- webhook payload normalization handles text, media, link previews, and location payloads without inventing fields;
- the two inventory listener numbers remain unchanged unless explicitly changed by the owner;
- business modules, not shared WhAPI code, own inventory/lead decisions.
