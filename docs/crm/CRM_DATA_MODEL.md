# EasyFind CRM — Canonical Data Model

**Canonical repository:** `zeidhussain9-cloud/efps-internal-automatios`  
**Branch:** `crm-ui-dashboard`  
**Status (2026-09-26):** Reconciled design contract; Supabase v1 schema provisioned. Live data import and UI integration pending.

## 1. Lead data source

The lead source for this CRM is the **local extracted dataset described in `docs/audits/LEADS_EXTRACTION_SOURCE_OF_TRUTH_AUDIT.md`** and the local SQLite database produced by that extraction.

The Leads Tracker Google Sheet, Slack lead workflow, DynamoDB lead workflow and future WhAPI webhook are outside the current CRM lead data path.

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

The prototype uses synthetic records only.

## 6. Future local CRM entities

Planned application tables/records:

`customers`, `lead_sources`, `requirements`, `requirement_history`, `conversations`, `messages`, `ai_runs`, `reply_drafts`, `inventory_snapshot`, `property_matches`, `property_interactions`, `inventory_controls`, `audit_events`, `sync_runs`, `sync_conflicts`, `webhook_events`.

These are application-layer records, not replacements for the historical source evidence.


## 7. Provisioned operational PostgreSQL schema

Supabase `easyfind-crm` in Mumbai contains nine tables: `crm_schema_migrations`, `crm_leads`, `crm_lead_sources`, `crm_messages`, `crm_followups`, `crm_activity`, `crm_ai_runs`, `crm_drafts`, `crm_property_actions`. The source SQLite is historical migration evidence, not a second live editable database. Stable deduplication is `(source_number,provider_message_id)`. This schema is a **v1 subset** of the broader conceptual entities above; webhook inbox, per-source AI cursor, requirement evidence and backup/restore are not yet implemented. All operational tables have RLS enabled and no browser-facing grants or policies. The server repository currently supports only parameterized reads behind a disabled-by-default API. Media bytes are excluded; future references use Cloudinary URLs.
