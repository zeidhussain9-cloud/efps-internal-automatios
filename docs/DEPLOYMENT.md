# EFPS SAM Deployment Contract

This document retains the historical SAM deployment contract. It is not the production deployment contract for the current CRM UI. Current CRM UI production deploys from `crm-ui-dashboard` to Render service `easyfind-crm-d01-d05`.

## Source of truth

- Repository: `zeidhussain9-cloud/efps-internal-automatios`
- Production/deployment branch: `crm-ui-dashboard` (Render auto-deploy); `main` is the reconciled release branch and must have the same tracked tree.
- SAM template: `template.yaml`
- Runtime credential resolution: AWS Secrets Manager dynamic references in the SAM function environment.
- Business rules: V10 deterministic control workbook; this document only defines deployment mechanics.

## Runtime credential inputs

`template.yaml` requires the existing AWS Secrets Manager ARNs as deployment parameters. The Notion intake is deployed as a separate isolated stack from `notion-intake-template.yaml`; it does not modify the existing WhAPI/CRM stack. Secret values are never committed to GitHub.

| SAM parameter | Environment variable(s) | Required secret shape |
|---|---|---|
| `WhApiSecretArn` | `WHAPI_API_TOKEN` | JSON object with `token` |
| `SlackSecretArn` | `SLACK_BOT_TOKEN`, `SLACK_SIGNING_SECRET` | JSON object with `bot_token` and `signing_secret` |
| `GoogleSheetsSecretArn` | `GOOGLE_SERVICE_ACCOUNT_JSON` | Complete Google service-account JSON as `SecretString` |
| `CloudinarySecretArn` | `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET` | JSON object with `cloud_name`, `api_key`, and `api_secret` |
| `MapsSecretArn` | `GOOGLE_MAPS_API_KEY` | API key as `SecretString` |


The existing `WebhookToken` parameter remains a `NoEcho` deployment parameter because the current webhook authorization code consumes `EFPS_WEBHOOK_TOKEN` directly. The isolated Notion Lambda uses the dedicated `NotionSecretArn` JSON secret: `api_token` for Notion API access and `webhook_secret` for the Notion Connection webhook verification token. The API token is retrieved from Secrets Manager at worker runtime rather than stored in Lambda environment variables. Neither value is stored in repository files.

The isolated Notion template requires only the Notion, Google Sheets, Cloudinary, and Maps secret ARNs; it has no DynamoDB parameter or DynamoDB IAM permission. The Lambda reads the secret values from Secrets Manager at runtime, so secret updates take effect without redeploying the stack. Secret values are not displayed or included in source control. The Notion inventory deployment reused existing secret ARNs and did not read, create, rotate, overwrite, or copy secret values. The status of existing raw photo/enrichment credentials is separate and was not validated in this rollout; do not change them as part of Notion deployment.

AWS CloudFormation supports versionless Secrets Manager dynamic references and resolves them when the resource is created or updated. Updating a secret value alone does not update an existing Lambda environment value; a stack/resource update is required when the resolved environment value must change. See the AWS documentation for the exact dynamic-reference semantics. urlCloudFormation Secrets Manager dynamic referenceshttps://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/dynamic-references-secretsmanager.html

## Deployment validation gate

Every change that can affect the SAM application must pass the dedicated `SAM deployment validation` workflow before it is considered repository-ready for deployment.

The workflow validates and builds both `template.yaml` (the existing shared stack) and `notion-intake-template.yaml` (the isolated Notion stack), validates each generated template, compiles Python runtime modules, and checks dependency packaging for each Lambda artifact set. Both deployments use the declared Python 3.12 runtime.

The workflow does **not** deploy AWS resources and does not require production secret values.

AWS SAM's build process is the packaging authority for Python Lambda dependencies: it reads the dependency manifest and places dependencies into the function build artifacts used for later testing, packaging, and deployment. urlAWS SAM build documentationhttps://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-using-build.html

## Deployment is not cutover

Passing repository validation means only that the committed SAM application is structurally valid and buildable. It does not establish:

- that the referenced Secrets Manager secrets exist or have the required values;
- that Slack, WhAPI, Google Sheets, Google Maps, or Cloudinary accept the credentials;
- that the deployed Lambda functions are running this commit;
- that production webhook traffic has been cut over; or
- that old runtime components have been retired.

Those are runtime verification gates and must be independently evidenced in AWS.

## AU / AV reserved-column rule

`Housing_Listings` remains a 48-column canonical grid, but `AU` (`source_group`) and `AV` (`inventory_locked`) are currently **reserved/dummy columns**.

The current repository contract is:

- AU must remain blank.
- AV must remain blank.
- Current inventory runtime code must not read, write, populate, or operate on AU/AV.
- Canonical active writes end at `AT`.
- A:AV representations may exist only where required to preserve the 48-field in-memory schema, with AU/AV represented as blank reserved positions.
- Any future use of AU/AV requires a separate explicit architecture decision; it must not be inferred from historical inventory-group or lock behavior.

This repository contract does not authorize or perform cleanup of historical live Sheet values in AU/AV. That is a separate controlled runtime/data operation.

## Required deployment evidence

Before production deployment is authorized, record the exact:

- SAM/CloudFormation stack name and region;
- deployed commit or artifact identifier;
- Lambda function versions/aliases, where applicable;
- supplied secret ARNs (identifiers only, never secret values);
- successful post-deployment runtime probes; and
- production traffic/cutover evidence.

No deployment or cutover is implied by this document.

The optional `EFPSNotionIntake` resource in the shared `template.yaml` is legacy and is not the deployed Notion path; do not enable it. Use only `notion-intake-template.yaml` for Notion intake.

## Isolated Notion intake verification — 2026-11-13 follow-up

- Target account/region: AWS `294417174793`, `ap-southeast-2`. Stack `efps-notion-property-intake` is `UPDATE_COMPLETE`; the existing secret ARN parameters were reused without displaying or changing secret values.
- Lambda `efps-notion-intake` is Active, `LastUpdateStatus=Successful`, `$LATEST`, `LastModified=2026-11-13T10:46:00Z`, CodeSha256 `+b4hBplC+2CGZag7HnpSDdmfwDqwuvHqtuSSLoGd/6c=`.
- The local Linux SAM dependency artifact was reused because Docker is unavailable. All declared packages were present, the updated Lambda source matched the local source hash, and the generated template passed SAM validation. The exact published commit also passed GitHub's fresh SAM container build and dependency packaging checks.
- Supabase `notion-inventory-state` is ACTIVE v6 with JWT verification enabled. Live checks confirmed a Notion edit and delete reached Supabase; restore did not produce an observed Lambda or Edge Function request. Earlier direct worker checks covered duplicate and restore-handler behavior, not webhook delivery.
- The test Supabase snapshot and intake event were removed. The test page was permanently deleted from Notion Trash after user approval. Supabase and the signed-in dashboard returned to 104 active listings (87 Available, 17 Rented Out).
- The signed-in dashboard displayed Notion-owned inventory and reflected the live Notion edit. The delete event also reached Supabase after about one minute. Restore did not trigger a new observed Lambda/Edge Function request, and the row remained soft-deleted; this remains an end-to-end blocker.
- Render was observed LIVE on commit `61688164b25f7a7a8e6df8248f91987a9c471ef6`; the release deployment ID was `dep-dbrev7ajnfac739de33g`. `/` and `/health` returned HTTP 200 in the earlier release check.

## Isolated Notion intake deployment — initial rollout, 2026-11-13

- Stack: `efps-notion-property-intake` (`ap-southeast-2`) — updated successfully to `UPDATE_COMPLETE` after confirming AWS account `294417174793`.
- Lambda: `efps-notion-intake` — Active, Python 3.12, 512 MB, 180-second timeout; `$LATEST`, `LastModified=2026-11-13T07:12:47Z`, CodeSha256 `BWKGDapY+LtrWskHtPWOLr0m8KcS0Ljp83aGkJFYvw4=`.
- API: `https://ko3771nvei.execute-api.ap-southeast-2.amazonaws.com/Prod/notion/intake`.
- Invalid `X-Notion-Signature` probe returned HTTP 401.
- SAM deployment reused the existing four secret ARN parameters and changed no secret values. The existing `efps-whapi-panel-v2` stack was not modified.
- The idempotent `_efps_notion_backfill` replay returned HTTP 200 and `accepted: 104`; Supabase confirms 104 processed intake events and 104 active `housing_notion` rows, with no Sheet-owned snapshot rows.
- `sam validate --template-file notion-intake-template.yaml --lint` and Python compilation passed. Docker/Finch/Podman were unavailable, so the current source was hash-matched into the previously built Linux dependency artifact for deployment. A fresh container SAM build did not run in this deployment turn.
- Raw Property Intake with photos may still depend on the existing Sheets, Cloudinary, and Maps runtime secret validity; those values were not inspected or changed during this turn. The direct Housing Listings mirror/backfill succeeded.
- The user confirms the existing Notion Connection webhook was verified and all eight Page events remain selected. The existing WhAPI stack and legacy listener remain untouched.
