# Project Rules

These are standing engineering and automation rules for EFPS Internal Automations.

## Truth and scope

1. Apply `CORE_STEERING.md` before every response or action.
2. Establish repository and runtime truth before implementation; never guess or silently infer missing facts.
3. Use the smallest safe change that satisfies the verified requirement.
4. Do not modify unrelated modules, shared capabilities, infrastructure, or documentation.
5. Preserve explicit business ownership boundaries.

## Architecture

- `modules/` owns EFPS business capabilities and business decisions.
- `shared/` owns reusable technical capabilities and must remain business-neutral.
- Shared services provide capabilities; modules decide when and why they are used.
- Established shared capability boundaries are `shared/cloudinary/`, `shared/google_sheets/`, and `shared/whatsapp_whapi/`.
- A shared boundary may exist before every runtime feature is complete; status must be explicit and verified.

## Cloudinary

`shared/cloudinary/` provides technical media storage/upload capabilities. Business modules decide which media is stored and why. The verified legacy reference used deterministic listing-derived property paths and a separate lead/enquiry namespace. fileciteturn228file0L2-L2

## WhatsApp / WhAPI

`shared/whatsapp_whapi/` must retain an explicit live-traffic gate. No token check, quota check, health ping, fetch, send, or other live WhAPI network operation should happen without the deliberate runtime approval mechanism derived from the verified legacy guard. fileciteturn223file0L2-L2

## Documentation

- `docs/` is the canonical home for permanent business and system knowledge.
- Every implementation must review every maintained root document and every document inside `docs/` against resulting repository reality.
- Update every affected document in the same work session.
- Update `HANDOFF.md` whenever current working state changes.
- Use `DOCUMENT_UPDATE_MATRIX.md` and `DOCUMENT_GOVERNANCE.md` for document ownership and routing.
- Do not create duplicate authoritative documents.

## Security

- Never commit secrets, API tokens, passwords, private keys, or production authentication material.
- Do not expose production data merely to simplify implementation.
- Document verified resource identifiers without storing secret values.
- Cloudinary configuration/credentials, Google service-account credentials, and WhAPI tokens must remain outside version control.

## Validation

A change is complete only when the applicable implementation, verification, validation, and documentation checks are complete and there are no known contradictions with repository truth.
