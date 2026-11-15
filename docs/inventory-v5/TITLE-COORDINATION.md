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
