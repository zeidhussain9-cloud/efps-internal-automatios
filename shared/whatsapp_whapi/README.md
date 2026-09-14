# WhatsApp / WhAPI Shared Service

Repository-specific shared integration layer for EFPS WhatsApp connectivity through WhAPI.

## Responsibility

This shared layer owns technical integration capabilities only:

| Component | Functionality |
|---|---|
| `connection` | Connection setup and connection state |
| `authentication` | API tokens, credentials, authentication headers, secure authorization |
| `API client` | Common authenticated WhAPI requests |
| `webhook registration` | Register EFPS webhook endpoints and required subscriptions |
| `webhook receiving` | Receive WhAPI events and pass them into internal processing |
| `webhook verification` | Verify incoming webhook requests |
| `message sending` | Reusable text, media, template, interactive and related sending primitives |
| `message receiving` | Normalize incoming WhatsApp events for business modules |
| `media handling` | Images, documents, video and audio transport |
| `contact handling` | WhatsApp contact operations exposed by WhAPI |
| `group handling` | WhatsApp group operations exposed by WhAPI |
| `configured WhatsApp numbers` | Connected EFPS numbers/accounts and their configuration |
| `webhook configuration` | Events listened for, endpoints, and routing configuration |
| `connection health/status` | Health and operational state of each configured connection |

The business module decides when and why these capabilities are used. This layer must not decide inventory workflow, lead classification, catalogue behavior, or other EFPS business rules.

## Verified legacy credential boundary

The verified `efps-platform` implementation keeps the WhAPI credential in AWS Secrets Manager under:

`efps-whapi-panel-token`

The legacy code reads the credential as `WHAPI_API_TOKEN` during local development and accepts the secret payload keys `api_token`, `token`, `value`, or `WHAPI_API_TOKEN`. fileciteturn315file0L2-L2 fileciteturn316file0L2-L2

The exact token value is **not** copied into this repository.

## WhAPI endpoint truth

The verified legacy base URL is:

`https://gate.whapi.cloud`

fileciteturn315file0L2-L2

Endpoint-specific operations must be implemented from verified WhAPI references. This repository must not invent API paths, payloads, response fields, webhook event schemas, or verification mechanisms.

## Safety gate

The legacy implementation blocks live WhAPI network traffic unless the deliberate runtime flag `EFPS_WHAPI_LIVE=1` is supplied. The guard covers fetches, token checks, quota checks, health pings and other live operations. fileciteturn223file0L2-L2

The shared implementation must preserve that safety boundary.

## Credentials policy

Never commit the token, secret payload, passwords, private keys, webhook secret values, or production connection credentials. Document secret names and variable names only.
