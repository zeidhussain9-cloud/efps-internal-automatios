# Notion Property Intake — Runtime Contract

## Current verified deployment state — 2026-11-13

- AWS account: `294417174793`; region: `ap-southeast-2`.
- CloudFormation stack: `efps-notion-property-intake` — `UPDATE_COMPLETE`.
- Lambda: `efps-notion-intake` — Active, Python 3.12, 512 MB, 180-second timeout.
- API endpoint: `https://ko3771nvei.execute-api.ap-southeast-2.amazonaws.com/Prod/notion/intake` (`POST /notion/intake`).
- The deployed Notion Lambda no longer references DynamoDB: `SessionsTableArn`, DynamoDB IAM actions, and the `DynamoIntakeStore` adapter were removed. The legacy `efps-sessions` table is not used by this Notion path.
- Supabase production project: `easyfind-crm` (`qttcutwzehtskfcwxkwj`, `ap-south-1`). Migration `notion_inventory_intake_supabase_idempotency` created `public.crm_inventory_intake_events` and service-role-only claim/update RPCs. Edge Function `notion-inventory-state` is Active with JWT verification enabled.
- Supabase idempotency acceptance: authenticated claim, listing-ID persistence, finish, and same-payload replay returned `claimed` then `duplicate`. The temporary test row was deleted.
- Notion API access: metadata/read checks for both databases returned HTTP 200. Controlled create-and-archive probes for both the Property Intake and Housing Listings databases returned HTTP 200; write/insert and archive permissions are verified.
- Google Sheet: the repository's canonical Sheet ID exactly matches the supplied workbook (`1zdOLWklkWlnVECCtcH4SJj6vm6nEVjINpTT2U2UJEKc`), tab `Housing_Listings`. Using the valid local macOS Keychain credential, a live read succeeded and the returned A:AT header matched all 46 operational column names.
- Cloudinary: authenticated API ping returned HTTP 200; a 1x1 PNG upload returned HTTP 200 and the temporary acceptance asset was deleted successfully.
- Google Maps: live address resolution using the valid local Keychain credential returned `VERIFIED` with locality evidence.
- **AWS runtime credentials are still blocked:** the AWS Secrets Manager record `efps-whapi-panel-sheet` currently contains `{}`; `efps-whapi-panel-cloudinary` contains placeholder values; `efps-whapi-panel-maps` contains `MIGRATION_PLACEHOLDER`. Valid credentials do exist in the Mac Keychain and passed the checks above, but the AWS secret-write action was not completed. The Lambda now reads these Secrets Manager records at runtime, so updating the secret values will take effect without another deployment.
- **Notion Connection webhook subscription is not yet verified.** Signature validation is implemented. Invalid signatures return HTTP 401; validly signed malformed page events reach page-ID validation (HTTP 400). No end-to-end intake was run because the AWS runtime secrets are still placeholders and no subscription delivery has been observed.
- Inventory module tests: 118/118 passed. Isolated SAM template validation/build passed. Supabase Edge Function idempotency acceptance passed.

## Data ownership and reconciliation

Notion is an intake surface, not a second inventory database. The authoritative inventory workbook remains Google Sheets `Housing_Listings`; Supabase is the durable processing/idempotency store and downstream CRM inventory projection. No Notion inventory processing state or duplicate guard uses DynamoDB.

- **Notion source page:** raw property text and uploaded photos remain in `Property Intake — Raw Details & Photos`.
- **Idempotency and processing state:** `public.crm_inventory_intake_events` in Supabase. Its primary key is the Notion source page ID; it stores payload hash, processing state, Listing ID, related Notion listing page ID, notes, and timestamps. RLS is enabled; table and RPC access are restricted to `service_role`, used only by the Supabase Edge Function.
- **Canonical inventory record:** the existing `Housing_Listings` Google Sheet tab, columns A:AT. Listing ID remains the immutable record identity. Reserved AU/AV columns remain untouched.
- **Supabase CRM inventory projection:** the existing five-minute Sheet-to-Supabase sync updates `public.crm_inventory_snapshot`, keyed by `listing_id`. The Notion adapter does not independently create a competing inventory projection.
- **Notion listing view:** the existing Housing Listings Notion database receives the matching Listing ID, property fields, photo URLs, and the intake page relation/status.

## Processing flow

1. An operator creates a page in the Notion Property Intake database and enters `Raw Property Data`; photos may be attached in `Photos`.
2. The Notion Developer Connection sends `page.created` or `page.properties_updated` to the endpoint above.
3. The Lambda verifies `X-Notion-Signature` against the stored webhook verification token, extracts the page ID, queues an asynchronous worker, and returns HTTP 202.
4. The worker fetches the page from Notion and computes a stable hash of raw property text and photo metadata.
5. The worker calls the Supabase `notion-inventory-state` Edge Function. A database RPC atomically claims the page ID. Same-hash processed replays return `duplicate`; recent processing claims return `in_progress`; failed/Needs Review/stale work can be reclaimed. The Listing ID is retained across retries.
6. If required raw text is missing, the intake page is marked `Needs Review`. Otherwise, the canonical Inventory pipeline allocates/reuses a Listing ID, writes the initial raw record, and performs extraction, normalization, validation, and Maps enrichment.
7. Supported Notion-hosted HTTPS photos (maximum ten, 20 MB each) are downloaded and uploaded through the shared Cloudinary helper to deterministic `properties/{listing_id}/photo_{n}` IDs. Unsupported hosts, non-image content, oversize images, or upload failures create review issues.
8. The processed A:AT record is written to `Housing_Listings`. The adapter creates/updates the Housing Listings Notion page by Listing ID and writes the v7.1 `whatsapp_post` from explicit/verified facts. The intake page receives Listing ID, final status, notes, processed timestamp, and the related listing page.
9. The existing five-minute Sheet-to-Supabase synchronization mirrors the Sheet row into `crm_inventory_snapshot` and records sync history.
10. Re-delivery of the same processed page/payload is stopped by Supabase idempotency before any second Sheet write. A materially changed page can be reprocessed against the same Listing ID.

The intake adapter does not send WhatsApp messages or dispatch a catalogue.

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

The intake database ID is `89dad7a3990849ca9dc23e5bcb3fa99f`; Housing Listings database ID is `bccfd4f55e294b269daa093a928f873a`.

## Secrets and runtime configuration

The isolated Lambda receives secret ARNs, not credential values. It retrieves credentials from Secrets Manager at runtime:

- `efps-notion-intake`: JSON with `api_token` and `webhook_secret`.
- `efps-whapi-panel-sheet`: complete Google service-account JSON object with `private_key`.
- `efps-whapi-panel-cloudinary`: JSON with `cloud_name`, `api_key`, and `api_secret`.
- `efps-whapi-panel-maps`: Google Maps API key as a plain SecretString (a JSON object containing `api_key` is also accepted).

The Supabase URL and public anon JWT are non-secret Lambda configuration. The Edge Function uses Supabase's server-side service-role key internally; it is never sent to Lambda. The Edge Function additionally checks a SHA-256 digest of the Notion API token supplied by the Lambda. Rotating that Notion API token requires updating the expected digest and redeploying the Edge Function.

## Remaining acceptance gates

1. Update the three AWS runtime secret records from the already-verified Mac Keychain credentials. Exact secret names and formats are listed above. The current AWS values are empty/placeholders; no credential values need to be pasted into chat.
2. Create the Notion **Connection webhook** subscription (not a database automation webhook action) for `page.created` and `page.properties_updated`, pointing to the endpoint above. Notion's verification handshake will automatically populate `webhook_secret` in `efps-notion-intake`.
3. After those two actions, run one controlled test page with a photo and verify one Sheet row, Cloudinary URLs, Notion listing relation/status, Supabase idempotency record, same-payload replay suppression, and the subsequent Sheet-to-Supabase sync.
4. Confirm no WhatsApp message or catalogue dispatch was sent.

The temporary Notion write-permission probe pages were archived. The temporary Supabase idempotency test row was deleted. No production inventory row was created by these probes.

## Legacy boundary

The old WhAPI `NEW`-delimited inventory listener and its DynamoDB session state are legacy code retained temporarily at the user's direction. It is not the new Notion processing path and is not to be removed until the final cleanup phase is explicitly started.
