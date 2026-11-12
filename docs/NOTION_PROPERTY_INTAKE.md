# Notion Property Intake — Runtime Contract

## Scope

The Notion database **Property Intake — Raw Details & Photos** is an intake surface, not a second inventory engine. The AWS Lambda adapter at `modules/efps-inventory-mgmnt/src/notion_intake.py` fetches the submitted Notion page, then delegates extraction, normalization, Maps enrichment, and validation to the existing `pipeline.process_closed_session()` implementation.

## Processing flow

1. Notion database automation sends the trigger page ID to the SAM endpoint `/notion/intake` with header `X-EFPS-Notion-Intake-Token`. The handler accepts `page_id`, top-level `id`, `page.id`, `data.page.id`, `data.id`, or `entity.id` payload shapes, queues an asynchronous self-invocation, and returns HTTP 202 immediately.
2. The API Lambda verifies the shared webhook token and enqueues the page ID. The worker invocation fetches the page through the Notion API; async retries are enabled for transient failures.
3. A conditional record in the existing `efps-sessions` DynamoDB table claims the page idempotently. The same `listing_id` is reused for retries and edits.
4. The original Raw Property Data is written to the canonical A:AT Sheet row. Photos are downloaded only from supported Notion-hosted HTTPS file URLs and uploaded through `shared/cloudinary/media.py` to deterministic `properties/{listing_id}/photo_{n}` IDs, up to the ten-image catalogue limit.
5. The canonical Inventory pipeline processes the raw text. It preserves the exact original Maps URL, applies locality/place-name changes only from VERIFIED Maps results, and routes unverified Maps candidates to Needs Review. Mandatory subtype validation remains active.
6. The processed row is persisted to Housing_Listings A:AT. The adapter generates the v7.1 `whatsapp_post` from explicit source facts and VERIFIED location, includes only the original short Maps URL, omits long Maps URLs and flags them for review, and never infers pet policy from the inventory default. A matching Housing Listings Notion page is created or updated by Listing ID; the intake page receives Listing ID, final status, notes, processed timestamp, and the relation.
7. Validation or media errors produce `Needs Review`; transient failures are recorded and remain retryable. Repeated delivery of the same successfully processed payload is idempotent.

## Notion database properties

The intake adapter reads:
- `Intake Entry` (title)
- `Raw Property Data` (rich text)
- `Photos` (files)

It updates:
- `Intake Status` (`Processing`, `Processed`, or `Needs Review`)
- `Listing ID`
- `Processing Notes`
- `Processed At`
- `Processed Property` (relation to Housing Listings)

The Housing Listings projection uses the fetched canonical database property names and types. WhatsApp Group and WhatsApp Destination are assigned only from the BHK mapping. The v7.1 `whatsapp_post` is generated from explicit/verified facts only. The adapter never sends WhatsApp messages.

## Security and deployment

The Notion SAM resource is optional and is omitted unless `NotionSecretArn` is supplied as a deployment parameter. When enabled, it requires one AWS Secrets Manager JSON secret:

- `api_token`: Notion internal integration token with read/write access to both intake and Housing Listings databases.
- `webhook_secret`: high-entropy shared token configured as the Notion automation's `X-EFPS-Notion-Intake-Token` header.

No token or secret value belongs in Git. The Lambda reuses the existing Sheets, Maps, and Cloudinary environment configuration and the existing DynamoDB sessions table. Its IAM grant is limited to GetItem/PutItem/UpdateItem on that table. The canonical Sheet-to-Supabase sync remains unchanged; this adapter does not write directly to Supabase.

## Acceptance gates

- SAM validation/build and Python inventory tests pass.
- AWS secret exists with the two required keys.
- Notion automation sends the trigger page ID and private header token.
- One controlled test intake produces exactly one Sheet row, Cloudinary URLs, one related Housing Listings page, and a completed intake record.
- Replaying the same event does not create a duplicate row or Notion page.
- No WhatsApp send or catalogue dispatch is performed. The form editor currently exposes only the title question; use the New Intake Queue table until Raw Property Data and Photos are configured as form questions.

## Current deployment boundary

Repository code and SAM configuration are prepared separately from production cutover. The endpoint is not active until the SAM stack is deployed with `NotionSecretArn`, the Notion automation is configured, and the acceptance test passes. The webhook responds 202 after queueing; the worker has a 180-second timeout and two asynchronous retries.