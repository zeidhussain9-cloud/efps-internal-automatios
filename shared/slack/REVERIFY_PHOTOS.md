# Bulk Photo Collection and Re-verification

## Why this workflow exists

Current Stage 1 webhook intake does not extract and persist inbound photo binaries into the inventory row. Until direct media extraction/association is implemented, Slack is the controlled human-assisted photo path.

This is a temporary operational design, not a statement that webhook media cannot be supported later.

## Queue eligibility

The legacy photo queue is derived fresh from the inventory sheet. A property is eligible when:

- `listing_id` exists.
- `intake_status = Processed`.
- `cloudinary_image_urls` is blank.
- `listing_state != Rented Out`.

The queue is recalculated from the sheet rather than being a permanently stored list. Session-level skips are remembered only for the current session.

## Bulk operating procedure

1. Open `#eps-wapi-pannel`.
2. Run `/efps photos start`.
3. EFPS selects the first eligible property and posts its property message.
4. The session records the operator, listing ID and Slack thread timestamp.
5. Open/reply to **that exact property thread**.
6. Attach all photos belonging to that property to the thread. Multiple photos may be supplied in one session.
7. Reply with the bare word `done`.
8. The photo-save worker is dispatched asynchronously.
9. The worker reads the same property/session context and uploads the attachments to Cloudinary.
10. Existing `cloudinary_image_urls` are preserved; new URLs are appended rather than replacing existing images.
11. The worker writes the resulting URL list back to the **same inventory row**.
12. Recalculate the queue. A successfully completed property should no longer qualify because its Cloudinary URL field is populated.
13. Continue with `/efps photos next` or the session's `next` behavior.
14. Use `skip` when the property cannot be completed now; use `exit` to stop the session.

## Important thread rule

Do not start another property session before the current property is complete or explicitly skipped. The thread timestamp is the association key between the Slack property message and its uploaded photos.

Slack does not support running the `/efps` slash command from inside a thread. Therefore:

- Start the session from the channel view.
- In the property thread, type `done`, `next`, `skip`, or `exit` as the applicable bare control word.

## Photo re-verification / recovery checklist

Use this when an operator believes photos were added but the row still has no URLs.

1. Identify the exact `listing_id`.
2. Read the canonical row; do not create a duplicate row.
3. Confirm the property still satisfies the photo queue rule or determine why it does not.
4. Locate the exact Slack property thread used for the session.
5. Confirm the attachments are actually present in that thread.
6. Confirm the save action was triggered with `done`.
7. Check whether the events/photo worker ran.
8. Check Cloudinary upload results.
9. Confirm the same row was updated and existing URLs were preserved.
10. If upload partially succeeded, recover by appending only missing images; never blindly replace the whole URL list.
11. Re-read the row and confirm the queue state.

## What not to do

- Do not manually type Cloudinary URLs into ordinary operator notes as the normal workflow.
- Do not attach photos to a different property's thread.
- Do not use a new listing ID merely because a photo save failed.
- Do not overwrite existing Cloudinary URLs during recovery.
- Do not assume a Slack `done` acknowledgement proves Cloudinary persistence; verify the row.
- Do not treat Slack as the canonical inventory store.

## Media timing constraint

The legacy WhAPI client records that inbound media URLs can expire, so any future direct-webhook media implementation must fetch media promptly. The current Slack fallback avoids relying on an expired WhatsApp media URL by using the Slack thread attachment as the operator collection point.

## Exit criteria for this temporary design

This workflow can eventually be replaced/augmented when Stage 1 reliably receives, fetches, associates, stores, and validates webhook media. Until that is verified in production, Slack photo collection remains the documented operational path.
