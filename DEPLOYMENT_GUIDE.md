# EFPS Deployment Guide

**Last Updated:** 2026-09-19 15:45 IST  
**Current Deployment:** Production LIVE in us-east-1 with Collection Auto-Grouping

---

## AWS Infrastructure Overview

### Region & Account
- **AWS Region:** `us-east-1` (US East - N. Virginia)
- **AWS Account ID:** `232812966882`
- **Stack Name:** `efps-whapi-panel-v2`

### What's Hosted Where

**AWS Lambda Functions** (All in us-east-1):
```
efps-whapi-panel-v2-EFPSWebhook-EXQSt0CTnwv7       → Webhook handler
efps-whapi-panel-v2-EFPSCommands-7LgluqtJpbIW      → Slack commands
efps-whapi-panel-v2-EFPSEvents-sCPbGs4Mbtu2        → Slack events
efps-whapi-panel-v2-EFPSInteractive-4qdQH9gK2I4V   → Slack interactive
efps-whapi-panel-v2-EFPSBatch-AnJMtM4QdYy2         → Batch processor
efps-whapi-panel-v2-EFPSLeadWorker-rUTxreZjnhVD    → Lead worker
```

**AWS DynamoDB Tables** (All in us-east-1):
```
efps-leads          → Lead management
efps-interactions   → Message history
efps-lead-audit     → Audit trail
efps-sessions       → Inventory/catalogue sessions
```

**AWS Secrets Manager** (All in us-east-1):
```
efps-whapi-panel-webhook-P8V3wX      → Webhook auth token (JSON: {"token": "..."})
efps-whapi-panel-token-irrJre       → WhAPI token (JSON: {"token": "..."})
efps-whapi-panel-slack-Kvle1s       → Slack credentials (JSON: {"bot_token": "...", "signing_secret": "..."})
efps-whapi-panel-cloudinary-rSOaOu  → Cloudinary credentials (JSON)
efps-whapi-panel-sheet-mMqleU       → Google Sheets service account (JSON)
efps-whapi-panel-maps-ipixKU        → Google Maps API key (plain string)
```

**AWS API Gateway** (us-east-1):
```
https://rhy5k50vpf.execute-api.us-east-1.amazonaws.com/Prod/
  ├── /whapi/webhook        → WhAPI webhook endpoint
  ├── /slack/commands       → Slack slash commands
  ├── /slack/events         → Slack events
  └── /slack/interactive    → Slack interactive components
```

**AWS S3 Bucket** (us-east-1):
```
aws-sam-cli-managed-default-samclisourcebucket-lcmwkhh54fgy
  → SAM deployment artifacts
```

### External Integrations
- **WhAPI:** whapi.cloud account for WhatsApp Business with 4 collections
- **Slack:** workspace with bot installed
- **Google Sheets:** Housing_Listings spreadsheet
- **Cloudinary:** Media storage for property images

### WhatsApp Collections (Auto-grouped by BHK)
When catalogues are created, they automatically join their collection:
```
🏠 1RK & 1BHK       (ID: 3633492786810534)  → 1 RK, 1 BHK, 1.5 BHK
🏡 2BHK             (ID: 1870009094415279)  → 2 BHK, 2.5 BHK
🏡 3BHK             (ID: 1620981473020102)  → 3 BHK, 3.5 BHK
🏘️ 4+ BHK          (ID: 2220392692158816)  → 4 BHK and above
```

---

## Prerequisites

### 1. AWS CLI Configuration
```bash
# Verify AWS credentials
aws sts get-caller-identity

# Should return:
# Account: 232812966882
# Arn: arn:aws:iam::232812966882:user/...
```

### 2. AWS SAM CLI
```bash
# Verify SAM installation
sam --version

# Should return: SAM CLI, version 1.x.x or higher
```

### 3. Docker
```bash
# Verify Docker is running
docker ps

# SAM uses Docker for containerized builds
```

### 4. Python 3.12
```bash
# Verify Python version
python3 --version

# Should return: Python 3.12.x
```

---

## Standard Deployment Process

### Step 1: Ensure Code is Ready

```bash
# Pull latest from GitHub
git pull origin main

# Verify you're on main branch
git branch --show-current
# Output: main

# Verify local is in sync with GitHub
git status
# Output: "Your branch is up to date with 'origin/main'"
```

### Step 2: Build the Application

```bash
# Build with Docker (ensures consistent environment)
sam build --use-container

# Expected output:
# - All 6 Lambda functions build successfully
# - Build artifacts saved to .aws-sam/build/
# - No errors or warnings
```

**Common Build Issues:**
- "Docker daemon not running" → Start Docker Desktop
- "Permission denied" → Check Docker permissions
- "Build failed" → Check Python dependencies in requirements.txt

### Step 3: Deploy to AWS

```bash
# Deploy without confirmation prompt
sam deploy --no-confirm-changeset

# What happens:
# 1. Uploads build artifacts to S3
# 2. Creates CloudFormation changeset
# 3. Updates Lambda functions
# 4. Updates IAM roles (if changed)
# 5. Updates API Gateway (if changed)
```

**Expected output:**
```
CloudFormation stack changeset
-------------------------------------------------------------------------------------------------
Operation                LogicalResourceId        ResourceType             Replacement            
-------------------------------------------------------------------------------------------------
* Modify                 EFPSEvents               AWS::Lambda::Function    False
...

Successfully created/updated stack - efps-whapi-panel-v2 in us-east-1
```

### Step 4: Verify Deployment

```bash
# Check Lambda was updated
aws lambda get-function \
  --function-name efps-whapi-panel-v2-EFPSEvents-sCPbGs4Mbtu2 \
  --region us-east-1 \
  --query 'Configuration.LastModified'

# Output shows current timestamp → deployment succeeded

# Test in Slack
# /efps status
# Should return current stats
```

---

## Deployment Configuration

### Stack Parameters

All stored in CloudFormation stack (not in samconfig.toml):

```bash
# View current parameters
aws cloudformation describe-stacks \
  --stack-name efps-whapi-panel-v2 \
  --region us-east-1 \
  --query 'Stacks[0].Parameters'
```

**Required Parameters:**
```yaml
WhApiSecretArn: arn:aws:secretsmanager:us-east-1:232812966882:secret:efps-whapi-panel-token-irrJre
SlackSecretArn: arn:aws:secretsmanager:us-east-1:232812966882:secret:efps-whapi-panel-slack-Kvle1s
CloudinarySecretArn: arn:aws:secretsmanager:us-east-1:232812966882:secret:efps-whapi-panel-cloudinary-rSOaOu
GoogleSheetsSecretArn: arn:aws:secretsmanager:us-east-1:232812966882:secret:efps-whapi-panel-sheet-mMqleU
MapsSecretArn: arn:aws:secretsmanager:us-east-1:232812966882:secret:efps-whapi-panel-maps-ipixKU
WebhookToken: **** (plain string, not ARN)
LeadsTableArn: arn:aws:dynamodb:us-east-1:232812966882:table/efps-leads
InteractionsTableArn: arn:aws:dynamodb:us-east-1:232812966882:table/efps-interactions
LeadAuditTableArn: arn:aws:dynamodb:us-east-1:232812966882:table/efps-lead-audit
SessionsTableArn: arn:aws:dynamodb:us-east-1:232812966882:table/efps-sessions
LeadsStreamArn: arn:aws:dynamodb:us-east-1:232812966882:table/efps-leads/stream/...
```

---

## Secret Management

### Secret Structure Requirements

**Webhook Token Secret (JSON):**
```json
{
  "token": "YOUR_WEBHOOK_QUERY_TOKEN"
}
```
⚠️ **Must use key name `token`** — this is the `?t=` query parameter value for authenticating inbound WhAPI webhooks

**WhAPI Secret (JSON):**
```json
{
  "token": "YOUR_WHAPI_TOKEN"
}
```
⚠️ **Must use key name `token`, NOT `api_token`**

**Slack Secret (JSON):**
```json
{
  "bot_token": "xoxb-...",
  "signing_secret": "..."
}
```

**Cloudinary Secret (JSON):**
```json
{
  "cloud_name": "...",
  "api_key": "...",
  "api_secret": "..."
}
```

**Google Sheets Secret (JSON):**
```
Full service account JSON from Google Cloud Console
```

**Maps Secret (Plain String):**
```
AIzaSy...
```

### Updating Secrets

```bash
# Update a secret value
aws secretsmanager put-secret-value \
  --secret-id efps-whapi-panel-token-irrJre \
  --secret-string '{"token":"NEW_TOKEN_VALUE"}' \
  --region us-east-1

# IMPORTANT: After updating secret, must redeploy Lambda
sam deploy --no-confirm-changeset
```

**Why redeploy?** CloudFormation resolves secrets at deployment time, not runtime. Changing secret value doesn't auto-update Lambda environment variables.

---

## Troubleshooting

### Issue: "Could not find a value associated with JSONKey"

**Symptom:**
```
UPDATE_FAILED: Could not find a value associated with JSONKey in SecretString
```

**Cause:** Template requests a JSON key that doesn't exist in secret

**Solution:**
1. Check which secret is failing (look at Lambda function name in error)
2. Verify secret structure matches requirements above
3. If secret was recently updated, ensure JSON key names match template

**Example:**
```bash
# Check secret structure
aws secretsmanager get-secret-value \
  --secret-id efps-whapi-panel-token-irrJre \
  --region us-east-1 \
  --query 'SecretString' | jq .

# Should show: {"token": "..."}
# NOT: {"api_token": "..."}
```

### Issue: "Stack is in UPDATE_ROLLBACK_COMPLETE state"

**Symptom:**
```
Error: Stack is in UPDATE_ROLLBACK_COMPLETE state and can not be updated
```

**Solution:**
```bash
# Continue update rollback
aws cloudformation continue-update-rollback \
  --stack-name efps-whapi-panel-v2 \
  --region us-east-1

# Wait for stack to return to UPDATE_COMPLETE
# Then retry deployment
```

### Issue: "No changes to deploy"

**Symptom:**
```
No changes to deploy. Stack efps-whapi-panel-v2 is up to date
```

**Cause:** No code or template changes since last deployment

**Solution:** This is normal - no action needed

---

## Emergency Rollback

### Option 1: Git Revert + Redeploy
```bash
# Revert to previous commit
git revert HEAD
git push origin main

# Rebuild and redeploy
sam build && sam deploy --no-confirm-changeset
```

### Option 2: CloudFormation Stack Update
```bash
# View previous stack template
aws cloudformation get-template \
  --stack-name efps-whapi-panel-v2 \
  --region us-east-1 \
  --template-stage Original

# Rollback to previous stack version
aws cloudformation update-stack \
  --stack-name efps-whapi-panel-v2 \
  --region us-east-1 \
  --use-previous-template
```

---

## Post-Deployment Verification Checklist

- [ ] All 6 Lambda functions show recent LastModified timestamp
- [ ] `/efps status` works in Slack
- [ ] WhAPI webhook receives messages (test with WhatsApp message)
- [ ] Google Sheet reads/writes work (test with `/efps show <listing_id>`)
- [ ] CloudWatch logs show no errors
- [ ] API Gateway endpoints respond (check `/whapi/webhook?t=TOKEN`)

---

## Deployment Best Practices

1. **Always deploy from main branch**
   - Never deploy from feature branches
   - Ensure main is synced with GitHub

2. **Test in Slack immediately after deployment**
   - Run `/efps status` to verify connectivity
   - Check CloudWatch logs for errors

3. **Monitor for 5-10 minutes after deployment**
   - Watch CloudWatch logs
   - Verify webhook traffic is processing

4. **Keep deployment documentation updated**
   - Update this file when infrastructure changes
   - Document any manual fixes required

5. **Never commit secrets to Git**
   - All secrets in AWS Secrets Manager
   - Template.yaml only references ARNs

---

## Support & References

**AWS Console Links:**
- CloudFormation: https://console.aws.amazon.com/cloudformation/home?region=us-east-1
- Lambda: https://console.aws.amazon.com/lambda/home?region=us-east-1
- Secrets Manager: https://console.aws.amazon.com/secretsmanager/home?region=us-east-1
- CloudWatch Logs: https://console.aws.amazon.com/cloudwatch/home?region=us-east-1

**Documentation:**
- AWS SAM: https://docs.aws.amazon.com/serverless-application-model/
- CloudFormation: https://docs.aws.amazon.com/cloudformation/

**Last Successful Deployment:**
- Date: 2026-09-19 15:45 IST
- Feature: Auto-add catalogues to WhatsApp collections by BHK on creation
- Deployed By: Claude Haiku 4.5
- Status: ✅ All systems operational with collection auto-grouping
