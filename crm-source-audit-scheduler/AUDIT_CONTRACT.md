# Scheduler Reconcile Audit — Canonical Contract

This file is the single repository source for the logic and evidence contract used by the Scheduler Reconcile Audit. The scheduled runner, source-audit snapshot and tests must consume or validate these rules here/through the shared implementation rather than creating parallel definitions.

## 1. Ownership

- Code: `src/crm-requirement-match-audit.mjs`
- Snapshot integration: `src/crm-source-audit.mjs`
- Scheduled gate: `crm-source-audit-scheduler/runner.mjs`
- Tests: `tests/source-audit-mcp.test.mjs` and `crm-source-audit-scheduler/runner.test.mjs`
- Operational checklist: `crm-source-audit-scheduler/CHECKLIST.md`
- Operations: `crm-source-audit-scheduler/OPERATIONS.md`

The audit is read-only. It never writes CRM, inventory, Sheet, WhAPI, classification, AI or deployment state.

## 2. Point 40 — Requirement field correctness

Population is the live set of contacts whose classification is `qualified_lead` and whose classification status is `promoted`.

For each qualified lead:

1. Read the authoritative legacy `crm_leads.requirements` JSON and `crm_leads.tenant_type`.
2. Project it through the same normalization contract used by the normalized requirement migration:
   - BHK
   - budget
   - preferred locations
   - tenant type
   - move-in date
   - pets
   - veg/non-veg
   - furnishing
   - parking
   - property type
   - bathrooms
   - occupancy count
   - lease term
   - preferred floor
   - preferred amenities
   - notes
3. Compare every projected field against `crm_lead_requirements`.
4. Reject invalid enum/numeric states instead of silently coercing them.
5. Point 40 is green only when every qualified lead has a profile, every checked field matches the authoritative projection, and every profile satisfies its database-compatible validation rules.

No requirement evidence is fabricated. Requirement evidence is a separate provenance layer.

## 3. Point 41 — Property-matching inputs

The canonical matcher inputs are derived only from the normalized requirement profile:

- BHK → normalized BHK tokens.
- Budget → non-negative numeric ceiling; unknown remains unknown and is never treated as zero.
- Preferred locations → normalized location tokens.
- Furnishing → supported normalized furnishing values.
- Pets → supported Yes/No values.
- Other requirement fields remain available to the audit as profile data but are not silently invented as matcher predicates.

Point 41 is green only when every qualified lead has valid, deterministic matcher inputs derived from the stored profile and the input validation contract accepts them.

## 4. Point 42 — Property-matching results

Results are evaluated against the same matcher contract used by the production inventory query:

- inventory source is the canonical housing-sheet snapshot;
- only non-deleted `Available` inventory is eligible;
- BHK, budget, locality, furnishing and pet predicates use the normalized inputs;
- results are deterministic and ordered by rent then listing ID;
- no result may violate the inputs that generated it.

Point 42 is green when every audited qualified lead has a valid result set under the same deterministic predicates. Zero matches is valid evidence and is not itself a failure.

## 5. Green gate

Points 40, 41 and 42 are green together only when:

`requirementMatchAudit.complete === true`

That means:

- zero missing requirement profiles;
- zero field mismatches;
- zero invalid requirement profiles;
- zero invalid matcher inputs;
- zero invalid returned result sets.

The scheduler must fail closed if this gate is not green.

## 6. Evidence produced per run

The source-audit payload exposes `crm.requirementMatchAudit` with:

- population: qualified leads, profiles present, profiles missing;
- field correctness: checked profiles, exact projection matches, mismatched leads, invalid profiles;
- matching inputs: checked profiles, valid/invalid inputs;
- matching results: checked leads, total matches, zero-match leads, invalid result sets;
- `complete`: definitive gate.

## 7. Documentation rule

When any audit pointer becomes green, update the repository-wide current-state documentation in the same change. Dated audit evidence may remain historical, but current-state claims must point back to this contract and the latest verified scheduler run.

Do not duplicate the matching algorithm in other documents. Link/reference this contract instead.

## 8. Current live verification baseline

Verified from production Supabase during the 2026-10-05 reconciliation:

- qualified promoted classifications: 253
- normalized requirement profiles: 253
- missing profiles: 0
- requirement evidence rows: present as a separate table; this audit does not fabricate or require evidence rows for Point 40
- active housing-sheet inventory: 71

The repository test suite passed 130/130 after the audit implementation.

Production green status requires the scheduled runner to execute this contract against the deployed code; local tests alone are not sufficient to claim the scheduled production run is green.
