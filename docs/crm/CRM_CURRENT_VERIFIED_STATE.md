# EFPS CRM — Current Verified Production State

> **Authoritative snapshot:** 2026-10-03 18:04 IST (12:34 UTC). This page contains the current operational state only. Older evidence belongs in dated audit documents and must not be read as current status.

## Repository and deployment

- Production branch: `crm-ui-dashboard`
- Current implementation commit: `e375c1f811e962e140caba2c964fb05cd94ab02a`
- Current tree: `7f9527ae9c26850f93d13d389f94b2b45b87447a`
- Render service: `srv-darsv560tbcc73cu4ip0`
- Production URL: https://easyfind-crm-d01-d05.onrender.com
- Production source: `+919148338801`
- Supabase project: `qttcutwzehtskfcwxkwj`

The repository requirement `tree(main) == tree(crm-ui-dashboard)` must be re-verified after every release. This release has not yet been reconciled into `main`; reconciliation is performed only after production deployment and runtime verification.

## Live data snapshot

- Leads: **186**
- CRM messages: **7573**
- Persisted webhook events: **1256**
- AI runs: **214**
- AI drafts: **214**
- Active inventory listings: **88**
- Inventory sync runs: **1905**

## Production safeguards

- WhAPI events are durably persisted and deduplicated at the webhook boundary.
- The one-minute webhook reconciliation job is active.
- The five-minute Housing inventory reconciliation job is active.
- The six-hour AI scheduler is active.
- Scheduled AI runs use per-lead checkpoints and idempotency keys.
- Automatic WhatsApp sending remains disabled; outbound messaging is operator-controlled.
- High-consequence AI status changes remain review-gated.

## Hardening closure

### Closed in this release

- Deterministic OOC assignment: only an exact, controlled out-of-coverage location set can auto-apply `Out of Coverage Area`. Selective, mixed, or unknown locations remain review-required.
- D08 documentation handoff: current UI architecture, operator-control boundaries, evidence model, inventory boundary, and production verification contract are documented in the current CRM documentation set.
- Current-status documentation: key CRM operational documents are being normalized to this snapshot and volatile historical claims are being removed from current-status sections.

### External infrastructure prerequisites

These cannot be truthfully marked complete from the connected repository/Render/Supabase interfaces alone:

- Independent encrypted backup artifact plus restore into a separately provisioned target. The repository already contains encrypted `pg_dump`/`pg_restore` tooling; the missing production evidence is an independently owned durable destination and an isolated restore target.
- AWS least-privilege credential rotation. The application uses the AWS SDK default credential chain, but creating/replacing the production IAM identity requires an authorized AWS IAM environment. No AWS IAM management connection is available here.

These are infrastructure provisioning tasks, not application-code defects.

## Deferred product changes

The following are intentionally not classified as production-hardening blockers:

- Incremental/delta AI analysis optimization.
- Field-level editing of AI-proposed requirement updates.

They require separate product/UX acceptance and are not silently represented as production-complete.

## Verification contract

A release is current only when all of the following are evidenced:

1. GitHub build/test/browser verification passes for the deployed commit.
2. Render reports that same commit as live.
3. Supabase scheduled jobs remain active and succeeding.
4. Webhook, inventory, and AI integrity queries reconcile cleanly.
5. `main` is reconciled to the same verified tree.
