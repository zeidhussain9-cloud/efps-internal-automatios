# EasyFind CRM — UI Design Specification

## Authoritative current verified state — 2026-10-01 21:55 IST

This is the latest repository/production checkpoint. Older dated sections in maintained documents are historical evidence and must not be interpreted as current state.

- **CRM deployment branch:** `crm-ui-dashboard`
- **CRM commit:** `1c196577fc414be52c8fc889b3886f11e0e9da5d`
- **CRM tree:** `908b635b2b7b04bdf3515934de2769393e282c34`
- **main:** `b2fbf366021852aedd4bf0ec66484ad421fb5662`
- **main tree:** `908b635b2b7b04bdf3515934de2769393e282c34`
- **Tree equality:** `tree(main) == tree(crm-ui-dashboard)` = **TRUE**
- **Render:** `easyfind-crm-d01-d05` / `srv-darsv560tbcc73cu4ip0`
- **Live Render deployment:** `dep-dav82h3m8hqs7399j4ug` = **LIVE**
- **Live Render commit:** `1c196577fc414be52c8fc889b3886f11e0e9da5d`
- **Production health:** `GET /health` = HTTP 200, `{"ok":true}`
- **Production WhatsApp source:** `+919148338801`
- **Supabase:** 186 leads; 6,870 messages; 465 webhook events; 310 classifications; 186 requirements; 196 AI runs; 196 drafts; 186 AI cursors; 88 active inventory rows.
- **Classification status:** 186 promoted; 88 classified; 23 pending; 13 excluded = 310 total.
- **Webhook status:** 465 processed; 0 received; 0 processing; 0 failed.
- **Message reconciliation:** 6,870 total = 4,806 lead-linked + 2,064 classified non-lead; unreconciled = 0.
- **Historical classification population:** 228 historical records; 140 qualified mappings.
- **Inventory:** 88 active rows = 71 Available + 17 Rented Out; 1,377 sync runs; latest sync recorded 88 rows / 0 changed / 0 removed; inventory-change rows = 0.
- **Cloudinary:** 829/829 distinct production URLs returned HTTP 200 with `image/*` content-type by direct HEAD checks from the production-machine network path.
- **AI integrity:** draft→AI-run lead mismatch = 0; stale evidence references = 0; invalid cursor lead links = 0.
- **Tests:** `npm run build` PASS; `npm test` 78/78 PASS; `npm run test:browser` 1/1 PASS.
- **Supabase Edge Function:** `whapi-crm-webhook` ACTIVE v8.
- **AWS legacy webhook:** no changes in the audited CRM hardening range.
- **24-item CRM audit:** GREEN / VERIFIED.


## Authoritative current closure — 2026-10-02

Evidence snapshot after final verification:
- crm-ui-dashboard commit: 555bad10e976ee5e810103a66916f461c2da53dc
- crm-ui-dashboard tree: b1b815ebedcdb9d9972da337761e7b805503094c
- main reconciliation commit: 0d979634bf971f93a60414c0a57a37f83b7ba245
- main tree: b1b815ebedcdb9d9972da337761e7b805503094c
- tree(main) == tree(crm-ui-dashboard): TRUE
- Render deployment: dep-davb0teq1p3s73d2kbo0, status LIVE, commit 555bad10e976ee5e810103a66916f461c2da53dc
- Production health: GET /health = HTTP 200, {"ok":true}
- Supabase current snapshot: 186 leads, 6,881 messages, 476 webhook events, 313 classifications, 186 requirement rows, 196 AI runs, 196 drafts, 88 active inventory rows, 71 Available inventory rows, and 1,189 crm_activity events.
- Webhook event counts are 476 total in the current snapshot; detailed processing-state reconciliation is not restated here unless freshly queried.
- Historical message-reconciliation totals from the 2026-10-01 checkpoint are retained in dated audit records; they were not re-run as part of this UI-only closure.
- Historical classification totals from the 2026-10-01 checkpoint are retained in dated audit records; they were not re-run as part of this UI-only closure.
- Requirements: 186/186 lead rows have requirement rows; orphan/missing = 0
- AI/drafts: 196 AI runs and 196 drafts exist in the current snapshot; the earlier verified mapping/evidence/cursor checks remain dated audit evidence.
- Inventory: 88 active rows; 71 Available; 17 Rented Out.
- Cloudinary: 829 distinct production URLs were identified in the earlier audit; external probing encountered timeouts, so 829/829 reachability is not claimed. The UI now fails closed to a media fallback for unreachable/non-Cloudinary URLs.
- Tests: npm run build PASS; npm test 79/79 PASS; npm run test:browser 1/1 PASS; git diff --check PASS.
- Supabase Edge Function whapi-crm-webhook deployment version was not re-verified during this UI checkpoint.
- Legacy AWS webhook/handler files: no changes in the CRM hardening commit range
- AI usage metadata: 192/196 current AI runs have complete input/output/total token metadata; 4 historical runs have no usage metadata and are not fabricated.
- 18-point Lead Workspace/UI/audit hardening scope: implemented, locally tested, deployed, production health verified, and reconciled into main.

Historical dated checkpoints below remain historical evidence; this block is the current source of truth.


**Status:** D01–D07 approved/resolved; D08 unresolved  
**Canonical repository:** `zeidhussain9-cloud/efps-internal-automatios`  
**Working branch:** `crm-ui-dashboard`  
**Figma:** https://www.figma.com/design/PBiMGsVQ0fVpSf39WwNmKb  
**Canva visual reference:** https://canva.link/qmph6ij1o6lue57  
**Data contract:** `CRM_DATA_MODEL.md`

## Current UI implementation checkpoint — 2026-10-01

The production Leads Inbox card shows **Lead status** and **Source number** beneath the lead identity, followed by the operational conversation summary: **Contacted date**, **Last message sent by**, and **Last message date**. Priority and classification chips are not shown on the inbox card.

The Leads Inbox header provides one clickable summary block for every supported lead status (`New`, `Active Follow-up`, `Waiting on Customer`, `Waiting on Us`, `Nurture`, `Dormant`, `Converted`, `Lost`, `On Hold`, `Out of Coverage Area`). Each block shows the live count for the selected source and applies the corresponding server-side filter when clicked. Lead-status edits in Lead Workspace persist to `crm_leads.lead_type`; the inbox reloads from the database so the lead moves to its new status grouping.

The AI Draft workspace displays provider/model provenance plus input tokens, output tokens, and estimated cost when the provider/model has a configured public rate. Complete chronological conversation context remains the AI source of truth.

## 1. Product shell

Main navigation:
1. Dashboard
2. Leads Inbox
3. Follow-ups
4. Inventory
5. Activity
6. Settings

Selecting a lead opens:
1. Overview
2. Conversation
3. Requirements
4. Property Matches
5. AI & Drafts
6. Activity & History

## 2. Global controls

Top bar:
- Global Search
- EFPS source selector
- Data freshness/refresh state
- Account/logout control

Page filters use compact controls rather than a permanent sidebar.

## 3. Inbox

Primary queue: Qualified Leads.

Review Queue: Cold/uncertain inquiries and items requiring qualification review.

Archive: retained non-primary classifications and excluded records from the local source dataset.

## 4. Lead row

Display:
- Customer name when verified; phone fallback
- Phone
- BHK + preferred location
- Budget max when known
- Status
- Priority
- EFPS source badge(s)
- Last interaction
- New activity / Needs Analysis state

Search and filtering are deterministic; no AI is invoked for them.

## 5. Lead workspace

### Overview
Identity, source number(s), workflow status, priority, current requirements, latest activity, next action and compact match/draft summaries.

### Conversation
Chronological stored messages with direction, timestamp, sender, source number, message type/media indicator and history coverage state.

AI drafts are never inserted into the observed conversation timeline.

### Requirements
BHK, preferred locations, budget min/max, furnishing, occupancy/tenant type, move-in date, pet preference, parking, current requirement summary and notes.

Unknown/unconfirmed values are explicit.

### AI & Drafts
Previous AI runs, saved intelligence, new/unanalysed message state, proposed changes, evidence, versioned drafts and explicit actions.

### Property Matches — D05 APPROVED
Global inventory plus contextual matches. Matches use verified inventory fields and deterministic criteria. Each candidate exposes matched, failed and Unknown conditions where relevant. Manual pin/exclude/override requires a reason. Inventory freshness is visible.

### Activity & History
Chronological audit/activity stream across human edits, classification, follow-ups, AI, drafts and property interactions.

## 6. Inventory UI contract

Use the canonical Housing Listings field definitions.

Property cards prioritize:
- Listing ID
- Locality
- BHK
- Rent
- Maintenance/inclusion
- Furnishing
- Tenant eligibility
- Pet state
- Parking
- Listing state/availability
- Verified highlights
- Media availability
- Freshness

D05 does not authorize live inventory connection.

## 7. Reliability states

The UI distinguishes:
- Loading
- Empty
- Error
- Stale
- Processing
- Partial
- Failed
- Retryable
- Awaiting human action

No silent failure.

## 8. Provenance

Every value is conceptually:
- Verified source
- Human-edited
- AI-derived
- System
- Synthetic/illustrative

Prototype fixtures are synthetic only.

## 9. Mobile

Flow:
`Inbox → Lead Workspace → tabbed section`

Primary context actions:
- WhatsApp
- Generate AI Reply
- Follow-up
- Save

Avoid an endless single-page lead workspace.

## 10. Data boundary

D01–D05 prototype:
- no live customer records
- no live inventory records
- no live WhatsApp send
- no destructive Sheets sync
- no production database writes

## 11. Figma handoff

Figma defines editable visual composition. This specification defines behavior/data meaning. Neither may invent fields or silently change business rules.

## AI pilot implementation checkpoint — 2026-09-27

The deployed on-demand `AI & Drafts` control is production source-backed. It analyzes the selected lead's complete chronological CRM conversation, normalized requirements, requirement evidence, operator notes, prior AI runs and per-lead cursor. The hosted provider chain is Bedrock primary with Ollama fallback, and `steering.md` supplies the dedicated model instructions. Human review/Accept/Reject remains required; AI-suggested lead status is not automatically applied and WhatsApp sending remains manual. Earlier fictional-fixture behavior is retained only in the dated prototype history.

## 8. Contact Classification — production simplification — 2026-09-30

Contact Classification is a pre-lead queue, not another lead-management dashboard.

The screen has exactly two sub-tabs:

1. Waiting for classification — pending and non-qualified contacts.
2. Total active inventory to CRM — promoted contacts.

Each row has one classification dropdown and one explicit Update button. Selecting a value does not persist it until Update is pressed and the server confirms the transaction.

- Non-qualified classifications remain in Waiting for classification.
- Qualified Lead creates/links the CRM lead, links preserved messages, and moves the contact to the qualified tab after the transaction commits.
- Failed writes stay on the same row and display the returned error.
- No additional classification filter is shown.

The dashboard then surfaces the next operational work: classification counts and open follow-ups.


## Current Contact Classification workflow — 2026-09-30

The production UI intentionally uses one simple Contact Classification screen with two tabs:

1. **Waiting for classification** — pending and non-qualified contacts.
2. **Total active inventory to CRM** — successfully promoted contacts.

Each contact row shows the phone number, a direct **Open WhatsApp** link, a classification selector and an explicit **Update** button. The button is disabled until the selected classification differs from the stored value. A successful non-qualified update keeps the contact outside CRM. A successful Qualified Lead update creates/links the CRM lead and preserved messages transactionally, then the UI moves the contact to the promoted tab. A failed write stays in place and displays the server error instead of silently moving the contact.

The Dashboard surfaces the classification counts and today's follow-ups so the operator can use the CRM as a daily work queue without a separate intake workflow.


## 2026-10-01 — D07 production operator-control specification

The application now uses a private operator session after verification of the configured CRM credential. The session token is opaque, HttpOnly and SameSite=Lax; sessions expire after 8 hours of inactivity or 12 hours maximum, and explicit logout revokes the session. Non-GET/HEAD cross-origin requests are rejected, and sign-in/sign-out use same-origin checks.

Privacy mode masks phone numbers and observed message bodies by default; opening WhatsApp from a lead requires an explicit reveal. Lead archive is a confirmed, reversible soft action with a preserved prior status in the audit record. Global security/operator events are visible in Activity, while lead-specific changes remain in Lead Workspace Activity & History.

CSV export is explicit, source-scoped and audit-recorded. Automatic retention deletion is disabled and permanent deletion is not exposed in v1. Offline status is visible and write/export controls are disabled until connectivity returns.


## 2026-10-01 — mobile and browser Realtime closure

The production CRM shell is responsive for narrow mobile and compact/tablet layout viewports. At compact widths the sidebar becomes a horizontal navigation rail, the top operator/status controls become horizontally scrollable, dashboard KPIs use a two-column layout, lead lists become full-width, and lead-workspace sections collapse to one column where appropriate. The CSS includes a 1000px compact-layout breakpoint so mobile browsers exposing a wider desktop-style layout viewport do not retain the desktop two-pane shell.

Browser Realtime is initialized after successful operator authentication rather than only at initial application mount. When the configured Supabase project URL and publishable browser key are present, the crm:live broadcast channel reports connecting then live; the channel is notification-only and refreshes CRM reads after the database trigger broadcasts message_inserted. Missing browser configuration is explicitly reported as unconfigured rather than being treated as a live connection.

## 2026-10-01 — Leads Inbox usability: conversation timeline and sorting

The Leads Inbox now exposes conversation-derived operational fields for every returned lead:
- Contacted date — timestamp of the first stored Incoming/customer message.
- Last message sent by — Customer or Us, based on the direction of the latest stored CRM message.
- Last message date — timestamp of the latest stored CRM message.

Date/time display uses DD-Month-YYYY / HH:MM in the Asia/Kolkata timezone. Values are computed from crm_messages server-side; no placeholder values are generated.

Inbox sorting is server-side so sorting remains correct across pagination. Available views are:
1. Last message — newest (default)
2. Customer replied — newest
3. First contacted — newest
4. Last message — oldest
5. Name — A–Z

The same lead card is used by Dashboard and Leads Inbox, so these conversation fields remain visible in both surfaces.

## 2026-10-01 — Service-area status

The Lead Status control now includes the compact operational status **OOC**, stored as `Out of Coverage Area`.

Service areas currently defined by the operator are: HSR Layout, Kudlu Gate, Bellandur, Sarjapur Road, Whitefield, Hoodi, Mahadevapura, Marathahalli, ITPL, Varthur, Kasavanahalli, Harlur, Panathur, Koramangala (limited), Yemalur, Bommanahalli (selective), and Old Airport Road (selective).

OOC is a Layer-2 CRM lead status, not a Contact Classification result. It does not remove the lead or suppress its conversation history. Automatic geographic assignment is intentionally not inferred from free-text locality; a deterministic coverage rule must be separately approved before automation.


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
- Live Supabase verification after schema deployment: 186 requirement profiles, 186 per-lead AI cursors, 6,622 CRM messages (4,228 outgoing), 195 webhook events (195 processed, 0 failed). That sentence records the earlier zero-state checkpoint; current drafts are durable, selectable after reload, and display their AI provider/model provenance.

## 2026-10-01 — Production AI workspace

The Requirements tab is now a normalized editable table backed by `crm_lead_requirements`. Fixed fields are BHK, budget, preferred locations, tenant type, move-in date, pets, veg/non-veg, furnishing, parking, property type, bathrooms, occupancy count, lease term, preferred floor, preferred amenities and notes. The profile retains `lead_id`, timestamps and `updated_by` for relational/audit linkage.

The AI & Drafts tab is a per-lead operational workspace containing saved AI run history, evidence-backed requirement proposals, requirement accept/reject workflow, suggested lead status, complete-history timeline analysis, versioned reply drafts and draft history. The AI is supplied the full chronological CRM conversation and relevant lead context. It may propose requirement changes and a reply; it cannot autonomously send WhatsApp messages or silently change lead status.

## 2026-10-01 — Draft workspace correction

The AI & Drafts tab now treats saved drafts as durable workspace state rather than transient AI-result state. Selecting a version loads its body into a persistent editor even after page reload. Each version displays provider and exact model identifier, and saved edits retain the selected draft's provenance.

## 2026-10-01 — AI workspace hardening

The AI & Drafts workspace now shows provider/model/fallback provenance, source message IDs, stale status, and a pre-send grounding check. Opening WhatsApp requires the deterministic check to pass; the operator can copy a draft and explicitly mark it sent after manual WhatsApp delivery. New CRM activity after draft generation marks the draft stale so it is not silently reused.

## 2026-10-01 — Final implementation verification

The UI implementation corresponding to this specification is production-live on crm-ui-dashboard. The final hardening release has passed build, 78/78 automated tests, and 1/1 browser regression. Search/pagination, inventory sorting and KPI filtering, draft/follow-up actions, error/empty states, Cloudinary fallback handling, and lead-workspace lifecycle controls are covered by the verified release. Production webhook reconciliation and AI persistence are live against real Supabase data. All 24 CRM audit items are GREEN.

## 2026-10-02 — Lead Workspace and audit-history closure

- Lead Workspace no longer displays the redundant “Actual lead” badge or the one-time bulk-import Priority · Medium chip.
- `crm_leads.priority` remains a stored compatibility field, but it is intentionally not rendered in the operator UI.
- Requirements are rendered as a structured normalized table. Database-defined enum fields use controlled dropdowns; BHK and preferred-location fields provide current inventory values as datalist suggestions while preserving custom-value entry.
- Conversation property boundaries are evidence-based. A stored supported property URL creates a property-reference section; only messages explicitly replying to that source-message ID are grouped into it. Other messages remain in General conversation rather than being inferred into a property.
- Dashboard inventory KPI is Total available inventory, sourced from crm_inventory_snapshot rows with listing_state='Available' and deleted_at IS NULL.
- Global Activity is CRM-wide and reads all crm_activity events, including lead-scoped events. Lead Workspace Activity & History reads the same event table with lead_id scoping. Both support date ranges and pagination.

- Audit rows display a presentation-only event category derived from the persisted action so operators can distinguish Lead, Message, Classification, Requirements, AI, Follow-up, Inventory, Webhook and System/Operator activity without changing stored event semantics.

- Leads Inbox cards use separated vertical rhythm, consistent borders/radius/elevation, and an identity row with deliberate name-to-phone spacing on mobile and desktop.
- The one-time bulk-import `crm_leads.priority` value is not rendered in the Lead Workspace UI.
- Global and lead-scoped audit history use the same labelled Date range dropdown and Custom range behavior for consistent production interaction.
