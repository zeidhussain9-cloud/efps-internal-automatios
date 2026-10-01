# EasyFind CRM — Canonical Data Model

**Canonical repository:** `zeidhussain9-cloud/efps-internal-automatios`  
**Branch:** `crm-ui-dashboard`  
**Status (2026-10-01):** Production CRM UI is live on `crm-ui-dashboard` / Render `easyfind-crm-d01-d05`. Current production source is `+919148338801`; historical and live data are reconciled in Supabase.

## Current operational baseline — 2026-10-01

- Production source: `+919148338801`
- Source-linked CRM leads: 186
- Contact classifications: 289
- Pending classifications: 2
- Promoted classifications: 186
- Current CRM messages: 6,621
- Webhook events: 73 (73 processed, 0 received, 0 failed)
- Historical SQLite message archive: 5,286; this remains historical evidence and is not the current live message count.
- The Contact Classification UI is operator-gated and uses explicit Update actions.
- Qualified Lead is the only path into Lead CRM.

## 1. Lead data source

The lead source for this CRM is the **local extracted dataset described in `docs/audits/LEADS_EXTRACTION_SOURCE_OF_TRUTH_AUDIT.md`** and the local SQLite database produced by that extraction.

The Leads Tracker Google Sheet, Slack lead workflow and DynamoDB lead workflow are outside the current CRM lead data path. WhAPI is now the live ingress for `+919148338801`, with `crm_webhook_events` as the durable first-write boundary.

## 2. Local SQLite source model

### `leads`

Canonical source fields identified by the audit:

`phone_number`, `customer_name`, `lead_status`, `lead_source`, `priority`, `current_requirement`, `bhk_requirement`, `preferred_location`, `budget_min`, `budget_max`, `furnishing_preference`, `occupancy_type`, `pet_preference`, `parking_required`, `move_in_date`, `matched_properties`, `last_interaction_date`, `next_followup_date`, `followup_count`, `tags`, `notes`, `created_at`, `updated_at`, `extracted_from_phone`, `classification`

Primary lead identity: normalized customer `phone_number`.

### `conversations`

Canonical source fields:

`message_id`, `phone_number`, `direction`, `message_body`, `message_type`, `media_urls`, `media_filenames`, `sender_name`, `timestamp`, `replied_to_id`, `is_processed`, `extracted_intent`, `extracted_entities`, `sentiment`, `requires_followup`, `created_at`, `processed_at`

The source audit records that the existing conversation ID is an SQLite auto-increment value. During CRM migration, a stable source-message identity must be created/derived before incremental imports are enabled.

### `lead_lifecycle_events`

Canonical source fields:

`event_id`, `phone_number`, `event_type`, `event_description`, `triggered_by`, `metadata`, `related_message_id`, `related_property_id`, `timestamp`

## 3. UI field model

### Lead identity
- Customer name
- Phone number
- EFPS source number(s)
- Classification
- Lead status
- Priority
- Last interaction
- New activity / needs analysis state

### Requirements
- BHK
- Preferred location(s)
- Budget min/max
- Furnishing
- Occupancy/tenant type
- Move-in date
- Pet preference
- Parking
- Current requirement
- Notes

### Conversation
- Message body
- Direction
- Timestamp
- Sender
- Source number
- Message type
- Media reference
- History coverage state

### Follow-up
- Next follow-up date/time
- Next action
- Follow-up count
- Overdue state
- Follow-up note

### AI and drafts
- Current saved intelligence
- Requirement proposals
- Evidence
- AI run history
- Draft versions
- Draft status
- Verified inventory references

## 4. Inventory — 48-field source contract

The CRM uses the canonical `Housing_Listings` field names and physical order already established in `shared/google_sheets/schema.py`:

`listing_id`, `status`, `intake_status`, `internal_property_type`, `listing_state`, `onboarded_on`, `raw_message_text`, `locality`, `society_name`, `landmark`, `pincode`, `google_maps_url`, `furnish_type`, `BHK`, `bathrooms`, `balconies`, `floor_number`, `total_floors`, `built_up_area`, `carpet_area`, `monthly_rent`, `maintenance`, `maintenance_included`, `security_deposit`, `preferred_tenant_type`, `bachelor_preference`, `pet_friendly`, `servant_room`, `covered_parking`, `open_parking`, `society_amenities`, `flat_furnishings`, `property_highlights`, `catalog_title`, `cloudinary_image_urls`, `age_of_property_years`, `whatsapp_contact_link`, `whatsapp_group_link`, `transaction_type`, `property_subtype`, `city`, `posted_url`, `posted_at`, `error_notes`, `meta_catalog_id`, `meta_catalog_status`, `source_group`, `inventory_locked`

AU/`source_group` and AV/`inventory_locked` remain reserved under the current repository contract.

## 5. Provenance

Every CRM UI value is conceptually one of:

- Verified source
- Human-edited CRM state
- AI-derived proposal/analysis
- System state
- Synthetic/illustrative

The production UI uses reconciled source-backed records for `+919148338801`; synthetic fixtures remain isolated test data.

## 6. Future local CRM entities

Planned application tables/records:

`customers`, `lead_sources`, `requirements`, `requirement_history`, `conversations`, `messages`, `ai_runs`, `reply_drafts`, `inventory_snapshot`, `property_matches`, `property_interactions`, `inventory_controls`, `audit_events`, `sync_runs`, `sync_conflicts`, `webhook_events`.

These are application-layer records, not replacements for the historical source evidence.


## 7. Provisioned operational PostgreSQL schema

Supabase `easyfind-crm` contains the operational CRM tables including the durable `crm_webhook_events` ingress/audit table. The source SQLite is historical migration evidence, not a second live editable database. Stable message deduplication uses `(source_number,provider_message_id)`. Live WhAPI ingress is enabled for `+919148338801`; webhook events are recorded before reconciliation into messages/classifications/leads. Contact classification is operator-gated. Tenant type is stored as a lead requirement, not as a separate header editor. Operational tables use RLS and browser-facing access remains protected through the CRM server. Media bytes are excluded; future references use Cloudinary URLs.


## 2026-10-01 — Production AI + normalized requirements implementation

Implemented on `crm-ui-dashboard` and verified locally:
- Requirements are now a normalized one-row-per-lead table, `crm_lead_requirements`, with fixed inventory-matchable fields: BHK, budget, preferred locations, tenant type, move-in date, pets, veg/non-veg, furnishing, parking, property type, bathrooms, occupancy count, lease term, preferred floor, preferred amenities and notes. `lead_id`, timestamps and `updated_by` preserve relational/audit linkage. Legacy `crm_leads.requirements` remains a compatibility mirror, not the authoritative edit surface.
- Requirements are editable from Lead Workspace and persisted transactionally through the protected CRM server.
- AI is no longer synthetic-fixture-only. Production analysis receives the complete chronological lead conversation, normalized requirements, requirement evidence, operator notes, prior AI runs and a per-lead AI cursor.
- AI output contains summary/timeline, evidence-backed requirement proposals, missing information, contradictions, suggested lead status, reply strategy, reply draft and evidence. Lead status remains suggestion-only.
- Requirement proposals require explicit operator acceptance; acceptance updates the normalized requirement table and appends requirement evidence. Reject is also audited.
- Every lead has its own AI cursor; the workspace exposes AI run history, requirement evidence, proposal review, draft editor and draft history.
- AI reply drafts are versioned in `crm_drafts`. The operator can edit/save/copy/open WhatsApp; the CRM never auto-sends the draft.
- Root `steering.md` now contains production EFPS context and explicit rules for full-history analysis, cold-lead reactivation, requirement evidence, inventory truth and operator-only sending. Public EasyFind context is based on the official EasyFind Property Solutions site. (official site: https://www.easyfindprops.com/)
- Live Supabase verification after schema deployment: 186 requirement profiles, 186 per-lead AI cursors, 6,622 CRM messages (4,228 outgoing), 195 webhook events (195 processed, 0 failed). That sentence records the earlier zero-state checkpoint; the current live database has 2 AI runs and 2 drafts, with provenance now stored on each draft.

## 2026-10-01 — Production AI and normalized requirement model

`crm_lead_requirements` is the normalized operator-editable requirement profile. It is keyed by `lead_id` and contains BHK, budget, preferred locations, tenant type, move-in date, pets, veg/non-veg, furnishing, parking, property type, bathrooms, occupancy count, lease term, preferred floor, preferred amenities and notes, plus audit timestamps and `updated_by`. `crm_leads.requirements` remains a compatibility mirror.

The production AI workspace also consumes `crm_ai_runs`, `crm_requirement_evidence`, `crm_drafts`, `crm_ai_cursors`, and the complete `crm_messages` history for the lead. AI status is advisory; requirement application is explicit and audited; reply drafts are versioned and operator-controlled.

## 2026-10-01 — Draft AI provenance

`crm_drafts` now stores `ai_run_id`, `ai_provider`, and `model_name` so every generated draft can be traced to the AI run/provider that produced it. Migration `016_crm_draft_ai_provenance.sql` is applied in production. Existing drafts were backfilled from their nearest preceding `crm_ai_runs` record; current verified state is 2 drafts, both from Ollama-era runs.

## 2026-10-01 — AI provenance, evidence, outcomes and stale-draft controls

`crm_ai_runs` now stores `provider`, `fallback_from`, and `fallback_reason`. `crm_drafts` now stores `ai_run_id`, `ai_provider`, `model_name`, `evidence_message_ids`, `evidence_summary`, and `sent_at`. Draft freshness is derived from whether newer CRM messages exist after draft creation. This supports model auditability, source evidence, stale-draft detection, and explicit operator outcome tracking without enabling automatic WhatsApp sending.
