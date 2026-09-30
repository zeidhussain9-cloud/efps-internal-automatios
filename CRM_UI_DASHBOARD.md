# EasyFind CRM UI Dashboard — Single Working Home

**Canonical working branch: `crm-ui-dashboard`.** Render, GitHub, and the local CRM UI checkout are aligned to this branch for the current production dashboard.

## Canonical location

**Repository:** https://github.com/zeidhussain9-cloud/efps-internal-automatios  
**Branch:** `crm-ui-dashboard`

`main` is the repository reconciliation branch; Render production remains deployed from `crm-ui-dashboard`. CRM UI implementation work is maintained on `crm-ui-dashboard`, and `main` is reconciled to the same production code/docs checkpoint after each approved release.

## Source of truth

**Leads:** `docs/audits/LEADS_EXTRACTION_SOURCE_OF_TRUTH_AUDIT.md` + the local SQLite dataset produced by that extraction.

**Inventory:** the verified Housing Listings contract/audit used to define D05. Live inventory integration comes later.

**Design:** Figma — https://www.figma.com/design/PBiMGsVQ0fVpSf39WwNmKb

**Visual reference:** Canva — https://canva.link/qmph6ij1o6lue57

## Approved state

**D01–D05: APPROVED**

D06 and D07 are resolved in the production CRM path. D08 remains the final unresolved design/handoff stage and requires an explicit design update before implementation.

## Current rule

Do not use the historical CRM branches as the working location. All future UI dashboard work belongs on `crm-ui-dashboard`.

## Current production workflow — 2026-09-30

### Contact Classification

The production UI uses one simple qualification section with two sub-tabs:

- Not pushed to CRM: pending and non-qualified contacts.
- Qualified leads pushed to CRM: promoted contacts.

The operator workflow is intentionally one action at a time:

Choose classification → Update → database confirms → queue refresh

Non-qualified classifications remain outside CRM. Qualified Lead is the only classification that creates/links a CRM lead and links preserved messages. The browser never treats a selected value as saved until the server confirms the database transaction.

### Dashboard

The dashboard presents only the daily operational counters and next actions: CRM leads, contacts not pushed, qualified contacts pushed, and follow-ups due today. Open follow-ups are listed below the counters and open directly into the relevant lead workspace.

### Reliability

Classification errors are rendered inline with the server response instead of silently changing the queue. The write endpoint is protected and gated by CRM_CLASSIFICATION_WRITE_ENABLED=true.


## 2026-10-01 — Production security/operator-control closure

D07 is implemented on `crm-ui-dashboard`: protected operator session UX, default sensitive-data masking, explicit/reversible lead archive, global audit visibility, explicit audit-recorded CSV export, retention/deletion boundaries, and visible offline/sync states. The browser E2E regression is corrected on the same branch.


## 2026-10-01 — mobile responsiveness and Realtime

The live CRM UI now has an explicit compact/mobile shell through the 1000px breakpoint, including full-width navigation, stacked header/status controls, two-column KPI cards, full-width lead rows and single-column lead workspace content. A browser regression assertion covers a 900px compact viewport so the desktop layout cannot silently regress into the mobile browser experience.

The Supabase browser Realtime client is configured from server-side Render build variables VITE_SUPABASE_URL and VITE_SUPABASE_PUBLISHABLE_KEY and is initialized after operator sign-in. The channel is notification-only; CRM data remains read from the protected server API. Realtime: live therefore means the browser subscription is active, not that the webhook itself is the source of truth.
