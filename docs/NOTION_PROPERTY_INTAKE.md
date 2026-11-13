# Notion Property Intake — Runtime Contract

## Current verified deployment state — 2026-11-13

- CloudFormation stack: `efps-notion-property-intake` in `ap-southeast-2` — `UPDATE_COMPLETE`.
- Lambda: `efps-notion-intake` — `Active`, Python 3.12, 512 MB, 180-second timeout.
- API endpoint: `https://ko3771nvei.execute-api.ap-southeast-2.amazonaws.com/Prod/notion/intake` (`POST /notion/intake`).
- Webhook probes: invalid handshake signature and invalid event signature each returned HTTP 401; a request signed with the currently stored verification token passed signature validation and reached page-ID validation (HTTP 400). No worker was queued by these probes.
- Notion API credential: read-only intake database metadata request returned HTTP 200; read-only Housing Listings database query returned HTTP 200 (one result returned; result content was not inspected).
- The existing `efps-whapi-panel-v2` CloudFormation stack, its six Lambdas, and its API Gateway were not modified by this isolated deployment.
- **Not end-to-end operational yet.** Notion API read access is verified, but write access and the webhook subscription itself are not verified. The deployed Lambda currently resolves `GOOGLE_SERVICE_ACCOUNT_JSON` to `{}` and resolves the Cloudinary credentials and Google Maps key to `MIGRATION_PLACEHOLDER`. Those are confirmed runtime blockers for Sheet writes, photo upload, and Maps verification. No Notion-to-Sheet/Cloudinary production write has been verified. The Notion Connection webhook subscription and a controlled acceptance test are also not verified as configured.
- Inventory module test suite: 118/118 passed (87 Notion-intake tests); isolated SAM template and generated template both pass `sam validate --lint`; SAM build succeeded.

Notion is an additional intake route alongside the existing WhAPI NEW-delimited inventory session and Slack operator-assisted property/photo intake. The Notion database **Property Intake — Raw Details & Photos** is an intake surface, not a second inventory engine. The isolated Lambda adapter in `modules/efps-inventory-mgmnt/src/notion_intake.py` delegates extraction, normalization, Maps enrichment, and validation to the existing `pipeline.process_closed_session()` implementation.

## Processing flow (designed runtime path)

1. An administrator configures a Notion Developer Connection webhook subscription to POST events to the endpoint above. This is a **Connection webhook**, not a Notion database-automation `Send webhook` action.
2. During initial subscription verification, Notion sends `verification_token` and signs the exact handshake body with that token. The handler verifies `X-Notion-Signature` before storing it in the `webhook_secret` field of the dedicated Secrets Manager JSON secret. Later deliveries must include `X-Notion-Signature`, which the handler verifies as HMAC-SHA256 over the exact raw request body using that token.
3. A valid event containing the Notion page ID is queued through asynchronous self-invocation; the HTTP handler returns 202. The worker fetches the Notion page using `api_token`. Lambda asynchronous invocation is configured for up to two retries.
4. A conditional record in the existing `efps-sessions` DynamoDB table claims the page idempotently under the `notion-intake:` key prefix. The same `listing_id` is reused for retries and edits. A repeated successfully processed payload is treated as a duplicate.
5. If `Raw Property Data` is missing, the intake page is marked `Needs Review`. Otherwise, the original raw text is placed into the canonical `Housing_Listings` A:AT row. A new listing ID is allocated only when one does not already exist for that intake page.
6. Supported Notion-hosted HTTPS photos (maximum ten, 20 MB each) are downloaded and uploaded through `shared/cloudinary/media.py` to deterministic `properties/{listing_id}/photo_{n}` IDs. Unsupported file hosts, non-image content, oversize images, or upload failures create review issues.
7. The canonical Inventory pipeline processes the raw text. It preserves the original Maps URL, applies locality/place-name changes only from VERIFIED Maps results, and keeps mandatory subtype validation. Unverified Maps evidence does not overwrite source facts and routes the item to review.
8. The processed A:AT row is written to `Housing_Listings`. The adapter creates or updates the matching Housing Listings Notion page by Listing ID and writes the v7.1 `whatsapp_post` caption from explicit/verified facts. The intake page receives Listing ID, final status, notes, processed timestamp, and the related listing page.
9. The existing Sheet-to-Supabase inventory synchronization remains the separate downstream mirror path. The Notion adapter does not write directly to Supabase and does not send WhatsApp messages or dispatch a catalogue.

**Important:** Steps 3–9 describe the implemented processing path, not a successful production acceptance run. Current credential blockers prevent that end-to-end claim.

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

The canonical Housing Listings database ID in code is `bccfd4f55e294b269daa093a928f873a`. The intake database ID is `89dad7a3990849ca9dc23e5bcb3fa99f`. WhatsApp Group and WhatsApp Destination are assigned only from the BHK mapping. The adapter never sends WhatsApp messages.

## Security and deployment

The isolated template is `notion-intake-template.yaml`. It creates only the `efps-notion-intake` Lambda, its IAM role/invoke configuration, and a dedicated API Gateway. It reuses the existing `efps-sessions` table and existing secret ARNs; it does not update the shared WhAPI/CRM stack.

The dedicated AWS Secrets Manager secret `efps-notion-intake` must contain:
- `api_token`: Notion internal connection token with read/write access to both Notion databases. The Lambda retrieves it from Secrets Manager at worker runtime; it is not stored in Lambda environment variables.
- `webhook_secret`: Notion subscription verification token, populated by the initial webhook verification handshake.

The template also references the existing Google Sheets, Cloudinary, and Maps secrets. Their existence alone is not sufficient: their resolved runtime values must be valid. The currently deployed values are not valid for this intake (Sheets JSON `{}`, Cloudinary and Maps placeholders); replace them only through the authorized secret-management process, then redeploy/update the isolated stack so CloudFormation refreshes dynamic references. Never put secret values in Git or documentation.

## Acceptance gates still open

- Supply valid production Google service-account JSON, Cloudinary credentials, and Google Maps API key to the approved secret records, then update the isolated stack.
- Verify page-level Notion reads and write permissions for both target databases during acceptance; database metadata and a read-only Housing Listings query already returned HTTP 200.
- Create/verify the Notion Connection webhook subscription and capture its verification token.
- Submit one controlled test intake and confirm exactly one Sheet row, expected Cloudinary URLs, one related Housing Listings page, and a completed intake record.
- Replay the same event and confirm no duplicate row or Notion page.
- Confirm the existing Sheet-to-Supabase sync mirrors the new row.
- Confirm no WhatsApp message or catalogue dispatch was sent.
