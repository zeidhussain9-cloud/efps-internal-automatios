# EasyFind CRM — UI Design Specification

**Status:** D01–D05 approved; D06–D08 unresolved  
**Canonical repository:** `zeidhussain9-cloud/efps-internal-automatios`  
**Working branch:** `crm-ui-dashboard`  
**Figma:** https://www.figma.com/design/PBiMGsVQ0fVpSf39WwNmKb  
**Canva visual reference:** https://canva.link/qmph6ij1o6lue57  
**Data contract:** `CRM_DATA_MODEL.md`

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
