# Notion Property Intake — Runtime Contract

## Follow-up acceptance status — 2026-11-13

A controlled live Housing Listings test exposed a defect after the earlier deployment evidence recorded below: for a page with no Listing ID, the Supabase `allocate_listing_id` RPC stored an ID, but `notion-inventory-state` returned `{ok:true}` instead of the ID. The Lambda therefore recorded the event as failed and did not create the inventory snapshot row. Local code now returns the ID and has a regression test; local CRM checks pass (142 Node tests/build and one browser test). This fix has not yet been published or deployed. The temporary test page (`417fedf9-b4e8-81ed-b882-df6cf2abd723`, title `EFPS TEST ONLY - DO NOT CONTACT - 20261113-101056Z`) and its failed intake event still require cleanup after deployment and a successful lifecycle test. Do not treat the create/edit/duplicate/archive/restore acceptance gate as passed until then. The production UI also remains unverified while signed out.

The deployment and data counts recorded below are observations from before this follow-up test; they do not demonstrate that the in-progress fix is live.

## Current verified deployment state — 2026-11-13

- AWS account: `294417174793`; region: `ap-southeast-2`.
- CloudFormation stack: `efps-notion-property-intake` — `UPDATE_COMPLETE`.
- Lambda: `efps-notion-intake` — Active, Python 3.12, 512 MB, 180-second timeout; SAM update completed 2026-11-13, `$LATEST`, CodeSha256 `BWKGDapY+LtrWskHtPWOLr0m8KcS0Ljp83aGkJFYvw4=`.
- API endpoint: `https://ko3771nvei.execute-api.ap-southeast-2.amazonaws.com/Prod/notion/intake` (`POST /notion/intake`).
- The deployed Notion Lambda no longer references DynamoDB: `SessionsTableArn`, DynamoDB IAM actions, and the `DynamoIntakeStore` adapter were removed. The legacy `efps-sessions` table is not used by this Notion path.
- Supabase production project: `easyfind-crm` (`qttcutwzehtskfcwxkwj`, `ap-south-1`). `public.crm_inventory_intake_events` provides page idempotency. The `notion-inventory-state` Edge Function is ACTIVE v4 with JWT verification enabled; v4 adds inventory lookup and lifecycle-safe direct Housing Listings synchronization. The deployed Lambda contains the direct mirror handler.
- Supabase idempotency acceptance: authenticated claim, listing-ID persistence, finish, and same-payload replay returned `claimed` then `duplicate`. The temporary test row was deleted.
- Notion API access: metadata/read checks for both databases returned HTTP 200. Controlled create-and-archive probes for both the Property Intake and Housing Listings databases returned HTTP 200; write/insert and archive permissions are verified.
- Google Sheet: the repository's canonical Sheet ID exactly matches the supplied workbook (`1zdOLWklkWlnVECCtcH4SJj6vm6nEVjINpTT2U2UJEKc`), tab `Housing_Listings`. Using the valid local macOS Keychain credential, a live read succeeded and the returned A:AT header matched all 46 operational column names.
- Cloudinary: authenticated API ping returned HTTP 200; a 1x1 PNG upload returned HTTP 200 and the temporary acceptance asset was deleted successfully.
- Google Maps: live address resolution using the valid local Keychain credential returned `VERIFIED` with locality evidence.
- **Raw Property Intake runtime dependencies:** the previous acceptance pass recorded the AWS Sheets secret as `{}` and Cloudinary/Maps values as placeholders. Those records were not inspected or modified in this deployment turn. This affects raw photo/enrichment intake only; the direct Housing Listings mirror and backfill succeeded with the existing Notion/Supabase path.
- The existing `EFPS CRM Property Intake` Connection is present in Notion Developer Connections. The user confirms its webhook was verified and all eight Page events remain selected. Invalid signatures return HTTP 401; signed malformed events reach page-ID validation (HTTP 400).
- AWS identity was verified as account `294417174793`. The database schema change and Edge Function v4 are deployed. SAM updated the Lambda stack to `UPDATE_COMPLETE`, and Lambda reports `LastUpdateStatus=Successful`. Existing secret ARNs were reused; no secret values were printed, copied, created, rotated, or overwritten.
- The idempotent backfill replay returned HTTP 200 with `accepted: 104`. Supabase confirms 104 processed intake events and 104 active `housing_notion` rows (87 Available, 17 Rented) in `crm_inventory_snapshot`; no `housing_sheet` or test-like rows remain.
- Inventory module tests: 129/129 Inventory Contract Python tests and 88/88 inventory-module tests passed. CRM `npm test`: 139/139 plus production build passed; browser regression: 1/1 passed. Repository audit, projection regression, Python compilation, and SAM lint passed. The reserved Notion fields are now omitted from the source projection.

## Data ownership and reconciliation

Notion Housing Listings is the canonical operator editing surface. Supabase's existing `public.crm_inventory_snapshot` remains the durable inventory projection read by the CRM dashboard. The Housing_Listings Sheet remains only for legacy Slack/raw-intake compatibility writes. The five-minute reconciliation cron was removed. The dashboard queries active `housing_notion` rows only, and its existing Supabase snapshot remains the projection. No Notion inventory processing state or duplicate guard uses DynamoDB.

- **Notion source page:** raw property text and uploaded photos remain in `Property Intake — Raw Details & Photos`.
- **Idempotency and processing state:** `public.crm_inventory_intake_events` in Supabase. Its primary key is the Notion source page ID; it stores payload hash, processing state, Listing ID, related Notion listing page ID, notes, and timestamps. RLS is enabled; table and RPC access are restricted to `service_role`, used only by the Supabase Edge Function.
- **Canonical inventory editor:** the existing Housing Listings Notion database (`bccfd4f55e294b269daa093a928f873a`), using immutable `listing_id` as record identity.
- **Supabase CRM inventory projection:** the existing `public.crm_inventory_snapshot`, keyed by `listing_id`. Housing Listings page events upsert or soft-delete the existing row directly. This is not a second table or competing projection.
- **Legacy Sheet compatibility:** existing Slack/raw-intake flows still write the `Housing_Listings` tab and A:AT processing fields. The dashboard does not read Sheet-owned inventory; the reconciliation cron is disabled. Reserved AU/AV remain blank.
- **Idempotency:** `public.crm_inventory_intake_events` stores Notion page hashes, state, and Listing ID; its restricted RPCs are called only by the authenticated Edge Function.

## Processing flows

### Housing Listings direct mirror

1. An operator creates or edits a property in the canonical Housing Listings database.
2. The Notion Connection sends a Page event to the endpoint. Keep all eight selected: `page.content_updated`, `page.created`, `page.deleted`, `page.locked`, `page.moved`, `page.properties_updated`, `page.undeleted`, `page.unlocked`.
3. The Lambda validates `X-Notion-Signature`, extracts the event page ID, queues an async worker, and returns HTTP 202.
4. The worker fetches the latest page, claims it in `crm_inventory_intake_events`, and converts its properties to the shared 48-field inventory contract plus Notion presentation fields.
5. If `listing_id` is empty, the restricted Supabase RPC allocates and stores one; the worker writes it back to the same Notion page.
6. The Edge Function upserts the existing `crm_inventory_snapshot` row with `source_kind='housing_notion'`. Deletion soft-deletes the projection; restore clears the tombstone. Same-payload replays are suppressed.
7. The dashboard reads active `housing_notion` rows from the same snapshot table. Archived pages soft-delete the row; restored pages clear the tombstone; replay repairs a missing projection idempotently.

### Raw details and photos intake

The Property Intake database remains the raw intake surface. Its existing worker reads raw text/photos, performs deterministic extraction and enrichment, writes a compatibility Sheet row, and creates/updates a Housing Listings page. That page then flows through the direct mirror path above. This raw intake path still needs the existing Sheets, Cloudinary, and Maps secret values to be valid; no new secrets are required.

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

1. Render deployment `dep-dbrbc8gjo6nc73etsmr0` is LIVE, with production `/health` and `/` returning HTTP 200. A signed-in inventory page check was not performed. The current production UI reads only active `housing_notion` rows; its data source contains 104 active rows.
2. The migration release includes a replay-recovery test. No disposable test listings were left in Notion or Supabase.
3. If raw Property Intake with photos is required, separately verify the existing Sheet/Cloudinary/Maps runtime credentials and pipeline. Do not create, rotate, or overwrite secrets without an explicit credential-maintenance task. Confirm no WhatsApp message or catalogue dispatch is sent.

The temporary Notion write-permission probe pages were archived. The temporary Supabase idempotency test row was deleted. The 104 production inventory rows in this rollout were created by the documented idempotent backfill.

## Legacy boundary

The old WhAPI `NEW`-delimited inventory listener and its DynamoDB session state are legacy code retained temporarily at the user's direction. It is not the new Notion processing path and is not to be removed until the final cleanup phase is explicitly started.
