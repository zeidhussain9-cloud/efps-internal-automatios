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

## Staged layer 4: saved upstream output, sealed source contract and effect preparation

`capture_upstream_output` freezes exact processed output and issues under the
existing source submission. It accepts the existing final pipeline statuses
Pending/Needs Review only, checks the destination candidate and payload binding,
and refuses replacement. This is an explicit staged capture boundary, not yet
called by the live pipeline. Its output hash does not prove who ran extraction.
Production orchestration must capture the unmodified result once after existing
media/maps/caption checks and resume from that result, not replay those steps.

`prepare_source_write` derives source Processed/Needs Review from that saved
output and saved destination conflicts, never a later caller's Processed request.
It retains the existing notes-append behavior and freezes a qualified processed
instant. Required source property IDs/types/status options/relation target are
sealed and reread. The exact source object is read twice, not merely trusted by
hash. SQL independently checks the frozen destination and mirror revisions.

`SourceEffectPreparation` supplies durable begin/dispatch/terminal-receipt/
readback/finish-preparation transitions. Begin compares exact saved source
snapshot and schema objects; bind requires the saved body hash; receipts require
the exact effect nonce/dispatch/request reference and a terminal success or the
narrow documented saved503 response. Readback compares all source property
values and page binding to the saved expected result, then rechecks destination
state before recording finish_prepared. Unknown source flight blocks subsequent
claims without an automatic timer clear.

There is still NO source HTTP writer and NO ledger finish/source completion
operation. Tests inject synthetic terminal receipts and readbacks into the real
Edge/SQL state machine, without actually sending a source PATCH. Even
finish_prepared keeps awaiting_source_ack and completion false. Source outcome
capture wiring, source execution/recovery/incident handling, final ledger commit
and next-payload handoff are not supplied by this checkpoint. New creation,
bootstrap, membership and production routing remain separate gates.

## Staged layer 5: coherent existing-row source completion

`run_existing_intake_staged` is an explicit, unconnected staging entrypoint. It
uses the actual shared `final_intake_output` body from the legacy intake, with
its photo/maps/locality/caption behavior unchanged. Only that function's exact
output is frozen. The initial pipeline row and clients still come from staging;
this is not a production route or a complete new/legacy inventory bootstrap.
No WhatsApp receiving, sending, posting, recipients or photo algorithm changes
are included. The production `process_page` still uses the legacy save path.

A durable pipeline-run ticket precedes extraction/media. A saved output resumes
without repeating those steps. A process stopped before capture remains held,
even if a media upload may have completed. It does not silently replay the whole
pipeline. A capture hash is integrity evidence, not proof of who ran a model.

`complete_existing_source` holds the source and known destination row leases,
checks exact current destination values/identity/parent/archive against the
frozen destination acknowledgment, and rechecks SQL row/mirror revisions. The
live destination check is repeated before dispatch, after response, and before
final commit. Detected conflicts quarantine the original bound mirror in both
canonical and legacy status readers without replacing the owner's values.
An identity query alone is not a live value check.

The source writer uses the actual one-attempt HTTP transport and stores its
exact effect nonce, page, method, body hash and server request reference. Normal
success and the narrow documented saved503 can read back; unknown transport,
missing request reference or unsaved receipt leaves a durable hold. Restart can
claim an effect ONLY with its already-persisted terminal receipt, then reread
without another PATCH. A source/effect/readback commit response lost after the
write resumes through saved state, not through a second source write. Duplicate
server request references cannot acknowledge different source effects.

Exact source values/schema, final live destination reads and a SQL commit under
the current row lease are required before `completed`. A new raw/photo version
can replace only a completed version with the same source/listing/page binding;
the old full submission including its effect/receipt is archived. Old archived
payload hashes cannot be used for a handoff. New work starts incomplete, with a
new actual pipeline run and no inherited success/outcome.

This is read-before-write protection, NOT Notion CAS or a transaction spanning
Notion and SQL. An owner edit after the last read can still race a source PATCH.
If detected after that PATCH, SQL completion is refused and the destination
mirror is quarantined. The source may already display Processed in that case;
there is no speculative compensating PATCH. The unresolved incident must be
handled explicitly. Unknown-flight and pre-capture holds have no automatic
operator recovery or timeout-clear path in this layer.

Tests use actual staged Edge/SQL and actual HTTP serialization/response handling
with synthetic remote services/model/media. They are not live Notion E2E proof.
New-create/unknown-create/bootstrap/membership, known lifecycle, reconciler,
production initial-row/route integration, controlled migration/inverse,
operator recovery acceptance and final content/release gates remain open.

## Isolated new-create checkpoint, not new-property completion

`inventory_v5_create.py` and the additive fixture migration cover only a bounded
new-source reservation, actual-output capture, one POST, receipt/readback, and
atomic baseline/mirror/provenance/reference/job bootstrap. There is NO source
relation PATCH/completion, title-pass orchestration, existing104 bootstrap,
production routing or live execution. A separate create-fixture flag defaults
OFF even if v5 is enabled. Its mandatory sealed policy names isolated fixture
visibility, Available, Processing, empty Live On and blank title. Those values
are explicit test inputs, not an approved production visibility policy.

Material blocker: the legacy CRM reader filters Available without a readiness
check. Processing does not hide an Available draft. This checkpoint does not
change those readers, invent a business availability to hide drafts, pause any
consumer, or claim a safe production draft. Missing fixture policy refuses
before allocation/media/create. Contradictory raw availability, production draft
visibility and full per-field lineage still require grounded resolution.

A new-source reservation atomically inserts its own legacy claim, uses the
established allocator's UTC-month/Crockford ID format, and freezes that result.
Preexisting legacy claims are refused because an older pipeline may still have
untracked external work. Legacy claim/allocator calls cannot take over a v5
reservation; new reservations participate in ID collision checks. No later
legacy-ID edit changes the immutable create binding. This is staged SQL, not a
claim that deployment has fenced the current live writer.

Before media and before POST the controller checks the exact source raw/photos,
empty complete relation, source IDs/types/schema seal, destination schema and
fully paginated allocated-ID query. One durable pipeline ticket protects media
capture from replay. Original onboarding instant, outcome and media results are
frozen. One POST binds URL/method/parent/bodyhash/effect nonce. Templates and the
PATCH saved503 rule are not used. A terminal response must contain server request
reference, page ID and complete body; absent/unsaved evidence holds indefinitely.
A later query match never authorizes adoption or another POST. Even a begun
intent interrupted before dispatch conservatively stays held.

Only the receipt-proven page can pass postresponse unique-identity and full typed
GET/readback, including stable property IDs/types and readonly/owner fields.
Source edits after POST hold without attaching the old page to a new payload.
Owner edits or duplicate identity hold before bootstrap. Exact row baseline,
unknown-ownership provenance, mirror, reference membership and queued title job
commit in ONE SQL transaction; a failure rolls all five back. Response loss can
resume the same receipt and exact bootstrap without new POST/media/reseed.

Every seeded value currently has legacy_unknown origin plus its exact created
value and create nonce. This proves what this controller wrote, not whether each
value was explicit source fact or derived. It deliberately does not seed all
fields as generated. Consequence: later automatic updates can refuse for review
until field lineage is proven. Existing arbitrary rows never gain ownership from
matching values. The title baseline is exactly blank, not a guessed rank; future
current-membership title/lease/mirror acknowledgment is still required before a
new source may complete. Read-before-write is not Notion CAS. Unknown create and
pre-capture holds still need explicit operator resolution, not timer clearing.
