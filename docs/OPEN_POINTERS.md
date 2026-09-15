# Open Pointers

This is the canonical list of unresolved decisions and verified unknowns for the current live-system migration and Inventory Phase-1 boundary. Unknowns are never guessed.

## Repository remediation closed

- Inventory Stage-1 webhook import context was corrected without changing canonical Stage-2 processing.
- Lead worker import-path wiring was corrected without duplicating Lead modules at repository root.
- Slack signing-secret resolution now supports `SLACK_SIGNING_SECRET` in AWS and local Keychain fallback.
- Slack Events `event_id` deduplication now uses an atomic claim in the existing `efps-sessions` table.
- Interactive/event operational handlers now report unexpected failures through the shared Slack bug/crash surface and return controlled responses.
- Lead inbound media references are persisted through the existing interaction `media_urls` field and `has_media` flag.
- Lead card deleted-message recovery was restored: a failed update falls back to posting a replacement and saving its timestamp.
- The public Slack Events `internal=save_photos` authentication bypass was removed.
- The canonical WhAPI client now sends `User-Agent: EFPS-Inventory-Phase1/1.0` centrally.
- Root SAM dependency packaging is defined through `requirements.txt` for the third-party libraries directly used by the destination runtime.
- `docs/MIGRATION_LIVE_SYSTEM_MAP_20260916.md` is registered in `DOCUMENT_MAP.md`.

## Runtime verification required

- Target AWS/SAM deployment of the remediation commit remains `NOT VERIFIED` in this execution environment.
- Target Lambda handler imports and packaged third-party dependencies remain `NOT VERIFIED` at deployed runtime.
- Slack app installation, bot membership, command registration, endpoint configuration, AWS signature verification, and live Slack API behavior remain `NOT VERIFIED`.
- WhAPI destination webhook URL/token relationship and live client compatibility remain `NOT VERIFIED`.
- Destination synthetic webhook delivery and end-to-end Lead/Inventory routing remain `NOT VERIFIED`.
- Google Sheets target credential access and a non-destructive destination read remain `NOT VERIFIED`.
- Production Sheet write behavior remains intentionally untested in this remediation session.
- Old runtime zero-traffic/cutover confirmation remains `NOT VERIFIED`; the old live system must not yet be retired.

## Deferred by boundary

- Production WhAPI media downloads and direct Cloudinary association beyond the currently authorized temporary photo workflow.
- Inventory lifecycle/locking implementation beyond the protected-column boundary.
- Future Meta Catalogue, Housing Portal, website publishing, Society Approvals, and other downstream integrations until explicitly authorized.

## Governance

When a pointer is resolved, update this document and the affected architecture/contracts/handoff in the same implementation session. Do not remove a pointer merely because it cannot be verified locally.
