# Slack Property Verification

## Purpose

This is the human-in-the-loop path for properties that cannot safely pass deterministic validation without operator input. It is property verification, not society approval.

## Start

From the property verification channel, run:

`/efps verify start`

The session selects the next row requiring human review and posts the property/questions in a thread.

## Fields asked by the legacy verification session

The legacy workflow asks, as applicable:

- `society_name`
- `locality`
- `pincode`
- `BHK`
- `bathrooms`
- `total_floors`
- `monthly_rent`
- `security_deposit`
- `built_up_area`
- `floor_number`
- `property_subtype`
- `society_amenities`
- `internal_property_type`
- `landmark`
- `furnish_type`
- `preferred_tenant_type`
- `bachelor_preference`

The new repository must use the current 48-column contract and its verified allowed values. Do not invent missing vocabulary.

## Thread workflow

1. Start with `/efps verify start` from the channel view.
2. Answer the questions in the property's thread.
3. Use explicit skip tokens (`skip`, `-`, `none`, `na`) when the operator does not have an answer, where the owning verification implementation permits them.
4. Reply with bare `submit` when the answers are complete.
5. EFPS writes nonblank answers to the same property row.
6. Deterministic dependencies are re-run.
7. Canonical validation runs again.
8. The row is moved to the appropriate post-verification state according to the current inventory contract.
9. Continue with `next`, `skip`, or `exit` as required.

## Important boundaries

Verification must not create a second property record. It corrects the canonical row.

Verification must not bypass Maps ownership for `locality`, `city`, `pincode`, or `google_maps_url`.

Verification must not directly modify system-owned or downstream-owned fields.

Verification must not create or update a separate society-learning/approval table. That behavior belonged to obsolete legacy material and is explicitly excluded from the new repository.

## Batch relationship

The intended lifecycle is:

`WhatsApp intake → Stage 1 raw row → Stage 2 deterministic processing → validation → Needs Review when required → Slack human verification → deterministic re-normalization → validation → downstream readiness`

Slack is the operator interface; the inventory sheet/canonical row remains the system record.

## Recovery

If a verification session appears stuck:

1. Identify the listing ID and exact thread.
2. Re-read the canonical row.
3. Determine whether the row still needs review.
4. Confirm the session state and thread timestamp.
5. Continue in the same thread when possible.
6. Never create a new listing to work around a stuck session.
7. After submission, verify the row rather than relying only on the Slack response.
