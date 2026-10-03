# CRM UI — Code Health & Follow-up Work

> Point-in-time notes from the independent audit of `crm-ui-dashboard` (2026-10-04).  
> Not a production status claim. Update only when the underlying code structure changes.

## Addressed in this change set

- Login rate limiting is explicit (`LOGIN_FAILURE_LIMIT` / `LOGIN_FAILURE_WINDOW_MS`), documented, and covered by unit tests (lockout, reset on success, per-client isolation).
- Dependabot enabled for npm and GitHub Actions so dependency and workflow updates surface as PRs.

## Known structural risks (not fixed in this PR)

These remain intentional follow-up items. Do not treat them as production blockers unless behaviour regresses.

### 1. Monolithic UI entry (`src/main.jsx`)

The React app concentrates routing, auth shell, leads inbox, lead workspace tabs, classification queue, inventory panel, audit views, drafts, and privacy mode in a single large module.

**Recommended direction (incremental, behaviour-preserving):**

1. Extract pure helpers and small presentational components first (already partially true for inventory).
2. Introduce feature hooks (`useLeadsList`, `useLeadWorkspace`, `useClassificationQueue`) without changing API contracts.
3. Split route-level pages only after hooks are stable and browser tests still pass.

### 2. Concentrated data access (`src/crm-repository.mjs`)

Most CRM reads/writes and activity logging go through one repository module. This simplifies transactions today but concentrates change risk.

**Recommended direction:**

- Keep a shared connection / transaction helper.
- Split domain surfaces (leads, messages, activity, inventory snapshot, AI cursor) only when a clear seam exists and tests cover both sides.
- Prefer additive modules over a big-bang rewrite.

### 3. External infrastructure gates

Independent encrypted backup / isolated restore and AWS least-privilege IAM rotation remain **external** prerequisites. Repository code must not claim them complete without independent evidence.

### 4. CSP style policy

`style-src 'self' 'unsafe-inline'` is required by the current Vite-built CSS approach. Revisit only if styles are moved to nonces/hashes without breaking the operator UI.

## Verification expectations for future modularization PRs

- `npm test` (unit + server) green
- `npm run test:browser` green when UI structure changes
- CRM UI Verification workflow green on the branch
- No silent change to classification, auth, or write opt-in flags
