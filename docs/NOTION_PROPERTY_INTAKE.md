# Notion Property Intake — Runtime Contract

## Scope

The Notion database **Property Intake — Raw Details & Photos** is an intake surface, not a second inventory engine. The AWS Lambda adapter at `modules/efps-inventory-mgmnt/src/notion_intake.py` fetches the submitted Notion page, then delegates extraction, normalization, Maps enrichment, and validation to the existing `pipeline.process_closed_session()` implementation.

## Processing flow

1. Notion database automation sends a POST containing `page_id` to the SAM endpoint `/notion/intake` with header `X-EFPS-Notion-Intake-Token`.
2. Lambda verifies the shared webhook token and fetches the page through the Notion API.
3. A conditional record in the existing `efps-sessions` DynamoDB table claims the page idempotently. The same `listing_id` is reused for retries and edits.
4. The original Raw Property Data is written to the canonical A:AT Sheet row. Photos are downloaded only from supported Notion-hosted HTTPS file URLs and uploaded through `shared/cloudinary/media.py` to deterministic `properties/{listing_id}/photo_{n}` IDs, up to the ten-image catalogue limit.
5. The canonical Inventory pipeline processes the raw text. It preserves the existing Maps URL rule and current validation contract, including mandatory subtype validation.
6. The processed row is persisted to Housing_Listings A:AT. A matching Housing Listings Notion page is created or updated by Listing ID, then the intake page receives Listing ID, final status, notes, processed timestamp, and the relation to that page.
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

The Housing Listings projection uses the fetched canonical database property names and types. WhatsApp Group and WhatsApp Destination are assigned only from the verified BHK mapping. The adapter does not send WhatsApp messages and does not infer a caption.

## Security and deployment

The SAM stack requires one AWS Secrets Manager JSON secret supplied as `NotionSecretArn`:

- `api_token`: Notion internal integration token with read/write access to both intake and Housing Listings databases.
- `webhook_secret`: high-entropy shared token configured as the Notion automation's `X-EFPS-Notion-Intake-Token` header.

No token or secret value belongs in Git. The Lambda reuses the existing Sheets, Maps, and Cloudinary environment configuration and the existing DynamoDB sessions table. Its IAM grant is limited to GetItem/PutItem/UpdateItem on that table.

## Acceptance gates

- SAM validation/build and Python inventory tests pass.
- AWS secret exists with the two required keys.
- Notion automation sends only the page id and private header token.
- One controlled test intake produces exactly one Sheet row, Cloudinary URLs, one related Housing Listings page, and a completed intake record.
- Replaying the same event does not create a duplicate row or Notion page.
- No WhatsApp send or catalogue dispatch is performed.

## Current deployment boundary

Repository code and SAM configuration are prepared separately from production cutover. The endpoint is not active until the SAM stack is deployed with `NotionSecretArn`, the Notion automation is configured, and the acceptance test passes.