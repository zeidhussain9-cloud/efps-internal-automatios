# Staged title-intent coordination

The explicit `run_coordinated_renumber` entrypoint now supplies real title hooks
through `CoordinatedTitleRepository`, the existing authenticated Edge transport,
and disposable-test SQL. It is not wired into the production webhook or the
15-minute reconciler. No live feature flag, migration or deployment changed.

The coordinator requires the Housing parent and fresh matching schema seal,
then holds the dependency row lease through title preparation, dispatch,
readback and acknowledgment. A separate title pending-kind stops a generic
dependency worker from consuming unfinished title work. Owner edits must be
acknowledged before numbering can proceed. Matching a human-entered rank does
not turn it into generated provenance.

Preparation records exact old values and the narrow desired title, but does
not advance generated-title provenance. Only the exact readback acknowledgment
updates the title baseline and provenance. Interrupted preparation can resume
its exact intent; interruption after a confirmed write but before acknowledgment
finishes the acknowledgment without a second PATCH.

The title job and dependency row both persist effect nonces and exact dispatch
bindings. The narrow documented saved-503 response is recorded in both scopes
before readback. Unknown transport flight keeps both barriers. Recovery needs
independent operator evidence for each exact effect, not a timeout or stable
read. The paired recovery test uses synthetic attestations, not real remote
terminal evidence. Operational acceptance of this potentially indefinite hold
remains unresolved.

A job's fixed membership snapshot can finish while a later membership job is
pending. That result is `completed_snapshot` with `membership_current=false`,
not a claim that the currently active inventory has its final numbering.

Tests exercise actual Python hooks, typed HTTP serialization, the staged Edge
handler and isolated PostgreSQL. They cover row-worker exclusion, owner edits,
crashes before dispatch and acknowledgment, both barriers and receipts, stale
leases, changed schema, membership changes, paired attested recovery and a
title-only generated-event pass without caption regeneration. No real Notion
atomic CAS is possible; prewrite/refetch checks only detect races they observe.

Still separate release gates: production scheduling and incident routing,
known-Housing lifecycle, v5 reconciler, controlled migration/inverse executor,
full E2E and restored dependencies/import-map/config. Raw Intake destination
compatibility remains held for the user's separate answer. Source/caption/
area/pet ownership holds remain unchanged. This is not cutover approval.

## Atomic title acknowledgment and mirror synchronization, staged B checkpoint

Title preparation now freezes the ENTIRE validated old mirror row along with
its durable pending title. Accepted old revisions are explicit: row N/mirror N
(new receipt-proven bootstrap or prior title acknowledgment) and row N/mirror
N-1 (the established destination/dependency acknowledgment convention). An ahead
mirror, quarantine marker, deleted/wrong-domain/wrong-binding mirror, mismatched
canonical/legacy state, or incomplete business-state baseline refuses. The
fixtures now provide complete Availability/Live On and mirror source controls;
SQL checks were not weakened to fit missing fixture fields.

`finish_title` validates the same frozen mirror, exact title readback and current
row lease. One SQL transaction changes source_record's SL number, mirror revision,
source hash and last-sync observation time, then acknowledges row values and
derived-title provenance. All other mirror columns and JSON annotations remain
unchanged, including business Availability, canonical/legacy status semantics,
Live On, media and original source snapshot/onboarding time. The title observation
hash is SHA256 over the new full source_record's UTF-8 PostgreSQL JSONB text. It
is a deterministic integrity key for that projection, not pipeline authorship or
an assertion that the older source snapshot was recaptured. It does not use the
creation plan's canonical-JSON value hash after the title changes.

A failed mirror write rolls back row acknowledgment and provenance too. A mirror
changed since preparation is not silently merged or rebased; visible HTTP title
may already have changed while SQL still holds the pending intent. Lost finish
responses resume without another PATCH. `ack_existing_title` now verifies the
mirror before skipping an already-numbered page, requiring equal row/mirror
revision for a previously generated title. A matching human title gains no
ownership simply because it matches a rank.

Lock order for title operations is reference advisory 55151126, worker row,
mirror. Reference/title-job functions take the same advisory lock before their
own membership/job rows. No transaction here requests a job row while holding
a worker/mirror lock. These SQL lock acquisitions are exercised in serial actual-
port tests, not proven across every concurrent schedule. An attempted disposable
parallel PostgreSQL test could not start because only PostgreSQL client binaries
are installed, not postgres/initdb/pg_ctl. Genuine multi-connection concurrency
validation remains open; serial PGlite is not evidence of it.

The created fixture test proves blank-title row1/mirror1 can use these same hooks,
while retaining Processing, unknown non-title ownership and empty source relation.
It does not add a creation-to-source ACK anchor, current-membership final source
commit, next-version handoff or source completion. C-E remain separate work. The
fixture gate/production draft visibility/readiness/ownership/operator decisions
and Notion no-CAS limitation are unchanged. Existing-source frozen revision guards
are deliberately not relaxed to accept a later title revision.
