# Notion Property Intake — Runtime Contract

## Current verified acceptance state — 2026-11-14

- The live Submit New Property form schema contains both Raw Property Data and Photos questions.
- Two existing submissions have Photos but blank Raw Property Data; both remain Needs Review. The recorded worker outcome explicitly says Raw Property Data is required. No source content was fabricated or altered.
- 12 Notion webhook event rows observed: 5 processed, 4 ignored non-intake changes, 1 rejected unauthenticated probe, 2 needs-review outcomes. Complete delivery coverage is not certified.
- AWS efps-notion-intake is Active with successful code update; Maps API-unavailable fallback deployed. Supabase notion-inventory-state ACTIVE v12.
- Supabase inventory projection has 106 active Notion-owned rows; business_status Pending on all 106.
- No tables deleted. Notion event history remains in crm_inventory_intake_events; WhatsApp event history remains in crm_webhook_events.
- Full end-to-end acceptance across raw text extraction, Maps, Cloudinary, Sheets, Housing Listings and Supabase remains pending a complete real operator submission.

# Notion Property Intake — Runtime Contract

## Historical initial event-ledger deployment — 2026-11-14 08:14 UTC (superseded by v12)

Task 3 is deployed. The additive migration extends the existing `public.crm_inventory_intake_events` ledger with namespaced Notion webhook event rows and restricted RPCs. It does not create a second event table and does not change the WhatsApp `public.crm_webhook_events` table or processing path.

- Supabase migration `crm_notion_webhook_event_history` is applied to project `qttcutwzehtskfcwxkwj`.
- Supabase `notion-inventory-state` is ACTIVE v10, JWT verification enabled.
- AWS `efps-notion-intake` is Active; stack `efps-notion-property-intake` is `UPDATE_COMPLETE`. The Lambda uses the existing Notion, Sheets, Cloudinary and Maps secret ARNs; no values were displayed or rotated.
- The existing intake ledger remains service-role-only with RLS enabled. Notion event rows use `source_page_id` prefixed with `notion-webhook:`; page-level intake idempotency rows remain keyed by the actual Notion page ID.
- Event records retain stable event identity, event type/page, sanitized payload, raw-body SHA-256, delivery attempts, lifecycle history, worker attempts/errors/outcome, AWS request ID and Listing ID/page correlation. Validation outcomes are retained separately while the existing processing-status constraint is preserved.
- The existing Notion form view `Submit New Property` exposes `Raw Property Data` and `Photos`. Both questions were confirmed by fetching the live view after deployment. The data-source description now directs operators to this form.
- Production end-to-end acceptance is pending the first user-submitted property. No synthetic production property has been created.

## Historical acceptance plan — awaiting first operator submission (superseded)

The Housing Listings mirror/reconciliation baseline remains as recorded below. Task 3 is deployed, but a real property submission is required to verify the complete raw intake chain. Once the operator confirms the submission, verify: webhook delivery/signature → durable event receipt → Lambda queue/worker → extraction/validation → Google Sheets A:AT row → Cloudinary uploads → Housing Listings page and relation → Supabase `crm_inventory_snapshot` projection and `crm_inventory_intake_events` completion. Any `Needs Review` or `Failed` state must be explained from recorded evidence; do not mark the flow accepted solely because the webhook returned HTTP 202.

## Historical acceptance checkpoint — 2026-11-13

## Historical acceptance checkpoint — 2026-11-13

The active Housing Listings mirror is reconciled and operational. The previous restore-delivery gap is covered by a scheduled reconciliation fallback; the actual Notion `page.undeleted` webhook has not yet been independently observed, but a soft-deleted projection for an active Notion page was restored successfully by the scheduled reconciler.

- 104 active Notion pages; 104 active Supabase `housing_notion` snapshots; 0 missing, orphaned, duplicate or semantically mismatched records.
- 104/104 intake event rows processed, with 104/104 Listing IDs populated and matching their snapshot rows.
- `source_group` and `inventory_locked` are blank across all 104 pages. 43 populated `inventory_locked` values were corrected to blank.
- A 15-minute scheduled reconciler queues only changed/restored pages and soft-deletes rows missing from the full Notion result. Empty results fail closed. The live run checked 104 pages, queued 0, skipped 104 unchanged, reconciled 104 event Listing IDs and soft-deleted 0 rows.
- Recovery test: rented listing `EF-2609-09B5` was soft-deleted in Supabase through the worker, then automatically reactivated by scheduled reconciliation. `deleted_at` returned to null.

## Historical verified deployment state — 2026-11-13

- AWS account `294417174793`; region `ap-southeast-2`; CloudFormation stack `efps-notion-property-intake` is `UPDATE_COMPLETE`.
- Lambda `efps-notion-intake`: Active, Python 3.12, 512 MB, 180-second timeout; `$LATEST` updated `2026-11-13T15:18:43Z`; CodeSha256 `zZxd6tQPK8D1GriTmqa6rM0KS3An1zHKDsCx/MCs9aU=`.
- API endpoint: `https://ko3771nvei.execute-api.ap-southeast-2.amazonaws.com/Prod/notion/intake` (`POST /notion/intake`).
- Supabase project `qttcutwzehtskfcwxkwj` (`ap-south-1`); `notion-inventory-state` ACTIVE v9 with JWT verification enabled.
- EventBridge runs the reconciliation every 15 minutes. Async Lambda processing retries twice over a maximum event age of one hour; exhausted failures go to the dedicated SQS queue with 14-day retention. CloudWatch log retention is 30 days.
- Lambda logs now include page ID, event type, Notion webhook event ID, AWS request ID, result, and duration without logging credentials or full payloads. Empty Listing ID allocation is retried up to three times.
- The existing `EFPS CRM Property Intake` Notion Connection and all eight Page event selections remain user-confirmed; settings were not changed. Invalid signatures previously returned HTTP 401.
- Existing AWS secret ARNs were reused. No secret values were printed, copied, created, rotated, or overwritten.
- The 104-page Notion view and Supabase projection were compared field-by-field after normalizing Notion rich-text/Markdown representation: 0 semantic field mismatches. Inventory counts remain 87 Available / 17 Rented Out.
- `/health` returned HTTP 200. The CRM dashboard remains on the existing Supabase inventory projection; no CRM UI code was changed in this repair.

## Data ownership and reconciliation

Notion Housing Listings is the canonical operator editing surface. Supabase's existing `public.crm_inventory_snapshot` remains the durable inventory projection read by the CRM dashboard. The Housing_Listings Sheet remains only for legacy Slack/raw-intake compatibility writes. The five-minute reconciliation cron was removed. The dashboard queries active `housing_notion` rows only, and its existing Supabase snapshot remains the projection. No Notion inventory processing state or duplicate guard uses DynamoDB.

- **Notion source page:** raw property text and uploaded photos remain in `Property Intake — Raw Details & Photos`.
- **Idempotency and processing state:** `public.crm_inventory_intake_events` in Supabase. Its primary key is the Notion source page ID; it stores payload hash, processing state, Listing ID, related Notion listing page ID, notes, and timestamps. RLS is enabled; table and RPC access are restricted to `service_role`, used only by the Supabase Edge Function.
- **Canonical inventory editor:** the existing Housing Listings Notion database (`bccfd4f55e294b269daa093a928f873a`), using immutable `listing_id` as record identity.
- **Supabase CRM inventory projection:** the existing `public.crm_inventory_snapshot`, keyed by `listing_id`. Housing Listings page events upsert or soft-delete the existing row directly. This is not a second table or competing projection.
- **Legacy Sheet compatibility:** existing Slack/raw-intake flows still write the `Housing_Listings` tab and A:AT processing fields. The dashboard does not read Sheet-owned inventory; the reconciliation cron is disabled. Reserved AU/AV remain blank.
- **Idempotency:** `public.crm_inventory_intake_events` stores Notion page hashes, state, and Listing ID; restricted RPCs are called only by the authenticated Edge Function. `crm_reconcile_notion_inventory_event_listing_ids` repairs the Listing ID mapping in bulk during scheduled reconciliation.

## Processing flows

### Housing Listings direct mirror

1. An operator creates or edits a property in the canonical Housing Listings database.
2. The Notion Connection sends a Page event to the endpoint. Keep all eight selected: `page.content_updated`, `page.created`, `page.deleted`, `page.locked`, `page.moved`, `page.properties_updated`, `page.undeleted`, `page.unlocked`.
3. The Lambda validates `X-Notion-Signature`, extracts the event page ID, queues an async worker, and returns HTTP 202.
4. The worker fetches the latest page, claims it in `crm_inventory_intake_events`, and converts its properties to the shared 48-field inventory contract plus Notion presentation fields.
5. If `listing_id` is empty, the restricted Supabase RPC allocates and stores one; the worker writes it back to the same Notion page.
6. The Edge Function upserts the existing `crm_inventory_snapshot` row with `source_kind='housing_notion'`. Deletion soft-deletes the projection; restore clears the tombstone. Same-payload replays are suppressed.
7. The dashboard reads active `housing_notion` rows from the same snapshot table. Page events soft-delete or restore rows; the 15-minute scheduled reconciler is the recovery backstop for missed creates, edits, deletes and restores. It queues only changed/restored pages, repairs event Listing IDs, and refuses to mass-delete when Notion returns zero pages.

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

## Remaining separate scope

1. Actual Notion `page.undeleted` webhook delivery remains unobserved. The 15-minute scheduled reconciliation now recovers an active Notion page whose Supabase projection is soft-deleted; the live fallback recovery test passed. Keep the eight user-confirmed Page event selections unchanged.
2. If raw Property Intake with photos is required, separately validate the existing Sheet/Cloudinary/Maps runtime credentials and pipeline. Do not create, rotate, or overwrite secrets without a separately authorized credential operation. No WhatsApp message or catalogue dispatch was sent during this repair.

The test page was permanently deleted from Notion Trash after approval. Its exact Supabase test snapshot and intake event were removed. The verified production inventory remains at 104 active rows.

## Legacy boundary

The old WhAPI `NEW`-delimited inventory listener and its DynamoDB session state are legacy code retained temporarily at the user's direction. It is not the new Notion processing path and is not to be removed until the final cleanup phase is explicitly started.


## Latest verified checkpoint — 2026-11-14

- No table has been deleted. Notion event history remains in crm_inventory_intake_events; WhatsApp event history remains in crm_webhook_events.
- Live Notion event rows: 8 (5 processed, 2 ignored/failed outcomes, 1 needs review). This proves logging for those records only; complete delivery capture is not certified.
- Two operator-requested Housing Listings updates were verified back in Notion and Supabase.
- Live Notion-owned projection: 106 active rows. Older 104-row figures above are historical checkpoints only.
- crm_inventory_snapshot.business_status is a first-class reporting field backfilled from source_record.status. All 106 active Notion rows currently report Pending.
- Raw Property Intake with photos has not passed a fresh real-property end-to-end acceptance run. Awaiting operator submission and verification of Sheets, Cloudinary and Maps runtime credentials.
- Maps API-unavailable fallback is implemented locally but not deployed: preserve only the original supported short URL, label it unverified, and do not infer place/locality/pincode.
- At that earlier checkpoint, UI/Edge Function/Maps code changes were local; they have since been deployed as recorded at the top of this document.
