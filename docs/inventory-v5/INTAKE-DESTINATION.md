# Approved destination compatibility: staged layer 1

Zeid approved build and test on 15 November 2026 at 23:25:03 IST after the
current behavior, broad existing-row rewrite weakness and final-schema mismatch
were explained. Approval excludes WhatsApp messages, receiving triggers,
posting, recipients and photo handling. It does not approve any live action.
The original approval and explanation are recorded in the Decision Log.

`inventory_v5_intake.py` is the first pure destination layer, NOT a completed
adapter and NOT connected to the intake worker. It validates the final schema
seal, title/formula/status/channel contracts and each selected option. Exact
package vocabulary as a whole relies on the independently reviewed sealed schema,
not a separate complete-vocabulary check in this layer. It uses
only the already reviewed strict package/tenant/BHK mapping. Custom or unknown
values stop for review instead of silently dropping detail.

Legacy source processing/status outputs are never treated as canonical
Availability, Pipeline Status or Live On. No source payload supplies the SL
number. No creation rank is guessed. Existing title, availability/channel
history, identity, catalog title, dates, media, raw source and routing cannot be
overwritten by a new processed payload through this existing-row plan.

An existing row must match its acknowledged baseline. Only a field whose
provenance already marks the current value as generated can change automatically.
Matching an owner or legacy value does not manufacture generated ownership.
Other changed values are preserved and cause a Needs Review plan. A Removed
listing refuses every changed source update, even to a generated field, until
an explicit lifecycle decision; source reprocessing cannot reactivate it. The plan
carries an exact before hash and cannot mark the source complete.

## Still required before this is an adapter

- A durable source-to-destination submission ledger: serialize payload versions
  for a source, exact source/listing/page binding and phases, no early source
  success, and exact source relation/status readback acknowledgment.
- Existing-row executor with row lease, exact before/refetch, pending-kind fencing,
  narrow typed writes/readback, qualified atomic mirror and provenance finish.
  A pure plan is not a durable write or a consumed approval.
- New row controller with idempotent create intent and unknown-flight barrier.
  If a create response is lost, never retry the POST on a timer. Recovery needs
  proven terminal evidence and verified unique identity/source binding.
- Coordinated membership, baseline/provenance seed, mirror and title jobs before
  source completion. Existing known-Housing lifecycle is still a separate gate.
- Strict duplicate-identity search, all relevant pages checked, wrong-parent and
  archived/restored destinations refused rather than silently reused.
- Actual old intake routing behind a disabled flag only after these ports and
  tests exist. Validate destination before media work, retain uploaded results
  and pending source acknowledgment across retries, and do not replay the whole
  legacy extraction/media pipeline just to finish destination acknowledgment.
- Full synthetic actual-port interruptions and independent review. No live
  Notion/Supabase mutation, deployment, consumer pause or schema cutover.

These gates deliberately remain open. This layer protects values by refusing
unsupported effects, not by pretending a database transaction includes Notion.

## Staged layer 2: existing destination execution and source phase ledger

`save_existing_destination` now exercises the real row-state/effect HTTP/mirror
ports and an additive source-submission SQL ledger through the staged Edge
handler. It is still an explicit entrypoint, not connected to intake routing.
The source/listing/page unique-active binding resolver remains a required
injected verification port, not a production lookup supplied by this layer.

Each source submission freezes payload hash, candidate and destination identity.
A different payload/binding is refused while this submission is unresolved.
An exact plan is durable before a dedicated intake row intent. Generic workers
cannot consume that intent. Generated provenance advances only at exact final
row acknowledgment, after readback and the lease/revision-qualified mirror.
Detected owner changes block writes/replay/acknowledgment. Removed rows retain
their explicit lifecycle hold.

A known completed row acknowledgment can resume a lost source-ledger response
without another PATCH. A plan or row intent interrupted before dispatch resumes
its exact remaining work. A mirror failure retains the pending intent and old
acknowledged provenance. Unknown Notion flight keeps the durable effect barrier.
There is no automatic timeout-based recovery or second uncertain PATCH.

The source ledger can enter `awaiting_source_ack` only after SQL independently
checks the exact acknowledged destination row, matching expected revision and
active mirror record including page identity and values. This phase is NOT
source success: source completion remains false; there is no finish operation.
The ledger currently refuses later payload versions even after destination ack
because final source acknowledgment/version handoff remains unimplemented.

Known remaining gates include final source relation/status acknowledgment,
new-create/idempotency/membership, actual binding lookup and production route
wiring, complete interrupted recovery availability, plus the broader release
gates. Tests use synthetic typed Notion HTTP and actual staged Edge/SQL ports,
not real Notion atomicity or a production E2E proof.

### Frozen-plan revision guard

A source plan also freezes the destination revision. If the process stops after
saving that plan but before installing the row intent, a normal dependency
acknowledgment, title pass or second source can advance the destination revision
without changing visible values. The executor now explicitly refuses before any
new preparation/effect when that frozen revision differs. It does not rebase the
plan, regenerate its candidate or relax destination acknowledgment to accept
arbitrary newer revisions. The planned submission stays blocked for explicit
resolution. Tests exercise all three intervening paths through actual ports and
verify zero destination PATCHes and unchanged provenance on refusal.

### Detected owner conflicts quarantine both mirror read paths

A detected conflict after a destination intent, including prewrite refetch,
postwrite readback, pending replay, or postmirror owner edit, now calls a
lease/revision/page/listing-qualified SQL quarantine. It sets canonical pipeline
and legacy business status to Needs Review on the known bound mirror without
copying owner values back or changing identity. The pending intent, acknowledged
row and provenance stay intact, and the source cannot complete.

Quarantine raises the mirror revision only. Normal mirror replay at the old row
revision consequently fails closed until explicit conflict resolution. This is
a conservative operational hold, not automatic reconciliation or a claim the
mirror now contains the owner's newest rent. A stale lease/revision, wrong page,
wrong identity or missing v5 mirror binding cannot quarantine another record.
Tests cover owner edits detected before dispatch, after write, after mirror,
on replay, plus postmirror identity/parent/archive changes and stale/wrong
quarantine calls. Unknown undetected concurrent Notion edits remain outside the
read-before-write guarantee.

### Cross-invocation validation failure

If a later invocation rejects a changed schema or no-longer-unique binding before
normal row loading, it now checks for an existing immutable source submission.
It claims only an already-existing pending intake row, verifies the stored plan,
original page/listing identity, payload marker and revision, and quarantines that
original mirror. New candidate identity/page values do not choose the target.
An initial invalid submission creates no ledger or row and cannot quarantine an
unrelated mirror. A busy, missing or unproven original pending row remains an
explicit incident-review gap; no unverified quarantine is claimed.

## Staged layer 3: actual binding reads and partial source-ack preparation

`ExistingBindingResolver` replaces a no-op/injected uniqueness assertion with a
read-only Notion/Supabase implementation: recover the existing immutable source
binding (submission ledger, otherwise legacy intake ledger), require its active
v5 mirror page binding, inspect the current Raw Intake source identity/parent/
payload hash/single relation, fully paginate the destination identity query,
require exactly one active Housing page, then re-read the source. It uses the
existing raw-text/photo claim hash without uploading or processing media.
Missing historical relation/mirror/binding is a hold, not guessed membership.

The existing executor can use this callable, but production intake routing still
does not instantiate it. The required v5 mirror means this is a post-bootstrap
existing-row reader, not a legacy-to-v5 bootstrap or a new-create path.

`prepare_source_ack` stores an immutable source-before snapshot/hash and proposed
Listing ID/relation patch under the source lease. SQL rechecks exact acknowledged
destination and mirror revisions/values. A duplicate exact preparation is
idempotent; changed source snapshot, payload, destination revision or stale lease
is refused. No source PATCH occurs. There is deliberately NO Processed/Needs
Review status patch: upstream processing outcome has not been captured in the
ledger, so a caller-provided status must not manufacture source success.
`source_status_unresolved=true` and `source_completion_allowed=false` remain.

Still required: durable upstream outcome, source schema seal/effect dispatch and
receipt proof, source PATCH/readback, exact ledger finish and payload-version
handoff. Preparing this relation plan is not completing source acknowledgment.
These tests use actual staged Edge/SQL and a synthetic Notion read client, not
live accounts. No production or WhatsApp-flow changes are included.
