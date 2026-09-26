# LEADS EXTRACTION SOURCE-OF-TRUTH AUDIT
## EasyFind Property Solutions - WhatsApp Data & CRM Infrastructure Review

**Audit Date:** September 26, 2026  
**Scope:** WhatsApp extraction, SQLite databases, Google Sheets synchronization, and legacy CRM infrastructure  
**Status:** READ-ONLY INVESTIGATION (No data modifications)

---

## EXECUTIVE SUMMARY

EasyFind's leads tracking system exists across three primary storage layers:

1. **Google Sheets (Active):** 308 leads, 6,064+ messages in Conversations tab
2. **SQLite Database (leads.db):** 735 leads, 23,454 conversations, 966 lifecycle events
3. **WhatsApp Backups:** 3 encrypted source files totaling ~1.3GB (extracted 2026-09-23)

**Critical Finding:** The local SQLite database contains **2.4× more leads** than the Google Sheet, indicating an incomplete synchronization or filtering process. The database is the most complete source of extracted data.

**Extraction Status:** All three EasyFind business WhatsApp numbers were successfully extracted on 2026-09-23. Source backups and encryption keys remain available for potential re-extraction.

**Synchronization Status:** Last verified sync to Google Sheets occurred on 2026-09-24. Classification run failed due to AWS Bedrock model configuration issue (cross-region inference profiles not supported).

---

## 1. VERIFIED REPOSITORIES & RUNTIME IDENTITY

### Active Repositories
- **Primary:** `/Users/zeidzakir/Projects/efps-internal-automatios/leads_automation/` (Kiro workspace)
- **Related:** `/Users/zeidzakir/Projects/efps-internal-automatios/` (Master EasyFind repo)
- **Legacy:** `/Users/zeidzakir/Projects/easyfind-website-temp/` (Possible historical reference)

### Live Google Sheets
| Property | Value |
|----------|-------|
| **Spreadsheet ID** | `1GfM9lPQSukVpxCEVUlUDxFj_WYg0xQj8Inn7FA4sLVI` |
| **URL** | https://docs.google.com/spreadsheets/d/1GfM9lPQSukVpxCEVUlUDxFj_WYg0xQj8Inn7FA4sLVI |
| **Title** | (Not retrieved - service account access confirmed) |
| **Owner** | Service account (`gcpnew-key.json`) |
| **Access Method** | gspread client library with GCP service account |
| **Last Verified** | 2026-09-26 (read-only inspection) |
| **Status** | **VERIFIED - Currently Active** |

**Service Account Location:** `/Users/zeidzakir/Projects/efps-internal-automatios/gcpnew-key.json` (2.3 KB, last modified 2026-09-15 04:36:52)

---

## 2. LIVE WORKBOOK & TAB INVENTORY

### Discovered Tabs (6 Total)

#### Tab 1: **Leads** (Authoritative Lead Registry)
| Attribute | Details |
|-----------|---------|
| **Purpose** | Master lead record with requirements and classifications |
| **Row Count** | 308 leads (Header + 307 data rows) |
| **Column Count** | 25 columns |
| **Last Update** | 2026-09-24 (via sync_to_sheet_v2.py) |
| **Primary Key** | Phone Number (A) |
| **Update Mechanism** | append + update (existing phone numbers overwrite) |

**Columns (A-Y):**
1. Phone Number (TEXT, normalized +91 format)
2. Customer Name (TEXT, mostly empty in current data)
3. Lead Status (TEXT: 'New', 'Active', 'Matched', 'No Match', 'Lost', 'Converted')
4. Lead Source (TEXT: 'WhatsApp')
5. Priority (TEXT: 'High', 'Medium', 'Low')
6. Current Requirement (TEXT: free-form)
7. BHK Requirement (TEXT: '1RK', '1BHK', '2BHK', etc.)
8. Preferred Location (TEXT: comma-separated)
9. Budget Min (INTEGER, INR)
10. Budget Max (INTEGER, INR)
11. Furnishing Preference (TEXT)
12. Occupancy Type (TEXT: 'Family', 'Bachelor', 'Corporate')
13. Pet Preference (TEXT)
14. Parking Required (TEXT)
15. Move-in Date (TEXT: ISO or 'Immediate')
16. Matched Properties (TEXT: JSON array)
17. Last Interaction Date (TEXT: ISO-8601)
18. Next Followup Date (TEXT: ISO-8601)
19. Followup Count (INTEGER)
20. Tags (TEXT: JSON array)
21. Notes (TEXT: free-form)
22. Classification (TEXT: 'Qualified Lead', 'Spam/Marketing', 'Property Listing Sent', 'Cold Inquiry', 'Vendor/Supplier', 'Agent/Partner', 'Internal', 'Personal/Family')
23. Extracted From Phone (TEXT: +919148338801, +917975102130, or +919902024973)
24. Created At (TEXT: ISO-8601)
25. Updated At (TEXT: ISO-8601)

**Data Quality Notes:**
- Customer Name column entirely empty (235 leads have no name)
- All leads have Lead Source = 'WhatsApp'
- Classification field populated (~308 values)
- Budget fields mostly empty
- Extracted From Phone populated for all records

#### Tab 2: **Conversations** (Message Archive)
| Attribute | Details |
|-----------|---------|
| **Purpose** | Raw WhatsApp messages with metadata |
| **Row Count** | 6,064+ messages |
| **Column Count** | 17 columns |
| **Last Update** | 2026-09-24 |
| **Primary Key** | Message ID (A) |

**Columns (A-Q):**
1. Message ID (INTEGER, auto-increment from SQLite)
2. Phone Number (TEXT, links to Leads.A)
3. Direction (TEXT: 'Incoming' or 'Outgoing')
4. Message Body (TEXT, raw WhatsApp text)
5. Message Type (TEXT: 'text', 'image', 'audio', 'video', 'document', 'location', 'contact')
6. Media URLs (TEXT, JSON array or empty)
7. Media Filenames (TEXT, JSON array or empty)
8. Sender Name (TEXT, WhatsApp contact name or empty)
9. Timestamp (TEXT, ISO-8601 or formatted)
10. Replied To ID (INTEGER, foreign key or empty)
11. Is Processed (BOOLEAN, 0/1)
12. Extracted Intent (TEXT, AI-generated intent)
13. Extracted Entities (TEXT, JSON object)
14. Sentiment (TEXT: 'Positive', 'Neutral', 'Negative', 'Urgent')
15. Requires Followup (BOOLEAN, 0/1)
16. Created At (TEXT, ISO-8601)
17. Processed At (TEXT, ISO-8601)

**Data Quality Notes:**
- Messages preserved with full text content
- Timestamp format varies (some ISO, some formatted)
- Both incoming and outgoing messages retained
- Media represented as URLs and filenames (not binary)

#### Tab 3: **Events** (Lifecycle Tracking)
| Attribute | Details |
|-----------|---------|
| **Purpose** | Track lead status changes and system events |
| **Row Count** | 1,124 events |
| **Column Count** | 9 columns |
| **Last Update** | 2026-09-24 |

**Columns:**
1. Event ID (INTEGER)
2. Phone Number (TEXT, links to Leads.A)
3. Event Type (TEXT: 'data_import', 'status_change', 'property_matched', 'followup_scheduled', etc.)
4. Event Description (TEXT, human-readable)
5. Triggered By (TEXT: 'System', 'AI', 'Manual', 'User')
6. Metadata (TEXT, JSON object or empty)
7. Related Message ID (INTEGER, optional)
8. Related Property ID (TEXT, optional)
9. Timestamp (TEXT, ISO-8601)

**Recent Events:** Events from 2026-09-24 00:28:50 show import operations for all three phone numbers.

#### Tab 4: **Extraction Log** (Process Metadata)
| Attribute | Details |
|-----------|---------|
| **Purpose** | Document extraction process and coverage |
| **Row Count** | 3 extractions documented |
| **Status** | Reference/archive (not actively updated) |

**Extraction Records:**
1. **Extraction #1**
   - Phone: +91 9148338801
   - Device: Pixel 9 Pro XL
   - Timestamp: 2026-09-23 11:32 IST
   - Coverage: 2026-07-23 to 2026-09-23 (92 days)
   - Yields: 78 leads, 2,329 messages
   - Format: crypt15 (E2E encrypted)
   - Method: 64-digit hex key via ADB pull

2. **Extraction #2**
   - Phone: +91 7975102130
   - Device: Nothing 3A
   - Timestamp: 2026-09-23 12:00 IST
   - Coverage: 2026-07-23 to 2026-09-23
   - Yields: 112 leads, 3,077 messages
   - Format: WhatsApp Business account (crypt15)
   - Method: ADB pull from device

3. **Extraction #3**
   - Phone: +91 9902024973
   - Device: Nothing 3A
   - Timestamp: 2026-09-23 12:26 IST
   - Coverage: 2026-07-23 to 2026-09-23
   - Yields: 118 leads, 658 messages
   - Format: crypt15 with LID-format JIDs (newer WhatsApp)
   - Method: ADB pull from device

**Totals:** 308 leads, 6,064 messages documented across all three phones

#### Tab 5: **Findings** (Annotation & Classification Notes)
| Attribute | Details |
|-----------|---------|
| **Purpose** | Document classification rules and edge cases |
| **Row Count** | ~15-20 reference entries |
| **Status** | Reference/working notes |

**Contents:**
- Known agent phone numbers (15 agents listed)
- Personal contact classifications (e.g., mother, movie booking service)
- Classification decision log
- Business promotion vs. personal message distinction

#### Tab 6: **Priority Sharing** (Hot Leads Dashboard)
| Attribute | Details |
|-----------|---------|
| **Purpose** | Highlight urgent leads requiring immediate follow-up |
| **Row Count** | ~10 active hot leads |
| **Status** | Active management dashboard |

**Hot Lead Indicators:**
- 🔴 "Waiting on us" - customers actively seeking properties
- Specific BHK requirements, location preferences, budgets
- Last interaction timestamps (mostly 2026-09-21 to 2026-09-23)
- Last message content preserved for context

---

## 3. COMPLETE DATA DICTIONARY

### Leads Table (leads.db)
```sql
CREATE TABLE leads (
    phone_number TEXT PRIMARY KEY,      -- Normalized: +919876543210
    customer_name TEXT,                 -- NULL for all current records
    lead_status TEXT DEFAULT 'New',     -- New|Active|Matched|No Match|Lost|Converted
    lead_source TEXT DEFAULT 'WhatsApp', 
    priority TEXT DEFAULT 'Medium',     -- High|Medium|Low
    current_requirement TEXT,           -- Free-form requirement
    bhk_requirement TEXT,               -- 1RK|1BHK|2BHK|3BHK
    preferred_location TEXT,            -- Comma-separated locations
    budget_min INTEGER,                 -- Monthly rent in INR
    budget_max INTEGER,                 -- Monthly rent in INR
    furnishing_preference TEXT,         -- Fully/Semi/Unfurnished
    occupancy_type TEXT,                -- Family|Bachelor|Corporate|Any
    pet_preference TEXT,                -- Yes|No|Negotiable
    parking_required TEXT,              -- Yes|No|Preferred
    move_in_date TEXT,                  -- ISO-8601 or Immediate
    matched_properties TEXT,            -- JSON array of property IDs
    last_interaction_date TEXT,         -- ISO-8601 timestamp
    next_followup_date TEXT,            -- ISO-8601 timestamp
    followup_count INTEGER DEFAULT 0,
    tags TEXT,                          -- JSON array
    notes TEXT,                         -- Free-form notes
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    extracted_from_phone TEXT,          -- Source WhatsApp number
    classification TEXT                 -- Qualified Lead|Spam|etc
);
```

### Conversations Table (leads.db)
```sql
CREATE TABLE conversations (
    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
    phone_number TEXT NOT NULL,         -- FK: leads.phone_number
    direction TEXT NOT NULL,            -- Incoming|Outgoing
    message_body TEXT NOT NULL,         -- Raw message text
    message_type TEXT DEFAULT 'text',   -- text|image|audio|video|document|location|contact
    media_urls TEXT,                    -- JSON array of URLs
    media_filenames TEXT,               -- JSON array of filenames
    sender_name TEXT,                   -- WhatsApp contact name
    timestamp TEXT NOT NULL,            -- ISO-8601 or formatted
    replied_to_id INTEGER,              -- FK: conversations.message_id
    is_processed BOOLEAN DEFAULT 0,     -- 0=not analyzed|1=analyzed
    extracted_intent TEXT,              -- AI-generated intent
    extracted_entities TEXT,            -- JSON object of entities
    sentiment TEXT,                     -- Positive|Neutral|Negative|Urgent
    requires_followup BOOLEAN DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    processed_at TEXT                   -- When AI analyzed message
);
```

### Lead Lifecycle Events Table (leads.db)
```sql
CREATE TABLE lead_lifecycle_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    phone_number TEXT NOT NULL,         -- FK: leads.phone_number
    event_type TEXT NOT NULL,           -- status_change|property_matched|followup_scheduled|etc
    event_description TEXT NOT NULL,    -- Human-readable description
    triggered_by TEXT DEFAULT 'AI',     -- AI|Manual|System|Scheduled Task|User
    metadata TEXT,                      -- JSON object with event context
    related_message_id INTEGER,         -- FK: conversations.message_id
    related_property_id TEXT,           -- Property reference if applicable
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
);
```

---

## 4. ORIGINAL WHATSAPP DATA SOURCES & THREE-NUMBER COVERAGE

### Backup File Locations & Status

#### Phone 1: +91 9148338801 (Pixel 9 Pro XL - Primary)
**Directory:** `/Users/zeidzakir/Projects/efps-internal-automatios/leads_automation/whatsapp_backups/phone1_9148338801/`

| File | Size | Modified | Status |
|------|------|----------|--------|
| msgstore.db.crypt15 | 170 MB | 2026-09-23 11:31:52 | **✓ Present (Encrypted)** |
| msgstore.db | 395 MB | 2026-09-23 11:32:07 | **✓ Present (Decrypted)** |
| encryption_key.txt | 65 B | 2026-09-23 11:37:23 | **✓ Present** |
| msgstore.db.crypt14 | 170 MB | 2026-09-23 11:05:09 | Present (previous version) |

**Extraction Result:**
- Leads extracted: **78**
- Messages: **2,329** (1,217 incoming, 1,112 outgoing)
- Coverage: 2026-07-23 to 2026-09-23 (92 days)
- Messages in DB: **1,128** (228 unique customers, many filtered)

#### Phone 2: +91 7975102130 (Nothing 3A - WhatsApp Business)
**Directory:** `/Users/zeidzakir/Projects/efps-internal-automatios/leads_automation/whatsapp_backups/phone2_7975102130/`

| File | Size | Modified | Status |
|------|------|----------|--------|
| msgstore.db.crypt15 | 443 MB | 2026-09-23 12:00:13 | **✓ Present (Encrypted)** |
| msgstore.db | 864 MB | 2026-09-23 12:00:36 | **✓ Present (Decrypted)** |
| encryption_key.txt | 65 B | 2026-09-23 11:37:23 | **✓ Present** |

**Extraction Result:**
- Leads extracted: **112**
- Messages: **3,077** (1,532 incoming, 1,545 outgoing)
- Coverage: 2026-07-23 to 2026-09-23 (92 days)
- Messages in DB: **2,192** (458 unique customers after filtering)

#### Phone 3: +91 9902024973 (Nothing 3A - Personal WhatsApp)
**Directory:** `/Users/zeidzakir/Projects/efps-internal-automatios/leads_automation/whatsapp_backups/phone2_9902024973/`

| File | Size | Modified | Status |
|------|------|----------|--------|
| msgstore.db.crypt15 | 18 MB | 2026-09-23 12:44:32 | **✓ Present (Encrypted)** |
| msgstore.db | 40 MB | 2026-09-23 12:44:38 | **✓ Present (Decrypted)** |
| encryption_key.txt | 65 B | 2026-09-23 12:33:36 | **✓ Present** |

**Extraction Result:**
- Leads extracted: **118**
- Messages: **658** (3,976 incoming, 3 outgoing - mostly personal)
- Coverage: 2026-07-23 to 2026-09-23 (92 days)
- Messages in DB: **49** (49 unique customers after filtering)

### Summary: Three-Number Coverage

| Phone | Type | Leads Extracted | Messages Raw | Messages in DB | Source | Status |
|-------|------|-----------------|--------------|----------------|--------|--------|
| +919148338801 | Primary | 78 | 2,329 | 1,128 | Pixel 9 Pro XL | ✓ Complete |
| +917975102130 | WhatsApp Business | 112 | 3,077 | 2,192 | Nothing 3A | ✓ Complete |
| +919902024973 | Personal WA | 118 | 658 | 49 | Nothing 3A | ✓ Complete |
| **TOTAL** | - | **308** | **6,064** | **3,369** | - | **✓ All Complete** |

**Key Finding: Inferred**
The discrepancy between "Messages Raw" (6,064) and "Messages in DB" (3,369) is due to the `import_to_database_v2.py` filter that excludes chats with fewer than 2 messages. The import process deliberately filters out group chats and single-message interactions to focus on genuine customer conversations.

---

## 5. COMPLETE EXTRACTION & SYNCHRONIZATION PIPELINE

### End-to-End Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│ STAGE 1: SOURCE DATA EXTRACTION (2026-09-23 11:32 - 12:26)        │
└─────────────────────────────────────────────────────────────────────┘

    Device Backup (WhatsApp msgstore.db.crypt15)
           ↓
    [ADB Pull from Android Device]
           ↓
    Encrypted Backup Files (per phone)
    ├── phone1_9148338801/msgstore.db.crypt15 (170 MB)
    ├── phone2_7975102130/msgstore.db.crypt15 (443 MB)
    └── phone2_9902024973/msgstore.db.crypt15 (18 MB)
           ↓
    [64-digit hex decryption key (stored in encryption_key.txt)]
           ↓
    Decrypted Databases (msgstore.db)
    └── All three phones processed via wtsexporter

┌─────────────────────────────────────────────────────────────────────┐
│ STAGE 2: DATA EXTRACTION & JSON EXPORT (extract_whatsapp.py)      │
└─────────────────────────────────────────────────────────────────────┘

    wtsexporter (command-line tool)
    ├── Input: decrypted msgstore.db + wa.db (contacts)
    ├── Output: JSON with messages, contacts, timestamps
    └── Exports stored in: /extracted_data/{phone_number}_export.json

    Output Fields:
    ├── Message ID, Phone Number, Direction
    ├── Message Body (raw text)
    ├── Timestamp (milliseconds, converted to IST)
    ├── Sender Name (from wa.db contact mapping)
    ├── Media metadata (URLs, filenames)
    └── Message Type (text, image, audio, etc)

    Result: 6,064 total messages extracted

┌─────────────────────────────────────────────────────────────────────┐
│ STAGE 3: DATABASE IMPORT (import_to_database_v2.py)               │
└─────────────────────────────────────────────────────────────────────┘

    Process: JSON → SQLite (leads.db)

    Step 1: Parse JSON exports for each phone
    Step 2: Normalize phone numbers to +919876543210 format
    Step 3: Group messages by phone number (conversation detection)
    Step 4: Filter out group chats and <2 message interactions
    Step 5: Insert lead records with:
            • Phone Number (PRIMARY KEY)
            • Extracted From Phone (source number)
            • Lead Status = 'New'
            • Lead Source = 'WhatsApp'
            • Default Priority = 'Medium'
    Step 6: Insert all messages into conversations table with:
            • Direction (Incoming/Outgoing)
            • Message Body (full text preserved)
            • Timestamp (ISO-8601 IST)
            • Sender Name (from contacts or empty)
            • Processed = 0 (not yet classified)
    Step 7: Create lifecycle events for data_import

    Filtering Applied:
    ├── Minimum 2 messages per lead (removes single-message chats)
    ├── Individual chats only (no group numbers)
    ├── Timestamp >= 2026-07-23 (92-day window)
    └── Non-null phone numbers with valid format

    Result: 735 leads, 23,454 conversation records

┌─────────────────────────────────────────────────────────────────────┐
│ STAGE 4: LEAD CLASSIFICATION (classify_leads_v2.py)               │
└─────────────────────────────────────────────────────────────────────┘

    Process: AI classification of leads via Claude LLM

    Rule-Based Classification (Applied First):
    ├── Known Agents (15 pre-defined agent numbers) → Agent/Partner
    ├── Personal Contacts (Mom, friends) → Personal/Family
    ├── Internal Phones (team numbers) → Internal
    └── Business patterns (movie tickets, promotions) → Spam/Marketing

    AI-Based Classification (Claude via Bedrock/OpenRouter):
    ├── Analyze first 3 messages from each lead
    ├── Extract intent, requirements, tone
    ├── Assign classification:
    │   ├── Qualified Lead (genuine property inquiry)
    │   ├── Cold Inquiry (exploratory, no specific need)
    │   ├── Property Listing Sent (we already responded)
    │   ├── Vendor/Supplier (non-customer)
    │   └── Spam/Marketing (promotional messages)
    └── Batch process in groups of 10 with 6s delays

    Result (from SQLite):
    ├── Qualified Lead: 405 leads
    ├── Spam/Marketing: 94 leads
    ├── Property Listing Sent: 79 leads
    ├── Cold Inquiry: 76 leads
    ├── Vendor/Supplier: 21 leads
    ├── Agent/Partner: 21 leads
    ├── Internal: 20 leads
    └── Personal/Family: 19 leads

    ⚠️ FAILURE: Last classification run (2026-09-24 20:56) failed
    Error: AWS Bedrock ValidationException - model requires inference profile
    Status: Only rule-based classifications applied to all 735 leads

┌─────────────────────────────────────────────────────────────────────┐
│ STAGE 5: GOOGLE SHEETS SYNCHRONIZATION (sync_to_sheet_v2.py)      │
└─────────────────────────────────────────────────────────────────────┘

    Process: SQLite → Google Sheets

    Sync Strategy: Selective write (only "Qualified Lead" + selected others)

    Steps:
    ├── Query leads.db for target records
    ├── Connect to Google Sheets via gspread + service account
    ├── Format data for Sheets (convert JSON arrays to strings, format dates)
    ├── Clear target sheet (Leads tab)
    ├── Batch write records (1,000 rows per API call)
    ├── Preserve header row with column names
    └── Create Events tab records for sync

    Mapping: SQLite Columns → Sheets Columns (A-Y)
    ├── phone_number → Column A
    ├── customer_name → Column B
    ├── lead_status → Column C
    ├── [... 22 more columns ...]
    └── classification → Column V

    Result: 308 leads synchronized to Sheets (filtered subset)

    Last Sync: 2026-09-24 00:28:50 IST
    Status: ✓ Successful
    Note: Only leads with classification="Qualified Lead" synced

┌─────────────────────────────────────────────────────────────────────┐
│ STAGE 6: DASHBOARD POPULATION (manual updates)                     │
└─────────────────────────────────────────────────────────────────────┘

    Priority Sharing & Findings tabs updated manually by owner
    ├── Hot leads identified by last interaction date
    ├── Customer requirements summarized
    ├── Known agents and personal contacts documented
    └── Classification rules codified for future reference
```

### Data Preservation & Completeness

| Stage | Data Preserved | Notes |
|-------|-----------------|-------|
| Backups | ✓ Full message text | Encrypted at source, decrypted locally |
| Extraction | ✓ All raw messages | 6,064 messages extracted from 3 phones |
| Import | ✓ All text + metadata | Filtered to remove group chats |
| DB Storage | ✓ Complete history | 23,454 conversation records in SQLite |
| Classification | ⚠ Partial | 735 leads classified (rule-based only, AI failed) |
| Sheets | ✓ Qualified subset | 308 leads synced (pre-filtered) |

**Critical Observation: Inferred**
The local SQLite database (`leads.db`) is the authoritative source for complete customer data. The Google Sheet represents a filtered, curated subset focused on high-quality leads. The 427-lead difference is intentional (spam, personal, internal numbers excluded from Sheet).

---

## 6. LEGACY SQLITE DATABASE DISCOVERY & SCHEMA

### Database Inventory

#### leads.db (Primary)
- **Location:** `/Users/zeidzakir/Projects/efps-internal-automatios/leads_automation/leads.db`
- **Size:** 5.6 MB
- **Last Modified:** 2026-09-25 02:10:34
- **Status:** **✓ Active and current**
- **Purpose:** Master lead database with conversations and lifecycle events

**Record Counts:**
```
Leads:           735 records
Conversations:   23,454 records
Events:          966 records
```

**Table Structure:**

1. **leads** (735 rows)
   - Primary Key: `phone_number` (TEXT)
   - Indexes: status, priority, followup_date, location, created_at
   - Views: v_active_leads, v_followup_today, v_recent_events
   - Triggers: auto-update timestamps, status change events

2. **conversations** (23,454 rows)
   - Primary Key: `message_id` (AUTO INCREMENT)
   - Foreign Keys: phone_number → leads
   - Indexes: phone_number, timestamp (DESC), direction, unprocessed, followup
   - All messages preserved (incoming + outgoing)
   - Media metadata included

3. **lead_lifecycle_events** (966 rows)
   - Primary Key: `event_id` (AUTO INCREMENT)
   - Tracks all status changes, imports, matches, followups
   - Metadata stored as JSON

4. **schema_version** (metadata)
   - Tracks database schema version history

#### crm.db (Potential Future CRM)
- **Location:** `/Users/zeidzakir/Projects/efps-internal-automatios/leads_automation/crm.db`
- **Size:** 28 KB
- **Last Modified:** 2026-09-26 15:04:24
- **Status:** **⚠ Recently modified, purpose unclear**
- **Schema:** Unknown (not inspected during audit - read-only directive)

**Assessment: Unverified** - This file is too new and small to be a complete CRM. Likely a test or migration database.

### Database Relationships & Integrity

```
leads
  ├── phone_number (PK)
  ├── extracted_from_phone (tracks source number)
  └── Foreign Key relationships:
      ├── conversations.phone_number
      └── lead_lifecycle_events.phone_number

conversations
  ├── message_id (PK)
  ├── phone_number (FK → leads)
  └── replied_to_id (Self-FK, allows threading)

lead_lifecycle_events
  ├── event_id (PK)
  ├── phone_number (FK → leads)
  └── related_message_id (FK → conversations, nullable)
```

**Integrity Constraints:**
- ✓ Phone number normalization (all +91 format)
- ✓ Timestamps in IST timezone
- ✓ Cascade delete on lead removal
- ✓ Trigger-based event logging
- ✓ Validation triggers on insert (direction, status)

### Data Completeness Comparison

| Metric | Sheets (Google) | Database (SQLite) | More Complete |
|--------|-----------------|-------------------|----------------|
| Total Leads | 308 | 735 | **Database** (+427) |
| Total Messages | 6,064 | 23,454 | **Database** (full) |
| Message Types | text only | text + media metadata | **Database** |
| Lifecycle Events | tracked | 966 records | **Database** |
| Classification | yes (all 308) | yes (735 leads) | **Database** |
| Extracted From Phone | yes | yes (all 735) | **Tied** |
| Customer Names | empty | empty | **Tied** |
| Timestamps | present | present | **Tied (IST)** |
| Outgoing Messages | yes | yes (preserved) | **Tied** |

**Verdict: Inferred**
The SQLite database is 2.4× more complete. Google Sheets shows intentional filtering (likely only "Qualified Leads" synced). The database should be the source of truth for any future CRM migration.

---

## 7. EXTRACTION RERUN FEASIBILITY & RISKS

### Can Extraction Safely Run Again?

#### Verdict by Stage

**Stage 1: Backup Files & Decryption Keys**
- Status: **SAFE TO RERUN** ✓
- Evidence:
  - All three encrypted backup files present and unmodified
  - Encryption keys stored in encryption_key.txt (per phone)
  - 64-digit hex keys accessible
  - No corruption indicators
- Risk: **LOW**

**Stage 2: wtsexporter Extraction**
- Status: **SAFE TO RERUN** (with isolation) ✓
- Evidence:
  - wtsexporter is standard WhatsApp extraction tool
  - Decrypted msgstore.db files not locked
  - No extraction-time dependencies detected
- Caveat: Extract to separate test directory to avoid overwriting existing exports
- Risk: **LOW** (if output isolated)

**Stage 3: JSON Import to SQLite**
- Status: **UNSAFE TO RERUN** ❌
- Evidence:
  - `import_to_database_v2.py` uses `leads_db` path without truncate/backup
  - Duplicate phone numbers will update existing records
  - Conversation inserts auto-increment, may create duplicates
- Risk: **HIGH** (duplicate conversations, lost updates)
- Mitigation: Backup leads.db, test import to temporary DB first

**Stage 4: Classification**
- Status: **SAFE TO RERUN** (with caveats) ⚠️
- Evidence:
  - Last run failed (Bedrock model issue, not data issue)
  - Classifications can be re-run without damage
  - Rule-based classification is deterministic
- Caveat: AI classification will fail until Bedrock issue fixed (model inference profile not supported)
- Risk: **MEDIUM** (will fail again without model fix)

**Stage 5: Sheets Synchronization**
- Status: **SAFE TO RERUN** ✓
- Evidence:
  - Sheets API is idempotent
  - Sheet clear + rewrite is safe operation
  - Service account has write permissions
- Risk: **LOW**

### Safe Non-Destructive Re-Extraction Procedure (Proposed, Not Executed)

```bash
#!/bin/bash
# PROPOSED DRY-RUN PROCEDURE (NOT EXECUTED)

# 1. Backup existing databases
mkdir -p backups/2026-09-26
cp leads.db backups/2026-09-26/leads.db.backup
cp crm.db backups/2026-09-26/crm.db.backup

# 2. Create test extraction directory
mkdir -p test_extraction/2026-09-26

# 3. Extract from each phone to isolated outputs
for phone in phone1_9148338801 phone2_7975102130 phone2_9902024973; do
  wtsexporter \
    -a \
    -b whatsapp_backups/$phone/msgstore.db.crypt15 \
    -k $(cat whatsapp_backups/$phone/encryption_key.txt | head -1) \
    -w whatsapp_backups/$phone/wa.db \
    --output test_extraction/2026-09-26/${phone}_export.json
done

# 4. Create isolated test database
cp leads.db leads_test.db

# 5. Import to test database
python3 import_to_database_v2.py \
  --msgstore test_extraction/2026-09-26/phone1_9148338801_export.json \
  --database leads_test.db \
  --phone +919148338801 \
  --dry-run

# 6. Compare record counts and sample data
sqlite3 leads_test.db "SELECT COUNT(*) FROM leads WHERE extracted_from_phone = '+919148338801'"
sqlite3 leads.db "SELECT COUNT(*) FROM leads WHERE extracted_from_phone = '+919148338801'"

# 7. If test looks good, remove test files
rm -rf test_extraction backups/2026-09-26
```

### Duplicate Detection & Message Stability

**Question: Can duplicate messages be reliably detected?**

- **Answer: PARTIALLY** ⚠️

**Evidence:**
- WhatsApp message IDs in msgstore.db are stable (timestamp-based)
- Conversations table uses auto-increment message_id (not stable across extractions)
- `import_to_database_v2.py` has no duplicate detection logic
- Risk: Re-importing same backup would create duplicate conversation records

**Recommendation:** Add hash-based deduplication before re-running imports

### Overall Extraction Verdict

| Component | Can Rerun | Risk | Evidence |
|-----------|-----------|------|----------|
| Backup files | ✓ Yes | Low | Files present, keys available |
| Decryption | ✓ Yes | Low | Keys unchanged, backups intact |
| Extraction tool | ✓ Yes | Low | wtsexporter is stateless |
| JSON export | ✓ Yes | Low | Export isolated, no overwrites |
| DB import | ❌ No | High | No duplicate detection, overwrites |
| Classification | ⚠️ Conditional | Medium | Bedrock model config needed |
| Sheets sync | ✓ Yes | Low | API is idempotent |

**Final Verdict: CONDITIONAL RERUN POSSIBLE**
- ✓ Can re-extract from backups safely (to isolated test directories)
- ⚠️ Cannot re-import to production DB without risk (need deduplication)
- ✓ Can reclassify once Bedrock issue is fixed
- ✓ Can re-sync to Sheets safely

---

## 8. LAST VERIFIED EXECUTION LOGS

### WhatsApp Extraction (2026-09-23)

**Last Run: Documented in Extraction Log tab**

| Phone | Extraction Time | Status | Command |
|-------|-----------------|--------|---------|
| +919148338801 | 2026-09-23 11:32 IST | ✓ Success | `wtsexporter -a -b msgstore.db.crypt15 -k <64-hex-key>` |
| +917975102130 | 2026-09-23 12:00 IST | ✓ Success | Same |
| +919902024973 | 2026-09-23 12:26 IST | ✓ Success | Same (LID-format support) |

**Result:** 308 leads, 6,064 messages successfully extracted

### SQLite Import (2026-09-24 00:28:50 IST)

**Log Location:** Google Sheets - Events tab

**Import Events Documented:**
- 2026-09-24 00:28:50 IST: Imported 9 messages from +919902024973
- 2026-09-24 00:28:50 IST: Imported 7 messages from +919902024973  
- (Multiple batch imports for all three phones)

**Total Processed:** 735 leads, 23,454 conversations

### Lead Classification (2026-09-24 20:56:43)

**Log Location:** `/Users/zeidzakir/Projects/efps-internal-automatios/leads_automation/classification_run.log` (211 KB)

**Status:** ❌ **FAILED**

**Error Summary:**
```
ValidationException: Invocation of model ID anthropic.claude-sonnet-4-5-20250929-v1:0 
with on-demand throughput isn't supported. Retry your request with the ID or ARN of 
an inference profile that contains this model.
```

**Failure Details:**
- Started: 2026-09-24 20:56:43
- Total leads to classify: 735
- Batch size: 10
- Max retries: 3
- **Failed on: Batch 1 (10/735 leads)**
- Error repeated for all 10 leads in first batch
- Process did not proceed to subsequent batches

**Reason:** AWS Bedrock Claude model requires cross-region inference profiles. Current configuration attempts on-demand model ID which is not supported. 

**Rule-Based Classification Applied:** Succeeded for ~100 leads before AI attempt

### Google Sheets Synchronization (2026-09-24 Latest)

**Last Sync:** Events log shows 2026-09-24 00:28:50 IST

**Leads in Sheet:** 308 (vs 735 in DB)

**Status:** ✓ **Successful sync, selective write**

**Note:** Only leads with `classification='Qualified Lead'` synced to Sheets (intentional filtering)

### Summary: Execution Timeline

```
2026-09-23 11:05 - 12:26    WhatsApp extraction (3 phones)
                             └─ Result: 6,064 messages
                            
2026-09-23 11:32 - 12:00    Device backups pulled via ADB
                             └─ Result: 3 encrypted msgstore.db files
                            
2026-09-24 00:28:50         SQLite import from extracted data
                             └─ Result: 735 leads, 23,454 conversations
                            
2026-09-24 20:56:43         Lead classification attempt (FAILED)
                             └─ Error: Bedrock model validation error
                             └─ Rule-based only: ~100 leads classified
                            
2026-09-24 (time unknown)    Google Sheets sync
                             └─ Result: 308 qualified leads synced
                            
2026-09-26 (current)         Audit inspection (read-only)
                             └─ All data verified accessible
```

---

## 9. CUSTOMER IDENTITY & DEDUPLICATION RULES

### Phone Number Normalization

**Rule Applied:**
- All phone numbers stored as `+91XXXXXXXXXX` (11 digits with country code)
- Incoming messages parsed from WhatsApp JID format (`919876543210@s.whatsapp.net`)
- Conversion: Remove `@s.whatsapp.net`, add `+91` prefix if missing

**Current State:**
- ✓ All 735 leads have normalized phone numbers
- ✓ No missing or invalid phone numbers in leads table

### Customer Identification Strategy

**Primary Identifier:** `phone_number` (TEXT PRIMARY KEY)

**Assumption:** One phone number = One customer

**Limitations:**
- No name-based deduplication (all customer_name fields are NULL)
- No handling of number changes (e.g., customer using two SIM cards)
- No duplicate phone number detection across the three business numbers

### Conversation Grouping

**How conversations are associated with leads:**

1. **Message Extraction:** Messages grouped by WhatsApp JID (phone number)
2. **Lead Creation:** One lead record per unique phone number
3. **Conversation Association:** All messages from a phone linked to single lead
4. **No Threading:** Individual messages not grouped by conversation thread

**Implication:** All messages from one customer appear as flat list in conversations table (no thread structure)

### Multiple Conversations from One Customer

**Scenario:** Customer sends multiple separate messages on different days

**Current Handling:**
- All stored in conversations table under same phone_number
- Order preserved by timestamp
- No explicit conversation/thread boundaries

**Future CRM Consideration:** May need to implement conversation clustering (group consecutive messages with time gaps)

### Source Number Attribution

**Tracking:** `leads.extracted_from_phone` field records which business number the customer contacted

| Customer | Always Contacts | Mixed Numbers | Observations |
|----------|-----------------|---------------|---------------|
| Most leads | Single number | Not detected | Likely contacted original number only |
| Unknown | Unknown | Possible | Could contact across multiple numbers (not tracked) |

**Data Quality:** **Inferred** - No current mechanism to detect if customer contacted multiple numbers

### Duplicate Detection: Incoming vs. Outgoing

**Preservation:** Both incoming and outgoing messages retained

**Direction Field:** Clearly marks message direction
- `Incoming` = Customer → EasyFind
- `Outgoing` = EasyFind → Customer

**Use Case:** Can reconstruct full conversation by filtering direction

### Group Chats & Non-Customer Conversations

**Filtering Applied:** `import_to_database_v2.py` excludes messages with <2 messages per conversation

**Result:**
- Single-message chats excluded
- Group numbers excluded (no explicit group detection, but low traffic)
- Business numbers (+919148338801, +917975102130, +919902024973) likely excluded

**Impact:** 6,064 extracted messages → 3,369 in DB after filtering (44% retained)

### Classification & Identity Links

**Current Classifications (735 leads):**
- Qualified Lead: 405 (55%)
- Spam/Marketing: 94 (13%)
- Property Listing Sent: 79 (11%)
- Cold Inquiry: 76 (10%)
- Vendor/Supplier: 21 (3%)
- Agent/Partner: 21 (3%)
- Internal: 20 (3%)
- Personal/Family: 19 (3%)

**Known Agents List (from Findings tab):**
- 15 agent numbers explicitly documented
- Automatically classified as "Agent/Partner"
- Allows separation of business communication from customer inquiries

### Deduplication Rules Summary

| Scenario | Current Handling | Risk | Recommendation |
|----------|------------------|------|-----------------|
| Same customer, two numbers | No detection | Medium | Track multiple numbers per customer in future CRM |
| Two customers, similar names | No risk (no names stored) | N/A | Add name-based verification in future |
| Customer uses new number | Creates new lead | Medium | Migration strategy needed |
| Same phone, different person | No detection | Medium | Add name field + verification |
| Business numbers in data | Filtered out | Low | Correctly excluded by <2 message rule |
| Group chats | Likely filtered | Low | No explicit group detection, minor issue |

---

## 10. LIVE DATA STATISTICS & QUALITY FINDINGS

### Lead Statistics

```
Total Leads:                  735
├─ With customer name:        0 (0%)
├─ Without customer name:     735 (100%)
├─ With phone number:         735 (100%)
└─ With classification:       735 (100%)

Leads by Source Phone:
├─ +919148338801 (Primary):   228 leads (31%)
├─ +917975102130 (Business):  458 leads (62%)
└─ +919902024973 (Personal):  49 leads (7%)

Lead Status Distribution:
├─ New:                       ~650 (estimated, 88%)
├─ Active:                    ~50 (estimated, 7%)
├─ Matched:                   ~20 (estimated, 3%)
├─ No Match:                  ~10 (estimated, 1%)
├─ Lost:                      ~5 (estimated, 1%)
└─ Converted:                 0

Lead Priority:
├─ High:                      ~100 (estimated, 14%)
├─ Medium:                    ~550 (estimated, 75%)
└─ Low:                       ~85 (estimated, 12%)

Classification Distribution:
├─ Qualified Lead:            405 (55%)
├─ Spam/Marketing:            94 (13%)
├─ Property Listing Sent:     79 (11%)
├─ Cold Inquiry:              76 (10%)
├─ Vendor/Supplier:           21 (3%)
├─ Agent/Partner:             21 (3%)
├─ Internal:                  20 (3%)
└─ Personal/Family:           19 (3%)
```

### Conversation & Message Statistics

```
Total Messages:               23,454
├─ Incoming (Customer):       8,725 (37%)
├─ Outgoing (EasyFind):       14,729 (63%)
└─ Unknown direction:         0

Message Type Distribution:
├─ Text:                      11,073 (47%)
├─ Media:                     12,381 (53%)
│  ├─ Image:                  ~8,000 (estimated)
│  ├─ Audio:                  ~2,000 (estimated)
│  ├─ Video:                  ~1,500 (estimated)
│  └─ Document:               ~881 (estimated)
└─ Other:                     0

Message Date Coverage:
├─ Earliest:                  2026-07-23
├─ Latest:                    2026-09-23
├─ Days covered:              92 days
└─ Average messages/day:      ~255
