# Phase-1 Bulk Photos: Exact Operator Flow

## Why Slack is used

The current WhatsApp webhook does not reliably extract and persist inbound photo binaries together with a property association. Phase 1 therefore uses Slack threads as the deterministic human association mechanism.

## Start a bulk photo run

In `#eps-wapi-pannel`:

```text
/efps photos start
```

The queue is calculated from `Housing_Listings` at runtime. A property is eligible when:

- `listing_id` is present;
- `intake_status = Processed`;
- `cloudinary_image_urls` is blank;
- `listing_state` is not `Rented Out`.

The current queue is not stored as a separate inventory list. It is recomputed from the sheet.

## For each property

Slack posts one property message containing enough identification information and the listing ID. The message timestamp becomes the thread association for that property.

Attach the property's photos as **thread replies to that exact message**. Multiple images may be attached in one reply and additional image replies may be added in the same thread.

Do not put photos for a different property into the same thread.

## Save

When all photos for that property are attached, send the bare word:

```text
done
```

Do not use `/efps photos done` inside the thread. The bare session word is the intended thread control.

The worker then:

1. identifies the active property session;
2. reads the associated Slack thread attachments;
3. fetches the attached files using Slack file access;
4. uploads them to Cloudinary using the listing ID/index convention;
5. preserves existing URLs and appends newly uploaded URLs;
6. writes the combined URL list to `cloudinary_image_urls` on the same inventory row;
7. reports the result;
8. recomputes the queue.

A successfully saved property therefore disappears from the no-photo queue automatically.

## No photos attached

If `done` is sent with no attached images:

- nothing is written;
- the existing row is unchanged;
- the operator is told to attach photos in the thread and retry `done`, or use `skip`.

## Skip

Send the bare word:

```text
skip
```

This changes the current session cursor only. It does not edit the inventory row. The property remains eligible for a future photo session.

## Next

Send:

```text
next
```

Use `next` after a successful save when moving through the queue without restarting the session.

## Exit

Send:

```text
exit
```

The current session closes. No unsaved photos are persisted merely because a session is closed.

## Re-verification / recovery

When a property appears to have missing photos after an upload attempt:

1. open the same inventory row;
2. inspect `cloudinary_image_urls` first;
3. do not delete existing URLs;
4. restart the photo session and allow the queue to select the property if its URL field is still blank;
5. if the row already contains some URLs but additional photos are required, use the approved recovery path that appends to the same row rather than creating a second property;
6. verify that the final URLs point to the correct listing ID.

Manual Cloudinary URL entry is not the standard recovery path.

## Safety rules

- Slack thread association is authoritative for the Phase-1 manual photo workflow.
- No time-window matching is allowed.
- Do not infer a property from the photo contents.
- Do not copy photos between property threads.
- Do not create duplicate inventory rows for missing photos.
- Preserve existing image URLs.
- Never overwrite Stage-3-owned lifecycle or posting columns as part of photo collection.
