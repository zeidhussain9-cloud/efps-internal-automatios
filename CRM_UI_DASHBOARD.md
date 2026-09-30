# EasyFind CRM UI Dashboard — Single Working Home

**Canonical working branch: `crm-ui-dashboard`.** Render, GitHub, and the local CRM UI checkout are aligned to this branch for the current production dashboard.

## Canonical location

**Repository:** https://github.com/zeidhussain9-cloud/efps-internal-automatios  
**Branch:** `crm-ui-dashboard`

`main` remains outside the CRM UI deployment path. CRM UI production work is maintained on `crm-ui-dashboard`.

## Source of truth

**Leads:** `docs/audits/LEADS_EXTRACTION_SOURCE_OF_TRUTH_AUDIT.md` + the local SQLite dataset produced by that extraction.

**Inventory:** the verified Housing Listings contract/audit used to define D05. Live inventory integration comes later.

**Design:** Figma — https://www.figma.com/design/PBiMGsVQ0fVpSf39WwNmKb

**Visual reference:** Canva — https://canva.link/qmph6ij1o6lue57

## Approved state

**D01–D05: APPROVED**

D06–D08 remain unresolved and are not to be implemented by assumption.

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
