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

D06 and D07 are resolved in the production CRM path. D08 remains the final unresolved design/handoff stage. D08 is a design/handoff item, not a production-data gate.

## Current rule

Do not use the historical CRM branches as the working location. All future UI dashboard work belongs on `crm-ui-dashboard`.

## Current production workflow — 2026-10-01

Verified current source: `+919148338801`; Supabase has 186 source-linked leads, 289 classifications, 2 pending classifications, 6,621 messages and 73 webhook events, all processed. OOC (`Out of Coverage Area`) is an available Layer-2 lead status. Automatic geographic OOC assignment is not enabled pending a deterministic coverage rule.


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

## 2026-10-01 — Leads Inbox operational columns

Lead rows/cards now show Contacted date, Last message sent by, and Last message date using the stored CRM conversation timeline. Contacted date is the first Incoming message timestamp; Last message date is the latest message timestamp; Last message sent by is derived from the latest message direction.

The Inbox provides server-side sorting for Last message newest, Customer replied newest, First contacted newest, Last message oldest, and Name A–Z. Sorting occurs before pagination so the operator is not limited to the currently loaded page.

All current source-linked production leads have at least one stored customer message at the 2026-10-01 verification checkpoint; no fixture/default timestamp is used for the new fields.

## 2026-10-01 — Out-of-coverage lead status

Lead Workspace and Lead Inbox support the compact status **OOC** (`Out of Coverage Area`) for leads requesting properties outside the approved service area.

Defined coverage currently includes HSR Layout, Kudlu Gate, Bellandur, Sarjapur Road, Whitefield, Hoodi, Mahadevapura, Marathahalli, ITPL, Varthur, Kasavanahalli, Harlur, Panathur, Koramangala (limited), Yemalur, Bommanahalli (selective), and Old Airport Road (selective).

The status is stored in `crm_leads.lead_type`. The current implementation does not automatically adjudicate free-text locations; that requires a separately verified geographic rule because some listed areas are selective.

## 2026-10-01 — Current live checkpoint
Production: easyfind-crm-d01-d05 (srv-darsv560tbcc73cu4ip0). The current deployment commit is recorded in the final checkpoint below. Bedrock Claude Opus 4.6 (au.anthropic.claude-opus-4-6-v1) is primary; Ollama gpt-oss:20b is fallback. Render startup verified Bedrock configuration presence and Supabase connectivity.

## 2026-10-01 — Current AI generation state

AI provider chain: Bedrock Claude Opus 4.6 (`au.anthropic.claude-opus-4-6-v1`) → Bedrock Claude Sonnet 4.6 (`au.anthropic.claude-sonnet-4-6`) → Ollama `gpt-oss:20b`. Drafts display provider/model/fallback provenance and source-message evidence. Stale drafts are flagged, and the operator must pass a deterministic pre-send check before opening WhatsApp. Sending remains manual; `Mark sent` is an explicit operator audit action. Incremental message analysis remains deferred.

## Final verified checkpoint — 2026-10-01

`crm-ui-dashboard` commit `c19e36c74a06eb7a5204e2f201a99916545b52b0`, tree `2dbd2258f655e7de599917c9e339f07d74c0e0b0`. Render deployment `dep-dautfd3ncjis73cu6dj0` is live. `main` has been reconciled to the same tree in commit `562905cfe435ee7ad8851c9c4a42360726a9b317`. Build passes and the automated test suite is 66/66. Browser test runner remains hanging locally and is not claimed as passed.
