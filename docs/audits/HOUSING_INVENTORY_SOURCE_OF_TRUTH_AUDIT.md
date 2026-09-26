# Housing Inventory Source-of-Truth Audit

**Date:** 26 September 2026  
**Auditor:** AI Agent (Kiro)  
**Repository:** `zeidhussain9-cloud/efps-internal-automatios`  
**Branch:** `main` (audit conducted on `audit/housing-inventory-source-of-truth-2026-09-26`)  
**Spreadsheet ID:** `1zdOLWklkWlnVECCtcH4SJj6vm6nEVjINpTT2U2UJEKc`  
**Primary Worksheet:** `Housing_Listings`

---

## Executive Summary

This audit documents the complete operational state of the EasyFind Property Solutions (EFPS) housing inventory system as it exists today. The investigation covered repository code, documentation, live Google Sheets data, and operational workflows to establish ground truth for integrating a new local-first CRM.

### Key Findings

**VERIFIED:**
1. Live spreadsheet has 87 active property rows (81 with listing IDs) across 1,246 total rows
2. Schema contract version 4 defines 48 columns (A:AV) with three-stage population model
3. **CRITICAL DISCREPANCY:** Column L physical header is "w" but schema declares "google_maps_url"
4. Current system successfully processes properties through all three stages (Intake → Processing → Publishing)
5. Reserved columns AU (`source_group`) and AV (`inventory_locked`) must remain blank per current contract
6. No current audit trail for manual Sheet edits; changes are not logged

**INFERRED:**
1. Column L discrepancy suggests either a manual header edit or schema drift
2. Six blank rows indicate incomplete or abandoned intake attempts
3. Photo collection workflow requires manual Slack-based operator intervention

**UNVERIFIED:**
1. Current AWS Lambda deployment state and commit version
2. Live webhook traffic routing and message deduplication
3. Whether AU/AV columns contain historical data requiring cleanup
4. Exact operational ownership of manual Sheet edits vs. automated updates

---

## 1. Repository and Runtime Details

### Repository Information
**Status:** VERIFIED

- **GitHub Repository:** `zeidhussain9-cloud/efps-internal-automatios`
- **Default Branch:** `main`
- **Canonical Schema:** `shared/google_sheets/schema.py`
- **Contract Version:** 4
- **Last Documentation Update:** References throughout indicate active maintenance through September 2026

### Runtime Components
**Status:** VERIFIED (code) / UNVERIFIED (deployment)

**Verified Code Modules:**

| Module | Location | Purpose | Status |
|--------|----------|---------|--------|
| Inventory Management | `modules/efps-inventory-mgmnt/` | Stage 1 & 2 processing | Active, production-grade |
| Housing Portal | `modules/efps-housing-portal-mgmnt/` | Stage 3 housing posting | Partially implemented |
| Meta Catalogue | `modules/efps_meta_catalogue_mgmnt/` | Stage 3 WhatsApp catalogue | Active, operational |
| Google Sheets Client | `shared/google_sheets/` | Schema & transport | Active |
| Google Maps | `shared/google_maps/` | Location resolution | Active |
| WhatsApp (WhAPI) | `shared/whatsapp_whapi/` | Message intake | Active |
| Slack | `shared/slack/` | Operational UI | Active |
| Cloudinary | `shared/cloudinary/` | Media storage | Active |

**Deployment Environment:**
- Platform: AWS Lambda (Python 3.12)
- SAM Template: `template.yaml`
- Credentials: AWS Secrets Manager (ARNs referenced, not values)
- **Deployment Status:** UNVERIFIED - Code exists but live Lambda version unknown

**Entry Points:**
1. **WhAPI Webhook** → `webhook_handler.py` → Routes to inventory or leads
2. **Slack Commands** → `/efps` command router → Multiple workflows
3. **Scheduled Handler** → `handler.py` → Processes Raw rows
4. **Manual Scripts** → `tools/run_phase1_rows.py` → Direct row processing

---

## 2. Complete Workbook and Tab Inventory

### Live Spreadsheet Overview
**Status:** VERIFIED (2026-09-26)

**Spreadsheet:** "Housing Agent — Listings"  
**URL:** `https://docs.google.com/spreadsheets/d/1zdOLWklkWlnVECCtcH4SJj6vm6nEVjINpTT2U2UJEKc/edit`  
**Locale:** `en_GB`  
**Timezone:** `Asia/Calcutta`  
**Service Account:** `gcpnew@easyfind-automations.iam.gserviceaccount.com`

### Tab-by-Tab Inventory

| Tab Name | Sheet ID | Hidden | Rows | Cols | Index | Purpose | Status |
|----------|----------|--------|------|------|-------|---------|--------|
| `backup_2026-08-30` | 1969679469 | Yes | 980 | 43 | 0 | Historical backup | BACKUP |
| `backup_2026-09-09_pre-cleanup` | 474617402 | Yes | 1,163 | 47 | 1 | Pre-cleanup backup | BACKUP |
| `Housing_Listings` | 655427889 | **No** | 1,246 | 48 | 2 | **ACTIVE INVENTORY** | **LIVE** |
| `Housing_Listings_copy` | 0 | Yes | 1,209 | 48 | 3 | Working copy | BACKUP |
| `config` | 519357567 | No | 1,000 | 26 | 4 | System configuration | ACTIVE |
| `Sheet4` | 2087160774 | Yes | 1,000 | 26 | 5 | Unknown/unused | LEGACY |
| `Sheet6` | 1736864104 | Yes | 1,000 | 26 | 6 | Unknown/unused | LEGACY |
| `Sheet11` | 149334732 | Yes | 1,000 | 25 | 7 | Unknown/unused | LEGACY |
| `Copy of Housing_Listings` | 1309175723 | Yes | 981 | 43 | 8 | Old backup | LEGACY |
| `leads` | 1392924935 | No | 1,000 | 26 | 9 | Lead management data | ACTIVE |
| `inventory_registry` | 624691283 | No | 1,000 | 26 | 10 | Registry/tracking | ACTIVE |
| `interactions` | 2083039215 | No | 1,000 | 26 | 11 | User interactions log | ACTIVE |
| `sessions` | 354433187 | No | 1,000 | 26 | 12 | Session tracking | ACTIVE |

### Config Tab Details
**Status:** VERIFIED

The `config` tab contains system-level configuration:
```
approved_count: 0
approval_threshold: 10
```

**Analysis:** Appears to be a legacy approval counter, possibly related to the removed society approval workflow mentioned in documentation.

---

## 3. Physical Column-by-Column Data Dictionary

### Housing_Listings Schema (48 Columns: A:AV)

#### CRITICAL SCHEMA DISCREPANCY

**Column L Header Mismatch:**
- **Schema Declares:** `google_maps_url`
- **Live Sheet Shows:** `w`
- **Severity:** HIGH - This breaks schema contract assumptions
- **Impact:** Code expecting "google_maps_url" header will not find it via header lookup
- **Status:** VERIFIED DISCREPANCY

### Complete Column Inventory


| Col | Letter | Schema Name | Live Header | Owner | Stage | CRM Read | CRM Write | Notes |
|-----|--------|-------------|-------------|-------|-------|----------|-----------|-------|
| 1 | A | `listing_id` | listing_id | PANEL | STAGE_1 | ✓ | ✗ | Immutable identity (EF-YYMM-XXXX) |
| 2 | B | `status` | status | PANEL | STAGE_1 | ✓ | ✗ | Raw→Pending→Needs Review |
| 3 | C | `intake_status` | intake_status | PANEL | STAGE_1 | ✓ | ⚠️ | Raw→Processed→Catalogue Ready→Published |
| 4 | D | `internal_property_type` | internal_property_type | PANEL | STAGE_2 | ✓ | ⚠️ | Gated Community/Semi Gated/Standalone |
| 5 | E | `listing_state` | listing_state | PANEL | STAGE_3 | ✓ | ⚠️ | Available/Rented Out/On Hold - **CRM may own this** |
| 6 | F | `onboarded_on` | onboarded_on | PANEL | STAGE_1 | ✓ | ✗ | IST timestamp, immutable |
| 7 | G | `raw_message_text` | raw_message_text | PANEL | STAGE_1 | ✓ | ✗ | Authoritative source, never replaced |
| 8 | H | `locality` | locality | PANEL | STAGE_2 | ✓ | ⚠️ | Maps may replace deterministic value |
| 9 | I | `society_name` | society_name | PANEL | STAGE_2 | ✓ | ⚠️ | Property/building name |
| 10 | J | `landmark` | landmark | PANEL | STAGE_2 | ✓ | ⚠️ | Never inherits locality |
| 11 | K | `pincode` | pincode | PANEL | STAGE_2 | ✓ | ⚠️ | Optional, Maps-enriched |
| 12 | L | `google_maps_url` | **w** | PANEL | STAGE_2 | ✓ | ⚠️ | **HEADER MISMATCH** |
| 13 | M | `furnish_type` | furnish_type | PANEL | STAGE_2 | ✓ | ⚠️ | Fully/Semi Furnished (blank=unfurnished) |
| 14 | N | `BHK` | BHK | PANEL | STAGE_2 | ✓ | ⚠️ | Integer or decimal (2.5 BHK, 1 RK) |
| 15 | O | `bathrooms` | bathrooms | PANEL | STAGE_2 | ✓ | ⚠️ | Numeric count |
| 16 | P | `balconies` | balconies | PANEL | STAGE_2 | ✓ | ⚠️ | Numeric count |
| 17 | Q | `floor_number` | floor_number | PANEL | STAGE_2 | ✓ | ⚠️ | Current floor (G, 1, 12, Duplex) |
| 18 | R | `total_floors` | total_floors | PANEL | STAGE_2 | ✓ | ⚠️ | Building height |
| 19 | S | `built_up_area` | built_up_area | PANEL | STAGE_2 | ✓ | ⚠️ | Square feet |
| 20 | T | `carpet_area` | carpet_area | PANEL | STAGE_2 | ✓ | ⚠️ | Computed as 90% if blank |
| 21 | U | `monthly_rent` | monthly_rent | PANEL | STAGE_2 | ✓ | ⚠️ | Required field |
| 22 | V | `maintenance` | maintenance | PANEL | STAGE_2 | ✓ | ⚠️ | Amount or qualifiers (+ Water) |
| 23 | W | `maintenance_included` | maintenance_included | PANEL | STAGE_2 | ✓ | ⚠️ | Yes/No |
| 24 | X | `security_deposit` | security_deposit | PANEL | STAGE_2 | ✓ | ⚠️ | Amount or months converted |
| 25 | Y | `preferred_tenant_type` | preferred_tenant_type | PANEL | STAGE_2 | ✓ | ⚠️ | Family/Open For All |
| 26 | Z | `bachelor_preference` | bachelor_preference | PANEL | STAGE_2 | ✓ | ⚠️ | Female Only /Male Only/Open for both |
| 27 | AA | `pet_friendly` | pet_friendly | PANEL | STAGE_2 | ✓ | ⚠️ | Yes/No (default Yes) |
| 28 | AB | `servant_room` | servant_room | PANEL | STAGE_2 | ✓ | ⚠️ | Yes/No (default No) |
| 29 | AC | `covered_parking` | covered_parking | PANEL | STAGE_2 | ✓ | ⚠️ | 0/1/2/3/3+ |
| 30 | AD | `open_parking` | open_parking | PANEL | STAGE_2 | ✓ | ⚠️ | Numeric or "-" |
| 31 | AE | `society_amenities` | society_amenities | PANEL | STAGE_2 | ✓ | ⚠️ | Exact dropdown values |
| 32 | AF | `flat_furnishings` | flat_furnishings | PANEL | STAGE_2 | ✓ | ⚠️ | Exact dropdown values |
| 33 | AG | `property_highlights` | property_highlights | PANEL | STAGE_2 | ✓ | ⚠️ | Optional text |
| 34 | AH | `catalog_title` | catalog_title | PANEL | STAGE_2 | ✓ | ⚠️ | Display title |
| 35 | AI | `cloudinary_image_urls` | cloudinary_image_urls | PANEL | STAGE_2 | ✓ | ⚠️ | Comma-separated URLs |
| 36 | AJ | `age_of_property_years` | age_of_property_years | PANEL | STAGE_2 | ✓ | ⚠️ | Optional numeric |
| 37 | AK | `whatsapp_contact_link` | whatsapp_contact_link | PANEL | STAGE_1 | ✓ | ✗ | Fixed company link |
| 38 | AL | `whatsapp_group_link` | whatsapp_group_link | PANEL | STAGE_1 | ✓ | ✗ | Fixed company link |
| 39 | AM | `transaction_type` | transaction_type | PANEL | STAGE_1 | ✓ | ✗ | Fixed "Rent" |
| 40 | AN | `property_subtype` | property_subtype | PANEL | STAGE_2 | ✓ | ⚠️ | Apartment/Villa/Studio/Duplex/etc |
| 41 | AO | `city` | city | PANEL | STAGE_1 | ✓ | ✗ | Fixed "Bengaluru" |
| 42 | AP | `posted_url` | posted_url | HOUSING | STAGE_3 | ✓ | ✗ | Housing portal owns |
| 43 | AQ | `posted_at` | posted_at | HOUSING | STAGE_3 | ✓ | ✗ | Housing portal owns |
| 44 | AR | `error_notes` | error_notes | HOUSING | STAGE_3 | ✓ | ✗ | Housing portal owns |
| 45 | AS | `meta_catalog_id` | meta_catalog_id | META | STAGE_3 | ✓ | ✗ | WhatsApp product ID |
| 46 | AT | `meta_catalog_status` | meta_catalog_status | META | STAGE_3 | ✓ | ✗ | Posted/Removed |
| 47 | AU | `source_group` | source_group | RESERVED | RESERVED | ✓ | ✗ | **MUST REMAIN BLANK** |
| 48 | AV | `inventory_locked` | inventory_locked | RESERVED | RESERVED | ✓ | ✗ | **MUST REMAIN BLANK** |

**Legend:**
- ✓ = Safe for CRM
- ✗ = Must not write
- ⚠️ = Write only with coordination and business rules

---

## 4. End-to-End Property Lifecycle Flow

### Stage 1: Initial Webhook Intake
**Status:** VERIFIED (code) / UNVERIFIED (live deployment)

**Entry Point:** `modules/efps-inventory-mgmnt/src/inventory_runtime.py`


**Process Flow:**

1. **WhatsApp Message Arrival**
   - WhAPI webhook receives message from authorized senders (917975102130, 919902024973)
   - `webhook_handler.py` routes to inventory listener vs. lead management
   - Message contains "NEW" marker or continuation text

2. **Session Management**
   - `inventory_runtime.py` manages durable session state in DynamoDB (`efps-sessions` table)
   - "NEW" message opens a property session
   - Subsequent messages accumulate until next "NEW"
   - **Image captions extracted:** Forwarded property listings with text descriptions are captured
   - Session close triggers Stage 2 processing

3. **Row Creation**
   - New property inserts at **row 2** (pushing existing down - most recent first)
   - Generates immutable `listing_id` in format `EF-YYMM-XXXX`
   - Sets `status = Raw`, `intake_status = Raw`
   - Records `onboarded_on` timestamp (IST format: "25 Sep 2026, 8:39 AM")
   - Preserves complete `raw_message_text` as authoritative source

**Current State:** Code exists; live webhook routing UNVERIFIED

---

### Stage 2: Deterministic Extraction & Property Processing
**Status:** VERIFIED (code and contracts)

**Entry Point:** `modules/efps-inventory-mgmnt/src/pipeline.py:deterministic()`

**Processing Pipeline:**

```
raw_message_text
  ├─→ source_segments.py      [Segment concatenated messages]
  ├─→ extract.py              [Discover field candidates]
  ├─→ field_resolution.py     [Select authoritative values for BHK, maintenance, property type]
  ├─→ normalize.py            [Apply business rules and dependencies]
  ├─→ validate.py             [Contract compliance check]
  ├─→ google_maps             [Enrich locality, pincode - network call]
  └─→ ai.py                   [Optional wording beautification only]
```

**Critical Resolution Rules:**

1. **internal_property_type** (drives amenities & parking defaults)
   - Explicit "Community: Gated Community" source wins
   - Explicit negative ("Standalone") is authoritative
   - Blank when unresolved (never fabricated as Standalone)
   - Exact outputs: `Gated Community`, `Semi Gated`, `Standalone`

2. **BHK** (preserves decimals, later corrections win)
   - Accepts 2.5 BHK, 1 RK forms
   - Later explicit values supersede earlier
   - Existing Sheet values never used as source

3. **maintenance** (unit normalization, qualifier preservation)
   - "Included" → `maintenance = 0`, `maintenance_included = Yes`
   - "Included + Water" → `maintenance = 0 + Water`, `maintenance_included = Yes`
   - Separate amount → normalize K/lakh, set `maintenance_included = No`
   - Preserves qualifiers like "+ Water"

4. **Google Maps URL** (deterministic extraction, not network)
   - Extracted from source text immediately
   - Supports short links and full URLs
   - Network resolution is separate enrichment step

5. **Landmark vs. Society**
   - `📍 Landmark:` + URL → landmark stays blank, URL goes to google_maps_url
   - Landmark never inherits locality
   - Society falls back to locality only after enrichment

**Dependency Chain:**
```
internal_property_type → society_amenities (exact dropdown values)
                      → covered_parking (default 1 when blank for Gated/Semi)
furnish_type → flat_furnishings (default bundles when blank)
preferred_tenant_type → bachelor_preference (Family=blank, Open For All=Open for both)
maintenance → maintenance_included (Yes/No)
built_up_area → carpet_area (90% fallback when blank)
monthly_rent → security_deposit (when expressed in months)
```

**Outcome:**
- Success: `status = Pending`, `intake_status = Processed`
- Validation Failure: `status = Needs Review`
- Column updates: A:D, F:AO, AU (protected: E, AP:AT, AV)

**Current State:** Fully implemented, regression-tested, contract-documented

---

### Stage 3a: Photo Collection (Manual Slack Workflow)
**Status:** ACTIVE (temporary manual process)

**Entry Point:** Slack command `/efps photos start`

**Process:**

1. Operator runs `/efps photos start`
2. System finds next property with `intake_status = Processed` and no `cloudinary_image_urls`
3. Posts property card to Slack thread
4. Operator attaches photos to thread
5. Operator replies `done`
6. System uploads to Cloudinary: `properties/{listing_id}/photo_{n}.jpg`
7. Writes comma-separated URLs back to `cloudinary_image_urls` column
8. Auto-advances to `intake_status = Catalogue Ready` IF:
   - `status = Pending`
   - Photos present
   - `listing_state ≠ Rented Out`
   - No existing `meta_catalog_id`

**Current Gap:** Webhook does not extract/persist media directly; Slack is temporary workaround

**Current State:** Operational, documented as temporary

---

### Stage 3b: Meta Catalogue Publishing
**Status:** ACTIVE

**Entry Point:** Slack command `/efps catalogue start`

**Process:**

1. Operator runs `/efps catalogue start` → confirms with `go`
2. System filters properties where `intake_status = Catalogue Ready`
3. Generates deterministic description (no AI):
   - Title from `catalog_title`
   - Bullet list: rent, deposit, maintenance, size, floor, tenant, pets, availability
   - Footer: society/location + Maps link
4. Calls WhAPI: `POST /business/products` with description, images, price
5. On success:
   - Writes `meta_catalog_id` (Product ID)
   - Sets `meta_catalog_status = Posted`
   - Updates `intake_status = Published`

**Current State:** Operational, documented

---

## 5. Ownership and Authority Matrix

### Write Authority by Owner

| Owner | Columns | Lifecycle Stage | Automation |
|-------|---------|----------------|------------|
| PANEL (Inventory Stage 1/2) | A:D, F:AO, AU | Intake through validation | Fully automated |
| HOUSING_AGENT (Housing Portal) | AP, AQ, AR | Downstream publishing | Partially implemented |
| META_CATALOG (WhatsApp Catalogue) | AS, AT, C (updates intake_status) | Catalogue publishing | Fully automated |
| RESERVED | AU, AV | Future use | Must remain blank |

### Column E (`listing_state`) Special Case

**Schema Declaration:** PANEL owner, STAGE_3  
**Current Behavior:** Not populated by Phase-1 path  
**Observed Values:** Available (65), Rented Out (16), blank (6)  
**Source:** UNVERIFIED - May be manual edits or external process  
**CRM Consideration:** This column is a strong candidate for CRM ownership

---

## 6. Live Inventory Statistics

**Collection Date:** 26 September 2026  
**Method:** Direct Google Sheets API read  
**Status:** VERIFIED

### Overall Metrics

| Metric | Count |
|--------|-------|
| Total Sheet Rows | 1,246 |
| Data Rows (excluding header) | 87 |
| Properties with listing_id | 81 |
| Blank/Incomplete Rows | 6 |
| Unique listing_ids | 81 |
| Duplicate IDs | 0 |

### Status Distribution

**Column B (`status`):**
- Pending: 81
- Blank: 6

**Column C (`intake_status`):**
- Published: 65
- Rented Out: 11 (NOTE: Unusual - this should be in `listing_state`)
- Processed: 5
- Blank: 5
- "ranches": 1 (DATA ERROR - typo or corruption)

**Column E (`listing_state`):**
- Available: 65
- Rented Out: 16
- Blank: 6


### Property Characteristics

**BHK Distribution:**
- 3 BHK: 31
- 2 BHK: 29
- 1 BHK: 12
- 4 BHK: 5
- 2.5 BHK: 2 (decimal BHK verified)
- 1 RK: 2
- Blank: 6

**Internal Property Type:**
- Gated Community: 56 (69%)
- Semi Gated: 25 (31%)
- Standalone: 0
- Blank: 6

**Property Subtype:**
- Apartment: 77 (95%)
- Villa: 2
- Duplex: 1
- Studio: 1
- Blank: 6

**Preferred Tenant Type:**
- Distribution not sampled in detail but contract values observed: Family, Open For All

### Data Quality Issues

| Issue | Count | Severity |
|-------|-------|----------|
| Missing `monthly_rent` | 6 | HIGH - Required field |
| Missing `cloudinary_image_urls` | 11 | MEDIUM - Blocks catalogue |
| Blank rows (incomplete intake) | 6 | MEDIUM - Cleanup needed |
| Invalid `intake_status` value ("ranches") | 1 | HIGH - Data corruption |
| `intake_status = "Rented Out"` (wrong column) | 11 | HIGH - Should be in `listing_state` |

### Publishing Status

**Meta Catalogue:**
- `meta_catalog_id` populated: 76 (94%)
- `meta_catalog_status = Posted`: 65
- `meta_catalog_status = Removed`: 11
- Blank: 11

**Analysis:** High automation success rate. "Removed" status indicates properties taken off catalogue (likely rented).

---

## 7. Audit Trail and Change Tracking

### Current Audit Capabilities
**Status:** VERIFIED (gaps identified)

**What IS Tracked:**
1. **Initial Creation:** `listing_id`, `onboarded_on` timestamp (immutable)
2. **Raw Source:** `raw_message_text` preserved permanently
3. **Processing Outcome:** `status`, `intake_status` reflect pipeline state
4. **Stage 3 Actions:** `meta_catalog_id`, `meta_catalog_status`, `posted_url` record downstream operations

**What IS NOT Tracked:**
1. **Manual Sheet Edits:** No log of who changed what field, when, or why
2. **Field-Level History:** No previous values stored
3. **Edit Attribution:** Cannot distinguish:
   - Automated pipeline updates
   - Manual operator corrections
   - Service account vs. human user edits
4. **Column E Changes:** `listing_state` transitions not logged
5. **Photo Updates:** No record of who uploaded photos or when they were added/removed

### Existing Logs (Inferred from Architecture)

**DynamoDB `efps-sessions` Table:**
- Records Stage 1 session lifecycle
- Tracks message deduplication
- Preserves session state until closure
- **Does not** track post-closure modifications

**Lambda CloudWatch Logs:**
- Execution logs for webhook, scheduled handlers
- Error logs in `#eps-runtime-error-bugs-reporting` Slack channel
- **Does not** provide structured audit trail

**Google Sheets Revision History:**
- Google Sheets maintains native revision history
- Manual inspection required; not programmatically queried
- **Does not** provide structured API for audit queries

---

## 8. Proposed CRM Integration Contract

### Safe Read Operations

The CRM may safely READ all 48 columns for:
- Property search and filtering
- Lead matching and recommendations
- Display in CRM interface
- Reporting and analytics
- Status monitoring

**Critical:** CRM must handle Column L header discrepancy ("w" vs. "google_maps_url")

### Recommended Write Boundaries

#### CRM-Owned Fields (Safe to Write)

**Column E (`listing_state`):**
- **Rationale:** Not populated by Phase-1, likely manual today
- **CRM Use:** Track Available/On Hold/Rented Out/Reserved
- **Sync Direction:** CRM → Sheet (CRM authoritative)
- **Validation:** Must use exact values: "Available", "Rented Out", "On Hold"

**New CRM-Only Data (Local SQLite):**
- Lead-property associations
- Show schedules and outcomes
- Customer preferences and notes
- Agent assignments
- Communication history
- CRM-specific workflow states

#### Restricted Write Fields (Requires Coordination)

**Operational Updates (With Business Rules):**
- `cloudinary_image_urls` - Only if CRM implements photo management
- `property_highlights` - Only with deterministic contract
- `catalog_title` - Only with approval workflow
- Location fields (`locality`, `society_name`, `landmark`) - Only verified corrections

**Never Write (Pipeline/Downstream Owned):**
- `listing_id` - Immutable
- `status`, `intake_status` - Pipeline state machine
- `onboarded_on`, `raw_message_text` - Historical record
- `whatsapp_contact_link`, `whatsapp_group_link`, `transaction_type`, `city` - Fixed constants
- `posted_url`, `posted_at`, `error_notes` - Housing portal owns
- `meta_catalog_id`, `meta_catalog_status` - Meta catalogue owns
- `source_group`, `inventory_locked` - Reserved, must stay blank

### CRM Audit Database Schema (Proposed)

**Table: `property_changes`**
```sql
CREATE TABLE property_changes (
    id INTEGER PRIMARY KEY,
    listing_id TEXT NOT NULL,
    column_name TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    change_source TEXT NOT NULL,  -- 'crm_user', 'crm_auto', 'sheet_direct', 'pipeline'
    user_id TEXT,
    timestamp INTEGER NOT NULL,
    reason TEXT
);
```

**Change Detection Strategy:**
1. **CRM-Originated Changes:** Log immediately on write
2. **Sheet Direct Edits:** Periodic polling (every 5 min) with checksum comparison
3. **Service Account Changes:** Detect via Google Sheets API user metadata (if available)

### Synchronization Model

**CRM → Sheet:**
- Immediate write for CRM-owned fields
- Validation before write
- Retry logic with conflict detection
- Log all changes locally

**Sheet → CRM:**
- Poll every 60 seconds for property list changes
- Detect new listings, status changes, downstream updates
- Pull full row on change detection
- Update CRM cache
- Flag conflicts if CRM pending writes exist

**Conflict Resolution:**
- CRM-owned fields: CRM wins, overwrite Sheet
- Pipeline-owned fields: Sheet wins, update CRM cache
- Simultaneous edits: Last write wins, log conflict

---

## 9. Known Schema Discrepancies and Risks

### Critical Issues

#### 1. Column L Header Mismatch
**Status:** VERIFIED  
**Risk:** HIGH

- **Schema:** `google_maps_url`
- **Live Sheet:** `w`
- **Impact:** Code relying on header names will fail
- **Root Cause:** Unknown - Possible manual edit or migration artifact
- **Recommendation:** Restore header to `google_maps_url` OR update schema contract

#### 2. Reserved Columns AU/AV
**Status:** VERIFIED  
**Risk:** MEDIUM

- Current contract: Must remain blank
- Historical data may exist in these columns
- No code should read/write these columns
- **Recommendation:** Audit for historical data, plan controlled cleanup if needed

#### 3. intake_status Value Confusion
**Status:** VERIFIED  
**Risk:** HIGH

- 11 rows have `intake_status = "Rented Out"`
- "Rented Out" belongs in `listing_state`, not `intake_status`
- Valid `intake_status` values: Raw, Processed, Catalogue Ready, Published
- 1 row has `intake_status = "ranches"` (corruption)
- **Recommendation:** Data cleanup script to move "Rented Out" to correct column

### Medium-Risk Issues

#### 4. Blank Rows
- 6 rows with no `listing_id`
- May indicate abandoned intake sessions or manual deletions
- **Recommendation:** Investigate and delete if truly abandoned

#### 5. Missing Critical Fields
- 6 properties missing `monthly_rent` (required field)
- Likely correlate with blank rows
- **Recommendation:** Either complete or remove

#### 6. Photo Collection Gap
- 11 properties missing `cloudinary_image_urls`
- 5 stuck in `intake_status = Processed` (waiting for photos)
- Manual Slack workflow is bottleneck
- **Recommendation:** Implement direct webhook media extraction

---

## 10. Unanswered Questions Requiring Owner Confirmation

### Deployment and Operations

1. **What commit is currently deployed to AWS Lambda?**
   - Impact: Cannot verify if live system matches audited code

2. **Is the WhAPI webhook actively routing to inventory intake?**
   - Impact: Unknown if Stage 1 is receiving live traffic

3. **Who manually edits the Sheet directly?**
   - Impact: Cannot attribute changes or design audit capture

4. **What is the intended use of reserved columns AU/AV?**
   - Impact: Need to know before allowing any writes

5. **Do AU/AV contain historical data needing cleanup?**
   - Impact: May require migration before CRM integration

### Schema and Data

6. **Why is Column L header "w" instead of "google_maps_url"?**
   - Impact: Must resolve before relying on header-based lookups

7. **Should `listing_state` be CRM-managed or remain manual?**
   - Impact: Determines CRM write authority

8. **What caused 11 "Rented Out" values in `intake_status`?**
   - Impact: Indicates misunderstanding of field purpose or data entry error

9. **Is the "ranches" value in one row a known issue?**
   - Impact: Data integrity concern

### Workflows

10. **Is there a process for operators to correct extraction errors?**
    - Impact: CRM may need to support correction workflows

11. **How are duplicate properties detected and handled?**
    - Impact: CRM should enforce or respect duplicate detection

12. **What triggers `listing_state` changes today?**
    - Impact: Must preserve existing trigger logic

---

## 11. Evidence Appendix

### Repository Paths Referenced

```
shared/google_sheets/schema.py          - Canonical 48-column contract
modules/efps-inventory-mgmnt/           - Stage 1/2 implementation
  src/pipeline.py                       - Deterministic entry point
  src/field_resolution.py               - BHK/maintenance/property type resolution
  src/source_segments.py                - Message boundary parsing
  src/extract.py                        - Candidate extraction
  src/normalize.py                      - Business rules application
  src/validate.py                       - Contract validation
  src/inventory_runtime.py              - Live Stage-1 adapter
modules/efps_meta_catalogue_mgmnt/      - Stage 3 catalogue publishing
shared/slack/                           - Operational UI
shared/whatsapp_whapi/                  - WhatsApp intake
shared/google_maps/                     - Location enrichment
shared/cloudinary/                      - Media storage
docs/ARCHITECTURE.md                    - System architecture
docs/DATA_CONTRACTS.md                  - Field semantics
docs/DETERMINISTIC_FIELD_RESOLUTION.md  - Resolution contracts
docs/INFRASTRUCTURE.md                  - External systems
docs/DEPLOYMENT.md                      - SAM deployment
HANDOFF.md                              - Current implementation state
```

### Verification Commands Used

```bash
# Sheet metadata and tab inventory
python3 << 'PYEOF'
from google.oauth2 import service_account
from googleapiclient.discovery import build
import json

with open('gcpnew-key.json', 'r') as f:
    creds_info = json.load(f)
creds = service_account.Credentials.from_service_account_info(
    creds_info, scopes=['https://www.googleapis.com/auth/spreadsheets.readonly'])
service = build('sheets', 'v4', credentials=creds)
sheet = service.spreadsheets()

# Get all sheet metadata
spreadsheet = sheet.get(spreadsheetId='1zdOLWklkWlnVECCtcH4SJj6vm6nEVjINpTT2U2UJEKc').execute()
# ...analysis code...
PYEOF

# Data statistics
python3 << 'PYEOF'
# ...read A2:AV1246, analyze columns...
PYEOF
```

### MCP Google Sheets Tool Calls

```
mcp_google_sheets_list_sheets(spreadsheet_id='1zdOLWklkWlnVECCtcH4SJj6vm6nEVjINpTT2U2UJEKc')
mcp_google_sheets_get_sheet_data(spreadsheet_id='...', sheet='Housing_Listings', range='A1:AV1')
mcp_google_sheets_get_sheet_data(spreadsheet_id='...', sheet='Housing_Listings', range='A2:AV10')
```

### Investigation Timeline

- 2026-09-26 08:00 - Started repository investigation
- 2026-09-26 09:00 - Verified live Sheet access, discovered Column L discrepancy
- 2026-09-26 10:00 - Analyzed 87 live properties, identified data quality issues
- 2026-09-26 11:00 - Compiled audit report

---

## 12. Recommendations

### Immediate Actions (Before CRM Integration)

1. **Fix Column L Header**
   - Restore "w" → "google_maps_url" in live Sheet
   - OR update schema.py to match reality
   - **Priority:** CRITICAL

2. **Clean Data Anomalies**
   - Move 11 "Rented Out" from `intake_status` to `listing_state`
   - Fix "ranches" typo
   - Remove or complete 6 blank rows
   - **Priority:** HIGH

3. **Verify Deployment State**
   - Document exact Lambda commit deployed
   - Verify webhook routing configuration
   - Test end-to-end flow from WhatsApp → Sheet
   - **Priority:** HIGH

4. **Audit Reserved Columns**
   - Check if AU/AV contain historical data
   - Plan cleanup if needed before allowing writes
   - **Priority:** MEDIUM

### CRM Integration Strategy

5. **Start with Read-Only Mode**
   - CRM consumes all 48 columns for search/matching
   - Handle Column L discrepancy defensively
   - Build local cache with sync monitoring
   - **Priority:** HIGH

6. **Implement Local Audit Trail**
   - SQLite database for all CRM actions
   - Periodic Sheet polling for external changes
   - Change attribution and conflict detection
   - **Priority:** HIGH

7. **Phase Write Capabilities**
   - Phase 1: CRM owns `listing_state` only
   - Phase 2: Add photo management
   - Phase 3: Add correction workflows
   - Never write pipeline/downstream fields
   - **Priority:** MEDIUM

8. **Establish Data Governance**
   - Document who can edit what
   - Define correction approval process
   - Create operator training materials
   - **Priority:** MEDIUM

---

## Conclusion

The EFPS Housing Inventory system is **operationally functional** with a well-defined three-stage architecture. The canonical schema contract (version 4) accurately describes column semantics and ownership, with **one critical exception**: Column L physical header mismatch.

Live data shows **high automation success** (81 properties processed, 76 published to catalogue) but reveals **data quality issues** requiring cleanup before CRM integration.

The system has **no structured audit trail** for manual edits, making it impossible to attribute changes or detect conflicts programmatically. The proposed CRM must implement its own local audit database and defensive synchronization logic.

**The CRM must adapt to the existing inventory system.** The recommended integration approach:
1. Start read-only
2. Own `listing_state` column as first write capability
3. Maintain complete local audit trail
4. Respect existing pipeline/downstream boundaries
5. Never assume deployment state matches code state

All substantive findings are marked **VERIFIED**, **INFERRED**, or **UNVERIFIED** as requested.

---

**End of Audit Report**  
**Branch:** `audit/housing-inventory-source-of-truth-2026-09-26`  
**Ready for review and integration planning**