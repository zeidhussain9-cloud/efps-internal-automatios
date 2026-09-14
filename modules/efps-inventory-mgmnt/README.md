# EFPS Inventory Management

Phase 1 owns the inventory business workflow from the dedicated two-number WhAPI listener through deterministic extraction, normalization, Google Maps resolution, validation, AI verification, and wording-only AI beautification.

## Property boundary
`NEW` opens a property session. Every text message until the next `NEW` belongs to that property. The closing `NEW` finalizes the session. Images are counted/recognized but their binary payloads are not downloaded in Phase 1.

## Raw source
All text messages are preserved in `raw_message_text`, in arrival order with timestamp/message-id metadata when available. Image payloads are never serialized into that field.

## Extraction source
Deterministic extraction reads the property's `raw_message_text` only. Existing canonical Sheet values are never used as extraction input during a replay.

## Maps
`shared/google_maps` is the reusable technical Maps capability. Inventory owns when/why a property requires Maps and consumes the normalized result for `locality`, `pincode`, and `google_maps_url`.

## Phase-1 boundary
No Cloudinary media download, inventory locking/lifecycle, duplicate governance, downstream Meta/Housing/website publishing, or Slack integration is implemented here.
