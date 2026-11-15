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
