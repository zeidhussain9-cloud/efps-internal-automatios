# CloudFormation Deployment Block - 2026-09-19

**Status:** ✅ **RESOLVED** - Deployed successfully at 2026-09-19 13:23 IST

---

## RESOLUTION SUMMARY

**Root Cause:** Template requested secret key `api_token`, but secret only contained key `token`

**Solution:** Temporarily added both keys to secret → deployed successfully → removed temporary key

**Deployment Time:** 2026-09-19T04:58:47Z (13:23 IST)

See bottom of this document for complete resolution details.

---

## ORIGINAL INCIDENT REPORT

## Problem Summary

CloudFormation stack updates fail with:
```
UPDATE_FAILED: Could not find a value associated with JSONKey in SecretString
```

**Critical:** Even the EXACT template.yaml from the last successful deployment (commit 3e67e70, deployed 2026-09-19 01:18 UTC) now fails with this error.

## Impact

- **Code changes ARE committed** to GitHub (`main` branch)
- **Catalogue creation fix** (commit 5ae3474) cannot be deployed to AWS Lambda
- **Old code continues running** (CloudFormation auto-rollback protects production)

## Root Cause Analysis

### What Changed
- **Sept 19, 12:00-12:45 IST**: All CloudFormation deployment attempts started failing
- **External change**: Something outside our code changed (secrets structure, AWS permissions, or CloudFormation service)
- **NOT our code**: Reverting to known-working template.yaml still fails

### Evidence
1. Last successful deployment: `3e67e70` (2026-09-19 01:18 UTC)
2. All 6 Lambda functions fail simultaneously during UPDATE phase
3. Error occurs during environment variable resolution from Secrets Manager
4. All secrets validate correctly when read directly via AWS API
5. All secret ARNs in stack parameters are correct with 6-char suffixes

### Secrets Validated
| Secret | Status | Structure |
|--------|--------|-----------|
| WhAPI | ✅ Valid | JSON with `token` key |
| Slack | ✅ Valid | JSON with `bot_token`, `signing_secret` keys |
| Cloudinary | ✅ Valid | JSON with `cloud_name`, `api_key`, `api_secret` keys |
| GoogleSheets | ✅ Valid | JSON (service account) |
| Maps | ✅ Valid | Plain string (API key) |

## Pending Deployments

### Catalogue Creation Fix (5ae3474) 
**File:** `events_handler.py`

**Changes:**
1. **Skip guard**: Check if property already has `meta_catalog_id` before attempting creation
   ```python
   existing_meta_id = str(row.get("meta_catalog_id", "") or "").strip()
   if existing_meta_id:
       slack.post_message(channel, f"⏭️ `{listing_id}` already created...")
       pos += 1
       continue
   ```

2. **Error protection**: Re-read row before writing error_notes to prevent polluting success state
   ```python
   row_number_check, row_check = _row(sheet, listing_id)
   if row_check and not str(row_check.get("meta_catalog_id", "") or "").strip():
       sheet.write_range(...)  # Only write error if no meta_catalog_id
   ```

**Why This Matters:**
- Prevents duplicate catalogue creation attempts
- Stops error messages from overwriting successful catalogue records
- Fixes the looping/stuck behavior reported by user

### Template Fixes (4a15af0, 4541337)
**File:** `template.yaml`

**Changes:**
1. Reverted `EFPS_WEBHOOK_TOKEN` to plain `!Ref WebhookToken` (from broken Secrets Manager resolution)
2. Removed redundant `:AWSCURRENT` version stage from `WHAPI_API_TOKEN`

**Status:** These changes are correct but cannot be tested until CloudFormation works again.

## Workaround Attempts

### ❌ Direct Lambda Deployment
**Attempted:** Upload code to S3 → update Lambda directly via AWS CLI

**Failed:** Deployment package (145 MB) exceeds Lambda's 250MB unzipped limit
- `.aws-sam/build` contains ALL functions, not individual packages
- Cannot isolate single function for deployment

### ❌ Template Reversion
**Attempted:** Revert template.yaml to exact commit that worked before (3e67e70)

**Failed:** Same Secrets Manager error even with known-working template
- Confirms issue is EXTERNAL, not in our code

## How to Deploy When Fixed

### Normal Deployment (when CloudFormation works)
```bash
sam build
sam deploy --no-confirm-changeset
```

### Verification
```bash
# Check Lambda was updated
aws lambda get-function \
  --function-name efps-whapi-panel-v2-EFPSEvents-sCPbGs4Mbtu2 \
  --region us-east-1 \
  --query 'Configuration.LastModified'

# Test catalogue creation in Slack
/efps catalogue start
# Reply: go
```

## Investigation Steps for Next Agent

1. **Check if secrets were modified:**
   ```bash
   # Compare secret modification dates
   aws secretsmanager describe-secret \
     --secret-id arn:aws:secretsmanager:us-east-1:232812966882:secret:efps-whapi-panel-token-irrJre \
     --region us-east-1 \
     --query 'LastChangedDate'
   ```

2. **Check CloudFormation service health:**
   - AWS Service Health Dashboard
   - Check if Secrets Manager resolution is degraded

3. **Try minimal template update:**
   - Change only description field
   - See if issue is specific to Lambda updates

4. **Check IAM permissions:**
   - Verify caller has `secretsmanager:GetSecretValue`
   - Check if any org-level SCPs changed

## Temporary Manual Fix (if urgent)

**If catalogue fix is urgently needed before CloudFormation is fixed:**

1. Copy ONLY the catalogue flow code from `events_handler.py` lines 191-231
2. Use AWS Lambda console's inline editor
3. Find the EFPSEvents function → Code tab → Edit inline
4. Replace the catalogue `while` loop section
5. Deploy from console

**Warning:** This bypasses version control. Re-deploy via CloudFormation once fixed to sync state.

## Files in This Incident

| File | Status | Commit |
|------|--------|--------|
| `events_handler.py` | ✅ Fixed, committed | 5ae3474 |
| `template.yaml` | ⚠️ Reverted to 3e67e70 state | (uncommitted) |
| Google Sheet | ✅ Cleaned manually | N/A |

## Timeline

| Time (IST) | Event |
|------------|-------|
| 11:06 | First deployment attempt failed |
| 11:56 | Second attempt (after EFPS_WEBHOOK_TOKEN fix) failed |
| 12:13 | Third attempt (after removing :AWSCURRENT) failed |
| 12:18 | Fourth attempt (with --force-upload) failed |
| 12:45 | Fifth attempt (exact 3e67e70 template) failed |

**Pattern:** Every attempt since ~11:00 IST fails with same error, regardless of template changes.

## Next Steps

1. **Wait for external issue resolution** (AWS service, secrets, or permissions)
2. **Re-run deployment** once CloudFormation works
3. **Test catalogue creation** immediately after deployment
4. **Document resolution** in this file

---

**Created:** 2026-09-19 12:50 IST  
**Status:** Active Incident  
**Severity:** Medium (production stable, new features blocked)  
**Contact:** Check AWS Support or Service Health Dashboard

---

## RESOLUTION DETAILS

**Resolved:** 2026-09-19 13:23 IST  
**Resolution Time:** 2 hours 17 minutes (11:06 - 13:23 IST)

### Actual Root Cause

The CloudFormation stack had an **old deployed template** requesting secret key `api_token`, but the secret was updated to only contain key `token`.

**What Happened:**
1. Original deployment used `api_token` key
2. Commit dfef978 changed template to request `token` key
3. Template deployed successfully BUT secret was never updated
4. Later, secret was manually updated to have `token` key (removing `api_token`)
5. CloudFormation tried to validate OLD Lambda env vars → looked for `api_token` → NOT FOUND → deployment failed

**Why It Was Hard to Debug:**
- Our source `template.yaml` was already correct (requesting `token`)
- The processed template showed it requesting `api_token` (from deployed stack)
- CloudFormation validates EXISTING env vars before applying new template
- Created a catch-22: Can't deploy new template until old env vars validate

### Resolution Steps

**Step 1:** Identified the mismatch
```bash
# Checked processed template
aws cloudformation get-template \
  --stack-name efps-whapi-panel \
  --template-stage Processed

# Found: Template requests api_token
# But: Secret only has token key
```

**Step 2:** Temporarily added both keys to secret
```python
# Added api_token key with same value as token
secret_json['api_token'] = secret_json['token']
# Updated secret via AWS SDK
```

**Step 3:** Deployed successfully
```bash
sam build && sam deploy --no-confirm-changeset
# CloudFormation validated old env vars → found api_token → passed ✓
# Applied new template → Lambda now uses token key ✓
```

**Step 4:** Cleaned up temporary key
```python
# Removed api_token key, kept only token
del secret_json['api_token']
```

### Verification

```bash
# Lambda updated successfully
$ aws lambda get-function --function-name efps-whapi-panel-v2-EFPSEvents-sCPbGs4Mbtu2
LastModified: 2026-09-19T04:58:47.000+0000 ✓

# Secret has correct key
$ aws secretsmanager get-secret-value --secret-id efps-whapi-panel-token | jq 'keys'
["token"] ✓

# Template requests correct key  
$ grep WHAPI_API_TOKEN template.yaml
{{resolve:secretsmanager:${WhApiSecretArn}:SecretString:token}} ✓
```

### Key Learnings

1. **CloudFormation validates before updating** - checks existing Lambda env vars can resolve before applying new template
2. **Secret key names must match** - changing template key name requires matching change in secret
3. **Use processed template for truth** - shows what CloudFormation actually deployed, not what's in source
4. **Break the cycle** - when stuck, temporarily make both old and new states valid, then deploy

### What Was Deployed

✅ **Catalogue Creation Fix** (commit 5ae3474)
- Skips properties that already have meta_catalog_id
- Protects success state from retry errors
- Fixes infinite loop/stuck behavior

✅ **IAM Role Updates** (commits 3e67e70, e0fca0b)
- Hardened DynamoDB permissions
- Added SessionsTableArn access for Commands/Events

✅ **Environment Variable Fixes**
- WHAPI_API_TOKEN correctly resolves to `token` key
- All other secrets already matched their template references

---

**Final Status:** ✅ Resolved and deployed to production  
**Production Health:** All systems operational  
**Next Action:** Test catalogue creation with `/efps catalogue start`
