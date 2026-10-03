# EFPS CRM — Current Verified State

> Verified 2026-10-03 18:35 IST. Repository candidate: `dd7ba3e94293181c620825433e5f2be8a71e91ff`.

## Runtime baseline

- Production branch: `crm-ui-dashboard`
- Current verified tree: `1bf9ebe11ed463a492fd131d69b1334ea6ab82a8`
- Render service: `srv-darsv560tbcc73cu4ip0`
- Production source: `+919148338801`
- Supabase: `qttcutwzehtskfcwxkwj`

## Database audit snapshot — 2026-10-03 12:34 UTC

- 186 leads
- 7,573 CRM messages
- 1,256 persisted webhook events
- 214 AI runs / 214 drafts
- 88 active inventory listings
- 1,905 inventory sync runs

## Post-deployment process evidence

- Webhooks: 729/729 processed; 0 failed; 0 pending; 0 event/message mismatches; 0 event/lead mismatches; 0 duplicate provider keys/fingerprints.
- Inventory: 372 sync runs; every audited run was 88 rows / 0 changed / 0 removed; 0 change-ledger rows since deployment.
- AI scheduler: 6 cycles; 24 leads selected; 14 AI runs completed; 3 deterministic updates; 0 AI failures; 0 scheduler failures; 14 drafts.

## Repository verification

- `npm run build`: PASS
- `npm test`: 102/102 PASS
- `npm run test:browser`: 1/1 PASS
- GitHub Actions: both CRM Synthetic CI and CRM UI Verification PASS on `dd7ba3e`.

## Hardening state

- OOC deterministic policy: implemented and regression-tested, but awaiting production deployment/runtime verification.
- D08 handoff: documented.
- Independent encrypted backup + isolated restore: external prerequisite, not yet evidenced.
- AWS least-privilege credential rotation: external IAM prerequisite, not yet evidenced.
- Automatic WhatsApp sending: disabled.

Use this document as the only current CRM runtime snapshot. Dated audit reports are historical evidence.