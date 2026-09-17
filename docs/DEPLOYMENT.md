# EFPS SAM Deployment Contract

This document is the repository-side deployment contract for the canonical `main` branch. It does not claim that AWS deployment, third-party integrations, or production cutover have been completed.

## Source of truth

- Repository: `zeidhussain9-cloud/efps-internal-automatios`
- Canonical branch: `main`
- SAM template: `template.yaml`
- Runtime credential resolution: AWS Secrets Manager dynamic references in the SAM function environment.
- Business rules: V10 deterministic control workbook; this document only defines deployment mechanics.

## Runtime credential inputs

`template.yaml` requires existing AWS Secrets Manager ARNs as deployment parameters. Secret values are never committed to GitHub.

| SAM parameter | Environment variable(s) | Required secret shape |
|---|---|---|
| `WhApiSecretArn` | `WHAPI_API_TOKEN` | JSON object with `token` |
| `SlackSecretArn` | `SLACK_BOT_TOKEN`, `SLACK_SIGNING_SECRET` | JSON object with `bot_token` and `signing_secret` |
| `GoogleSheetsSecretArn` | `GOOGLE_SERVICE_ACCOUNT_JSON` | Complete Google service-account JSON as `SecretString` |
| `CloudinarySecretArn` | `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET` | JSON object with `cloud_name`, `api_key`, and `api_secret` |
| `MapsSecretArn` | `GOOGLE_MAPS_API_KEY` | API key as `SecretString` |

The existing `WebhookToken` parameter remains a `NoEcho` deployment parameter because the current webhook authorization code consumes `EFPS_WEBHOOK_TOKEN` directly.

The repository does not create, rotate, or overwrite these secrets. The AWS deployment operator must supply ARNs for existing secrets and ensure their shapes match this contract. This is intentionally separate from proving that the referenced secrets currently exist in AWS.

AWS CloudFormation supports versionless Secrets Manager dynamic references and resolves them when the resource is created or updated. Updating a secret value alone does not update an existing Lambda environment value; a stack/resource update is required when the resolved environment value must change. See the AWS documentation for the exact dynamic-reference semantics. urlCloudFormation Secrets Manager dynamic referenceshttps://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/dynamic-references-secretsmanager.html

## Deployment validation gate

Every change that can affect the SAM application must pass the dedicated `SAM deployment validation` workflow before it is considered repository-ready for deployment.

The workflow performs:

1. `sam validate --lint` against `template.yaml`.
2. A clean `sam build --use-container` using the declared Python 3.12 runtime.
3. Validation of the generated `.aws-sam/build/template.yaml` with `sam validate --lint`.
4. Python bytecode compilation of repository runtime modules.
5. A dependency-presence check against the built Lambda artifacts for the externally imported runtime packages.

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
