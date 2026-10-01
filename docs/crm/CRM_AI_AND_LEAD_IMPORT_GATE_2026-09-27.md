## Superseded by production checkpoint — 2026-09-30

The synthetic-only/live-data gate described below is historical. The current CRM production source is `+919148338801`; real source-scoped CRM data is active in Supabase, and the operator-gated classification/promotion flow is live. The two additional source numbers remain visible but inactive for production ingestion.

# AI and historical lead import gate — 2026-09-27

## Verified implementation
- Render CRM deployment `7ed3bee` recovered from an inventory SQL JavaScript escaping error and was confirmed live. Synthetic AI was explicitly enabled through the server-side Render setting. This is **not** evidence that the remote Ollama model responded successfully.
- Local integration test exercises the actual authenticated `/api/ai/analyze` HTTP route with a local Ollama-compatible test provider: unauthenticated access returns 401, a non-fictional ID returns 422 without calling the provider, and fictional `L-1001` returns a structured proposal. The provider key is passed server-side only. This is a **mock-provider** integration test, not a real remote Ollama request.
- Full application tests: 58/58 passed; production build and Chromium browser journey passed after rebuilding the local bundle. Commit `83ccdb4` on `crm-ui-dashboard` only. Check the current GitHub Actions run before treating CI as complete.

## Read-only source SQLite audit
- Original source file: `leads_automation/leads.db`, opened with SQLite `mode=ro`; no data was changed or exported.
- 735 leads with 735 distinct nonblank phone keys; 23,454 conversations with 23,454 distinct nonblank message IDs; 966 lifecycle events.
- 0 conversation rows or lifecycle events refer to a phone missing from the lead table. Source extraction grouping has 458, 228 and 49 lead rows respectively (source identifiers deliberately omitted here).
- Separate `leads_automation/crm.db` has zero rows in its leads, interactions and inventory tables; it is **not** the canonical historical source.
- Existing curated extraction (308 leads / 6,064 messages) remains unreconciled against the larger historical SQLite. The source schema lacks an explicit conversation source_number column, so deduplication must map message provenance from the audited extraction rather than infer it from customer phone.
- Supabase at this checkpoint has 3 test leads, 0 messages, 81 active inventory rows and 4 inventory sync runs. Do not merge historical customer data with test records without isolation, backup/restore evidence, provenance reconciliation and authorization.

## Remaining sequential gates
1. Verify actual remote Ollama response through the authenticated Render route using only fictional ID L-1001; check model identity, structured extraction, timeout and error handling. Never submit real conversations during this pilot.
2. Independently verify encrypted Supabase backup and restore to an isolated target, then reconcile 735/23,454/966 against the curated 308/6,064 source by stable IDs and source attribution. Prepare a read-only dry-run manifest with zero PII in logs.
3. Review production authentication, access scopes, retention and operator override; approve D06–D08. Only then authorize a controlled, audited real-data import. Keep `CRM_DB_WRITE_ENABLED` and `CRM_REAL_DATA_ENABLED` disabled until gates pass.
4. Confirm the latest live Render deployment, GitHub Actions result and browser journey after each change. `main` must never be modified.

## Superseding hosted-AI and steering verification — 2026-09-27

- [x] Hosted Ollama Cloud `gpt-oss:20b` returned a successful fictional `L-1001` proposal from Render at 2026-09-26 21:25:38 UTC; the provider returned `bhk`, `location`, `budget`, `pets` and `uncertainties`. The corrected adapter accepts JSON and fenced JSON. This supersedes the earlier unverified-provider statement above.
- [x] Dedicated root `steering.md` is the **only** CRM model system instruction. `src/ollama-adapter.mjs` reads and caches it server-side, limits it to 2 KiB and sends it with one fictional fixture per on-demand invocation; it does not send `CORE_STEERING.md` or the full business-context document.
- [x] Steering tests verify company, business, role, JSON contract, size and single-request behavior; full suite/build/browser must pass on the new commit and Render must independently verify the deployed change.
- [x] Live Render deployment `49b4f30` loaded the dedicated steering and successfully called hosted `gpt-oss:20b` at 2026-09-26 21:36:16 UTC, returning all five expected keys. [x] Render `CRM_OLLAMA_STARTUP_SMOKE_ENABLED=false` was applied; config deploy `dep-das3lspa4omc738mqre0` reached live at 2026-09-26 21:37:57 UTC. Startup logs show a successful Supabase connection and no model smoke invocation; on-demand fictional analysis remains enabled.
- [ ] Complete representative fictional fixture evaluation, error/retry/timeout validation and operator review; a single successful response does not establish production accuracy.
- [ ] Independent encrypted backup/isolated restore, source-provenance reconciliation and D06–D08 approval remain **blocked**. No real lead import or automatic WhatsApp send.


## Historical gate status superseded — 2026-09-30\nThe dated import gate above describes the pre-reconciliation state. The current CRM source +919148338801 is already reconciled in Supabase. The present operator write surface is the audited contact-classification promotion flow; broader real-data write gates remain separate.\n

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
- Live Supabase verification after schema deployment: 186 requirement profiles, 186 per-lead AI cursors, 6,622 CRM messages (4,228 outgoing), 195 webhook events (195 processed, 0 failed). AI runs/drafts/evidence remain 0 until an operator first runs production AI and accepts/creates outputs.
