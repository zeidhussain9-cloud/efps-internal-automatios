# Remaining runtime gates after management access

15 November 2026. Preparation only. No live execution or release approval.
Baseline inspected: 20047d57ca22967ac67c49e4d5ac1c16932be3c7.

## What changed in the evidence

The read-only management inspection captured deployed inventory Edge v12 and
WhatsApp Edge v10 configurations, complete ESZIPs, embedded original application
sources and relevant SQL definitions. WhatsApp source exactly matches this
branch. Inventory v12 does not contain staged v5 routes. Raw body hashes are
backup hashes, not the platform's separately reported ezbr hashes. Artifact
capture does not prove a successful restoration or deployed v5 equivalence.

Native private 104-row schema/value forward and inverse checks passed for the
fixture baseline. They are not a controlled production executor, mirror restore,
atomic operation, live cutover or human-edit concurrency proof.

## Independent inventory work, in dependency order

### 1. Title intent and acknowledgment

Current `V5RenumberRepository` injects `prepare_title` and `ack_title` hooks.
There is no production hook that binds a title change to the dependency worker's
owner state. Its title effect also lacks the worker port's dispatch binding and
terminal receipt hooks. Finish these together, not by inserting no-op hooks.

Required checks:
- The same page/listing binding and schema seal apply to every title read/write.
- A prepared title, exact before value, membership job and lease are durable
  before dispatch. No title effect can race an active row dependency effect.
- A human title change becomes review. No blanket title overwrite on retry.
- Acknowledgment updates generated-title provenance only after matching readback.
- Crash before dispatch, after dispatch, after readback and before acknowledgment
  resume safely or remain explicitly blocked. No timer clears unknown flight.
- A membership change during a pass queues the next complete snapshot and does
  not falsely mark a mixed pass as the current complete order.

### 2. Known Housing lifecycle

Current enabled runtime rejects new membership, deleted, restored and moved-out
pages. Preserve that refusal until one coordinated lifecycle port exists.
Identity allocation for incoming Raw Intake is OUTSIDE this independent step.

Required transitions for known Housing identities:
- Active to archived/moved-out: read current parent/state, tombstone the bound
  mirror identity, deactivate reference membership, persist pending order work.
- Archived/moved-out to restored Housing: preserve listing ID, confirm current
  binding/parent, reactivate membership according to reviewed ordering rules,
  and queue title plus dependency work without borrowing stale event values.
- Persist resumable intermediate phases. A webhook receipt cannot be processed
  while mirror or membership work is still pending.
- Test duplicate and out-of-order delivery, delete then restore to a previously
  completed membership, stale leases and human edits during each boundary.

### 3. Existing 15-minute reconciler

The enabled reconciler currently refuses all execution. Replace refusal only
when the known lifecycle port exists. One fully paginated, validated Housing
membership read drives current-state comparisons, not an old event snapshot.
Never treat a failed or empty query as permission to mass tombstone.

Required checks:
- New/unregistered pages are a durable hold, not implicit intake approval.
- Known membership changes use the same lifecycle port as webhooks.
- Unchanged rows do not loop into self-write processing.
- Paging failures, duplicate IDs, wrong parent, identity collisions and schema
  changes stop the cycle without acknowledging a complete scan.
- Synthetic resumed-cycle integration precedes an authorized deployed cycle.

### 4. Controlled migration and inverse

`inventory_v5_migration.py` contains pure guards, not an HTTP/SQL executor.
Native fixture scripts prove representability and ordering but are not a
production release controller. Prepare a separate disabled executor with:
- A fresh sealed whole-run manifest: property IDs/types/options/views, exact
  typed row before/after values, owner/provenance, qualified dates, mirror
  before/after state, reference order, queue watermarks and code/config backups.
- One run ledger with schema/row/mirror/order phases and exact checkpoints.
- Prewrite refetch, narrow patch, readback and changed-row review instead of
  applying a stale manifest. No proof of Notion CAS is claimed.
- A reverse-schema-before-values inverse, preserving new edits as conflicts,
  followed by mirror/order/view validation before any consumer restart.
- A disposable full-size combined rehearsal with interruption at each phase,
  exact final readbacks and tested restoration of captured application
  dependencies/import-map/config, not only the entrypoint text.

## Separate held scope

Do not implement the final-schema Raw Intake destination adapter until the
user's answer is recovered. No WhatsApp messages, triggers, distribution,
posting, recipients, media behavior or settings changes. No silent intake pause.

## Release gate remains closed

These preparations do not accept the uncertain-flight operational tradeoff,
settle held area/pet/caption ownership, provide a final exact manifest, authorize
SQL migrations/deployment, or authorize cutover/old-column deletion. Send the
complete manifest and rollback checks for final review before any live action.
