# Existing Housing runtime adapter - staged only

The Lambda source now has an existing-Housing-only v5 adapter, enabled only when
`EFPS_INVENTORY_V5_ENABLED` equals the exact string `true`. Default and other
values retain the legacy route. This is not deployed or ready to enable.

The adapter requires an exact reviewed schema hash through
`EFPS_INVENTORY_V5_SCHEMA_SHA256`, the final v5 types, a known page-to-listing
mirror binding and a seeded acknowledged baseline with the same identity. It
does not mint a production schema seal, infer legacy ownership from a live edit,
allocate a new identity or seed order. Current Notion is fetched for each old
queue redelivery; stale event row snapshots are not used as write payloads.

Existing active pages run through the actual dependency repository, narrow
Notion HTTP/dispatch/receipt port and lease/revision-qualified mirror request.
The source mirror gets contract version 5 and a qualified onboarding instant;
internal snapshot keys are not projected. Invalid dates fail rather than gaining
a guessed instant. A changed page listing ID is compared to the known stored
identity, not promoted to a new identity.

V5 busy/retry/needs_recovery outcomes cannot be marked processed by the old event
status mapper. Review maps to the existing needs_review ledger state. Unknown
v5 outcomes fail closed. No legacy writer is attempted after v5 failure.

## Explicitly unfinished

- New page membership, deleted pages, restored pages and moved-out pages need
  coordinated reference-order/title handling. These paths now refuse legacy
  fallback when v5 is enabled. They are not claimed supported.
- The old 15-minute reconciler refuses to run with v5 enabled. Its coordinated
  v5 adapter and a witnessed resumed cycle remain required before release.
- Raw Intake follows its existing route. Compatibility of its legacy writer
  with the final schema/owner state is a separate unresolved deployment gate;
  this work does not switch it to v5 or alter WhatsApp processing.
- No operational title provenance hooks, production seed loader, automatic
  unknown-flight recovery, controlled migration/rollback executor or deployed
  incident routing are supplied by this existing-page adapter.
- This read-before-write architecture has no Notion atomic CAS. Test fixtures
  and isolated SQL are not a live end-to-end or coordinated transaction proof.

## Tests and request limits

Isolated tests cover the actual runtime -> repository -> Edge -> disposable SQL
path, typed page HTTP writes/readback and repeated old queue delivery. Routing
tests cover default legacy mode, enabled existing Housing, Raw Intake archive,
delete/archive safety, missing/changed schema seal, unseeded identity, unsupported
membership/reconciler and event outcome acknowledgements.

Rich text is losslessly chunked to at most 2,000 UTF-16 units per item, capped at
100 items. A conservative 500,000-byte properties payload cap uses the escaped
JSON encoding before dispatch binding or HTTP. Oversize input is rejected, not
truncated. These local failures do not justify automatic clearing of an already
begun durable effect. Official size limits:
https://developers.notion.com/reference/request-limits

## Known-parent boundary repair

The first staged adapter missed two known-move cases. A canonical Housing page
moved into Raw Intake could enter the old intake route, and a move after outer
routing was not checked by the runtime snapshot. Neither path was deployed.
The enabled route now resolves a known inventory binding before any non-Housing
route or archive shortcut. Every runtime snapshot requires the expected Housing
parent, including prewrite refetch and postwrite readback. Known moves, missing
parents and wrong parents refuse patch/mirror effects. This remains a checked
read-before-write boundary, not atomic CAS against a simultaneous move.
