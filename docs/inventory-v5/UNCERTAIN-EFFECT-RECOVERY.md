# Uncertain Notion write recovery - staged, not deployed

A durable effect barrier is a safety stop, not a timer. Ordinary workers cannot
create the operator recovery attestation. No production verifier is configured;
the default raises RecoveryBlocked. Never clear the barrier only because an
HTTP request timed out, its lease expired, its process died, or two reads agree.
A requests timeout is not a total execution deadline or proof of remote quiescence.

## Before clearing

1. Stop/quarantine new work for the affected page/job and preserve the exact
   active_effect, pending patch, prepared inputs, request identifiers and logs.
2. Establish that the former local writer cannot resume or issue another write.
   Record independently verified termination/fencing evidence for that exact
   invocation. Process death is necessary in some cases but is not sufficient.
3. Independently establish that the exact remote mutation cannot still apply:
   a terminal response for the identified request or a documented upstream
   cancellation/drain guarantee. A transport exception without a terminal
   response does not meet this gate. This integration currently has no generic
   Notion remote-request status/cancellation guarantee. If terminal evidence
   cannot be obtained, leave the barrier in place and report a blocked listing.
   Do not trade availability for a silent overlapping write.
4. Fetch current Notion state and compare every relevant value to the prepared
   before values and exact intended patch. A third value or unrelated new edit
   requires owner review. Do not overwrite it or certify it as generated.
5. A database administrator may register a single-use attestation bound to the
   exact effect JSON, page, optional job, writer evidence, remote evidence and
   exact request evidence. The service-role worker cannot insert/update these
   attestations. Evidence references must point to actual inspected records,
   never text invented to satisfy required fields.
6. The reconciliation function uses readback plus the trusted verifier, then
   calls the recovery RPC. SQL checks the unused attestation, exact effect and
   expired/no-active lease atomically. A changed effect refuses recovery. The
   RPC clears only that barrier, preserves pending work and marks the proof used.
   It does not write Notion or acknowledge unknown values as successful.
7. Resume only through a fresh lease. The ordinary pending-intent replay must
   still pass exact before/intended/third-value checks. Read back, mirror under
   the revision fence and then finish. Title jobs keep their checkpoint and use
   the same title-only rule. Preserve a full incident record and notify the owner
   when work remains blocked or a manual value needs a decision.

## Verification performed

- Unit tests reject missing proof, third values, changed tickets, timeout-only
  claims and automatic clearing. Default verifier performs no Notion read/write.
- Isolated SQL rejects missing/mismatched/reused attestation and denies worker
  insertion. Exact saved effect CAS is required.
- Actual repository -> actual Edge -> isolated PostgreSQL test leaves uncertain
  effect blocked, rejects default recovery, uses a synthetic administrator proof
  fixture, reconciles without a Notion mutation, preserves pending work and then
  permits a fresh claim. The synthetic proof is not a production verifier.
- Worker and renumber adversarial tests show an expired old effect cannot be
  overtaken. Native human Notion edits are still not protected by atomic CAS.

Release remains blocked for any path that requires guaranteed automatic recovery
from an unknown Notion flight. Do not describe this as unconditional self-healing.

## Operational acceptance still required before release

The incident table records the exact blocked effect on a refused takeover and
records reconciliation readback, remaining values, state hash, decision and
attestation reference separately from ordinary worker state. Worker return is
needs_recovery/blocked, not ordinary busy. The title queue also returns
needs_recovery. These are backend signals only: no deployed operator view,
alert routing, named incident owner, database attestor or response commitment
has been selected. Those must be explicit before release.

One uncertain listing write can block that listing indefinitely. One uncertain
title write can block all later numbering jobs indefinitely. Do not call this
bounded recovery. If the owner does not accept this tradeoff, defer automatic
writes/renumbering until there is a supported remote quiescence guarantee.
A production incident view should show affected listing/job, first blocked time,
exact effect reference, owner, evidence still missing and next action, without
exposing credentials. Alert on a new incident and material state changes; do
not send repeated unchanged alerts. Routing/account changes remain gated.

The service role is privileged trusted application code. The recovery table's
restricted insert grant prevents accidental use through the ordinary port; it
is not a tamperproof boundary against malicious code with other privileged
capabilities. Python readback validation is part of the trusted implementation.
The SQL recovery RPC persists that readback/decision, checks exact effect and
attestation CAS, and does not independently interpret Notion values.
