# EFPS Internal Automations — Current Handoff

## Current state

The authorized implementation target is **Inventory Management Phase 1**. The workflow has three top-level stages: Stage 1 Initial/Webhook, Stage 2 Deterministic Extraction/Property Processing, and Stage 3 downstream boundary reserved for later consumers.

## Stage-2 implementation truth

- `extract.py` discovers deterministic source facts from completed `raw_message_text`.
- `source_segments.py` is the canonical source-message boundary parser for concatenated WhatsApp inventory messages.
- `field_resolution.py` is the canonical candidate-resolution layer for BHK, maintenance, and internal property type.
- `pipeline.py` is the authoritative deterministic processing boundary and passes resolved internal property type explicitly into normalization.
- `normalize.py` consumes canonical resolved property type and must not independently reclassify it.
- BHK preserves decimals and later explicit corrections.
- Maintenance requires maintenance-specific context, normalizes K/lakh units, independently evaluates inclusion, and preserves source qualifiers such as `+ Water`.
- Internal property type has exactly three business values: Gated Community, Semi Gated, and Standalone. Explicit negative gating is authoritative against generic positive wording; absence of authoritative evidence remains unresolved and does not prove Standalone.
- Numeric balcony extraction covers explicit singular/plural source forms, including bare `Balcony` as one balcony.
- Explicit no-pet source wording is authoritative during final normalization.
- `📍 Landmark:` followed only by a Maps URL remains a blank landmark; the URL belongs to `google_maps_url`, and landmark never inherits locality.
- Existing Sheet Stage-2 values are never deterministic extraction input.
- `Needs Review` is governed by `docs/NEEDS_REVIEW_CONTRACT.md`; non-blocking field gaps do not become property-processing blockers by themselves, but they must still remain deterministic and contract-valid.

## Canonical dependency contract

```text
internal_property_type -> society_amenities
internal_property_type -> covered_parking (blank-only default)
furnish_type -> flat_furnishings (blank-only default)
preferred_tenant_type -> bachelor_preference
maintenance -> maintenance_included
built_up_area -> carpet_area (blank-only fallback)
monthly_rent -> security_deposit (month-based source form)
```

For tenant eligibility:

- `preferred_tenant_type` has exactly two live Sheet values: `Family` and `Open For All`.
- `Family` -> `bachelor_preference` is blank.
- `Open For All` -> `bachelor_preference` defaults exactly to the Sheet dropdown value `Open for both`.
- Explicit valid source evidence for `Female Only ` or `Male Only` overrides the default.
- `Female Only ` includes the intentional trailing space present in the live Sheet dropdown and that exact value is the canonical contract.

## Audit findings fixed in this work

The repository-wide audit found and corrected stale or contradictory repository truth in the following areas:

1. The production projection gate previously stripped the exact trailing space from `bachelor_preference` and hardcoded a trimmed vocabulary. It now compares the exact live values directly from `shared/google_sheets/schema.py`.
2. `landmark` in the schema incorrectly declared a locality dependency even though the implementation explicitly forbids locality inheritance. The dependency metadata is now empty and aligned with runtime behavior.
3. Inventory source-extraction and inventory README documentation previously described a Standalone fallback when property-type evidence was absent. The canonical rule is now consistently documented as unresolved/blank rather than fabricated Standalone.
4. The dated deterministic review and `OPEN_POINTERS.md` contained stale intermediate RED/current-failure status. They now describe the final hardening state and retain unresolved items only where runtime verification is genuinely still required.
5. Root AI guidance was stale about the number of established shared capability boundaries. The current repository inventory is six: Cloudinary, Credentials, Google Maps, Google Sheets, Slack, and WhAPI.
6. A repository-wide read-only audit utility was added at `tools/repository_audit.py` and wired into Inventory Contract CI before the deterministic regression suite.

## Verification baseline before this audit

The last verified deterministic baseline on `main` (`df9ef879a570290f13fe2a300a90d950691d32b7`) had 78 passing regression tests, 25/25 read-only projection rows, 48/48 canonical fields, zero model errors, zero writes, and a 25/25 production projection contract gate. Those results were evidence for that commit only.

## Current audit branch

Branch `phase1-repository-audit-hardening` contains the audit hardening described above. Final acceptance requires the branch CI to pass, the changes to be merged to `main`, and the exact resulting `main` commit to be synchronized locally before any live deterministic extraction/write operation is started.

## Safety boundary

No production Sheet write is part of the repository audit or read-only projection gate. Live deterministic extraction for rows 2–26 is the next acceptance boundary after the audited commit is merged and synchronized. External Maps runtime verification and deterministic source projection remain separate boundaries.

No production credentials or secrets are part of this change set.
