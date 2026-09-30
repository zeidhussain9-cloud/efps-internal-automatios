## Superseded by current production checkpoint — 2026-09-30

This 2026-09-26 audit is retained as historical evidence. Its synthetic-only baseline and instruction to leave `main` untouched no longer describe the current CRM state. Current production runs from `crm-ui-dashboard`; `main` is repository-reconciled but is not the Render deployment branch. Real source-scoped CRM data is active for `+919148338801`. Contact classification, webhook ingress, Supabase persistence, and the operator-gated promotion flow are implemented and deployed.

# CRM stabilization audit — 2026-09-26

# CRM stabilization audit — 2026-09-26

## Scope and verified baseline
- Historical checkpoint statement: canonical branch was `crm-ui-dashboard` and `main` was then treated as untouched. The current repository is reconciled across both branches; Render remains on `crm-ui-dashboard`.
- Render service: `easyfind-crm-d01-d05`; latest checked deployment `d802eee0f3145ca03621ad6a8e98477fb59623c8` was live.
- User approved the visual prototype and requested the next cleanup, hardening and synthetic Ollama pilot.
- Current React entry point `src/main.jsx` contains UI, synthetic records, matching and action handlers in one component. Styles are concentrated in `src/style.css`.
- Existing demo data is illustrative hand-authored material, **not yet derived from the audited local extraction**.

## Confirmed gaps against approved D01–D05
- D01: initial page is Leads Inbox rather than approved Dashboard; global search, refresh/freshness and account controls incomplete.
- D02: limited filters, no stable source-backed activity sorting, no duplicate merge/review workflow.
- D03: only some requirement fields editable; no durable follow-ups or reversible merge/split.
- D04: provider unavailable placeholder; no saved intelligence, proposals, evidence, idempotent retries or draft versions.
- D05: synthetic property records lack actual images, maintenance and many verified schema fields; pin/exclude state is not scoped per lead; no durable property interaction history.
- Activity and Settings currently have only session activity and placeholder configuration.
- No authentication or durable test database. The Render URL is public: **do not connect real customer data**.
- Current demo copies drafts into an external WhatsApp composer; opening/copying does not confirm sending.
- No automated UI or model evaluation tests existed at the start of this audit.

## Cleanup safety
Do not delete legacy internal-automation code or docs merely because they are not part of the CRM. Identify ownership, references and usage before removing files. Preserve source evidence and historical audits. Keep live credentials out of the frontend and repository.

## Implementation sequence
1. Refactor React into tested components, data adapters and scoped per-lead state while preserving the approved visual design.
2. Complete D01–D05 interactions and explicit empty/loading/stale/error states.
3. Add synthetic-only persistence, validation, security controls, tests and a deployment health check.
4. Inspect the **actual local** audited extraction with the user's authorized computer access; derive distributions/patterns without copying identities or verbatim sensitive text to Render.
5. Generate fictional customer/message/property fixtures with provenance, known expected extraction results and photo placeholders. Inventory media later comes from verified `cloudinary_image_urls` or approved property media.
6. Connect Ollama through an authenticated backend/proxy only. Never expose Mac Ollama directly or browser-side secrets.
7. Run full synthetic workflow and regression evaluation; review D06–D08 privacy/operational decisions before live migration.

## Completion gate
Do not call this stage finished until code tests, end-to-end browser tests, deployment checks, privacy checks and the synthetic model pilot are independently verified.

## Superseding checkpoint — 2026-09-27

The initial provider-unavailable and unauthenticated states above are historical. Render authenticated hosted Ollama `gpt-oss:20b` and received a five-key fictional response at 2026-09-26 21:25:38 UTC. The CRM adapter now reads dedicated compact root `steering.md`; model input remains fictional-only and operator-reviewed. Durable production workflows, full synthetic evaluation, isolated restore and D06–D08 remain open.
