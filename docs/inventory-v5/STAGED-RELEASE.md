# Inventory v5 staged build - 15 November 2026

Status: implementation in progress, not a release or cutover approval.

Original scope: inventory columns FIRST. WhatsApp flow remains entirely untouched until inventory is finished and Zeid separately says to move on. No WhatsApp intake/distribution runtime or webhook changes. Inventory-only Notion/Supabase work uses synthetic tests; crossing this boundary is a blocker, not permission.
Baseline: 489b242427997b33e8628cb0d5574800f5520034.
No production deployment, schema mutation, inventory rewrite, posting or old-column deletion has been done by this build.

## Verified locally

- 383 Python tests, 152 Node tests and Vite build pass.
- Repository audit includes the new files and passes.
- Disposable PostgreSQL checks cover additive schema compatibility, typed empty channels, vocabularies, RLS, worker fencing, revision checks, persisted write intents, and renumber-job serialization/checkpoints.
- The actual staged Edge handler runs in a local harness with an injected SQL client. It rejects disabled v5 and bad auth/leases and preserves typed mirror values. This is not an Edge deployment test.
- New extraction rules run together over the legacy extractor with manual-value protection. Production webhook routing is not yet connected to this path.
- Pure rollback checks restore each of the104candidate rows exactly and refuse changed inputs. No live rollback rehearsal is claimed.
- A native isolated Notion database with synthetic titles10,2,1 sorts visually1,2,10using a hidden formula property. Production Housing has not been changed.

## Explicit schema choice

Rename the required title Property to SL number, preserving its property ID. Add a hidden formula `_SL numeric sort` with expression `toNumber(prop("SL number"))`. Sort All Properties ascending by this formula and keep it hidden in every client-facing view. Preserve other views' chosen filters/sorts unless the reviewed manifest explicitly changes them. Source: https://developers.notion.com/reference/update-a-view . The API supports property-based sorts; sorting numeric text titles is not sufficient.
The104-rowseedis the fully paginated current All Properties order. Do not substitute creation-time ordering:103historicalpages share a timestamp. New pages receive a persisted insertion sequence, newest first. A single resumable renumber job writes only changed titles. The job is not atomic across pages; display maintenance state while changing membership.

## Remaining gates

1. Finish inventory-only direct-Housing Notion webhook/runtime integration behind a disabled-by-default feature gate. Defer any Raw Intake integration that changes WhatsApp intake behavior to its later separately authorized phase. Wire durable order RPCs and title intent acknowledgements. Do not present the injected ports as a live worker.
2. Independently review the code, SQL functions and state transitions. Add missing deletion/restoration-to-a-previous-membership regression and end-to-end port tests.
3. Finish field-by-field caption/source/pin/manual-correction audit.51structuralcandidatesareheld. A nonempty caption and a stored source link do not prove its facts or building.
4. The104carpetvalues match the old90%helper, and all104rawbuilt-upanchorsmatchcurrentbuilt-upvalues. Prepare exact90sqftreplacementdiffs, but do not infer field ownership solely from matching a formula.8storedpetNofieldsconflictwithanunstated-Yesoverlayandremainprotected.
5. Verify deployment access and the Edge bundle. The saved Supabase item is a service-role JWT, not a Management API token. Body retrieval returned401. Supabase dashboard is signed out; GitHub SSO asks for a missing website login. A repository push token is not a website password. No credential reset or failed password attempt occurred.
6. Rehearse schema conversion and inverse order on an isolated full fixture. Only the additive SQL and pure row inverses are tested so far. Select conversion and property deletion are separate risks.
7. Finish compatibility readers/filters and old-queue handling. The Edge v5 path dual-fills legacy mirror status columns and rejects v4 overwrite of a v5 record, but the full old-queue replay contract still needs end-to-end proof.
8. Obtain the final pre-cutover review against exact row/caption/date/order/schema manifests. Then, and only then, perform a controlled deployment and real end-to-end check, inspect Notion/CRM pixels, and observe one resumed15-minutereconciler cycle.
9. Old Housing columns remain until the separately recorded final deletion gate. Rewrite the simple canonical page only at the END.

## Rollout checklist, not executed

- Capture current deployed code/config hashes, existing Edge bundle or an authenticated rollback artifact, source schemas/property IDs/options/views, all104pages, mirror rows, provenance/order state, queue watermarks and webhook receipt counts.
- Pause derivation consumers, not incoming durable receipts. Drain or quarantine old payloads; keep retry routing intact. Verify no active old writer remains.
- Apply additive SQL once through a migration ledger, not by rerunning raw CREATE statements. Check service-only grants and RLS.
- Deploy compatibility readers and disabled v5 writer. Verify v4 behavior before schema changes and fail closed on incompatible versions.
- Apply reviewed target schemas and exact typed patches using before-hash checks, narrow writes, prewrite refetch and readback. Skip changed rows for review rather than overwrite them.
- Seed the actual saved-view order, apply static titles and hidden sorter, and verify1-104visuallyandbyfullpaginatedquery.
- Enable one controlled v5 worker. Check identity, media order/count, availability, channel history, source/raw text, catalog title, captions, routing, timestamps and status counts.
- Resume normal concurrency and the existing15-minutereconcileonlyafterthecontrolledcheckpasses. Observe the full cycle.

## Rollback

Stop on identity/media/channel-state loss, unexpected posting, incorrect row count, sync divergence or repeated derivation loops. Stop consumers first, preserve receipts and the new owner edits. Restore compatible code before reverting data types. Apply inverse patches only to exact expected post-change rows. A changed row is a conflict, not permission to restore an old copy. Keep additive SQL state and old columns until the final deletion gate; do not run an old full-row writer against new types. Reverse schema order from the saved property IDs/options, then restore values and views, then validate both read paths before resuming.

## Release notes to retain

-9existingnpmadvisories:4high,5moderate. The affected versions are unchanged from the original baseline lockfile. No automatic upgrade was made. Handle in a separate dependency update, not by hiding it in inventory work.
- Management API401andunverified deployed Edge equivalence remain open.
- Native Notion readable timestamp text is not made chronologically sortable by the internal SQL timestamp. CRM chronology uses a separate qualified instant. Only five ISO display offenders are proposed for reformatting; preserve the other99readabledisplaysbyte-for-byte.
- Source preservation and manual ownership can require Needs Review rather than automatic correction. A per-listing lease cannot make Notion atomic against a human edit.
- No Meta/WhatsApp/Housing.com operations are in this build.

## Review repair checkpoint, not independent closure

1. Equal nonblank legacy values retain legacy_unknown even when matching a package. Authorized generated changes advance last_generated_value. Two-pass regressions added for both reviewer repros.
2. Protected source/identity edits persist Needs Review and observed ownership. SQL finish cannot erase Needs Review from acknowledged values. Identity edits quarantine the known mirror identity by its saved page binding, not the newly edited ID. Actual repository -> Edge -> PostgreSQL test added.
3. Database trigger enforces v5 downgrade and monotonic revision rejection under the row lock. v5 mirror uses a lease/revision-qualified transactional RPC. Source page binding is checked. v4 delete/reconcile writes against a v5 row now fail closed; old writers still must be drained before rollout.
4. All ten number fields in the captured Housing schema use numeric equivalence. Actual typed Notion serializer/readback -> repository -> Edge -> PostgreSQL tests cover writes, a second pass and interrupted replay.
5. Worker and title-job writes use durable active-effect intents. A begun but unconfirmed effect blocks successor takeover even after lease expiry. A timeout, crash, uncertain flight or expired completion requires explicit reconciliation after proving the original process/request cannot still write. There is intentionally NO automatic timer that clears the barrier. The production Notion client has a 25-second HTTP timeout, no automatic PATCH retry; each write renews before starting. No SQL lease can provide CAS against human Notion edits. Title-intent provenance hooks are still injected, not deployed.
6. A separate combined schema/value/mirror manifest now preserves property IDs, uses exact typed forward/inverse values, and keeps onboarded_at and contract version only in mirror data. The inverse title restores the original title on the same property ID. Synthetic whole-state reversal passes; live mirror-before snapshots and actual isolated schema-conversion readback are still required. The private104-rowcombinedmanifestisNOTexecutable,usespendingIDsfornewcolumns,andexplicitlyblocksexactmirrorrollbackwithoutabackup.
7. Permanent tenant/amenity listing-ID exceptions removed from the reusable normalizer. Private one-time correction entries require exact full before and corrected-after hashes; changed owner choices refuse the old correction.

All changes remain staged and require independent retest. Independent24c660freviewclosedreportedstageddefects1/2/3/4/7andunsafe-takeoverpartof5. Operator reconciliation is newly staged, not independently closed.

## Later evidence checkpoint

Native isolated one-row schema forward/reverse rehearsal independently passed:
eight rich-text columns converted to selects with stable IDs; title renamed on
same ID; four additions written/read and then removed only in the synthetic DB.
Original nine schema definitions and complete typed property JSON compare equal,
including title/bachelor whitespace. Screenshots inspected. Preserved raw evidence
and reconstructed call index sent privately. This is not a full104mirrorrollback.

Deletion then restoration to a previously completed membership now has a SQL
regression: restoration creates a new job at offset0withthecorrectsavedorder.
Hash-bound reviewed corrections are migration-only and idempotent, not a
consumed-once ledger. See UNCERTAIN-EFFECT-RECOVERY.md for fail-closed recovery.

A later local checkpoint persists separate recovery incidents/readback/remaining
patch/decision/state hash. Actual title-job recovery now resumes through the
repository/Edge/SQL ports and checkpoints to completion. Operational incident
routing, named operator/admin and a production blocked-state view remain open.
The service role is trusted privileged code, not a hostile-worker boundary.
Real mirror-before backup is now captured privately (104active,9tombstoned),
reconciles with Notion on all business fields after numeric/blank normalization,
and is included in104exactcombinedforward/reversemodelchecks. This still is not
an executable production manifest or full104nativecutover/reversalrehearsal.

Healthy concurrent claims during an unexpired effect now return ordinary busy,
not needs_recovery. Worker/title regression tests cover this and normal effect
completion closes matching incidents. A narrow documented saved503receiptpath
is staged/tested without PATCH retry; unknown503/504/transportlossremainsblocked.
