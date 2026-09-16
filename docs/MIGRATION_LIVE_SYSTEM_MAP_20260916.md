# EFPS Migration Live System Map — 2026-09-16

## Repository baseline

- Canonical `main`: `971fa444137c2c03f146db9abbafb8b694aceb3f`
- Reconciliation starting point: `36e9d0ba8566b820dd861b92858423edfd6ca8ed`
- Legacy migration branch: `62c976bf039c7c06dd8bb74803ece01c8b918dd8`
- Reconciliation is reconstructed from `main`; it is not a rebase of the migration branch.

## Approved Lead contracts

- `history::open` posts history as Slack messages/thread content; no `lead_history` modal.
- `stage::Lost` performs direct stage handling; no `lead_lost` modal or reason-submission flow.
- Audit records use UTC timestamps for storage and IST for presentation.
- Dashboard discovery uses Slack history; no dashboard state is persisted in `DDB_SESSIONS`.
- Newly created dashboards are not pinned.
- Digest uses Slack-history discovery/update/post behavior.
- Webhook authentication occurs before the live gate, matching legacy `modules/efps-whapi-panel/webhook_handler.py:lambda_handler` at commit `bd186c7c3418d633bca6766b1b92204c7a56d484`.

## Lead runtime path

```text
WhatsApp / WhAPI webhook
        |
        v
webhook_handler.py
        |
        +--> authenticate query token
        |
        +--> evaluate live gate
        |
        +--> Lead messages
                |
                v
        Lead record / DynamoDB
                |
                v
        lead_card.py / Slack
                |
                v
        leads_worker.py
                |
                v
        Slack-history dashboard digest
```

## Inventory boundary

```text
WhAPI
  -> listener detection
  -> Stage-1 session/raw intake
  -> canonical current-main Inventory Phase-1 / Stage-2 processing
```

The reconciliation Inventory adapters do not contain the prohibited legacy Stage-2 extraction, normalization, field-resolution, validation, or pipeline implementation.

Repository boundary: **CLEAN**.

Executable Stage-1 → canonical Stage-2 runtime path: **NOT VERIFIED**.

## Runtime/configuration verification remaining

- Lead worker compatibility.
- Production `EFPS_DDB_PREFIX` value.
- Slack credential payload schema.
- Webhook credential payload schema.
- Inventory Stage-1 → canonical Stage-2 executable path.
- Slack live installation/endpoint/signature verification.
- WhAPI live transport compatibility.

No AWS infrastructure, secrets, production configuration, or external systems are changed by this document.
