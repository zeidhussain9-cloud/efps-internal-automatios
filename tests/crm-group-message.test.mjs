import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';

const read=path=>readFile(new URL('../'+path,import.meta.url),'utf8');

test('group-message classification is a first-class excluded classification',async()=>{
 const [migration,suffixFix,repository,ui,webhook]=await Promise.all([
  read('db/migrations/20261003150000_crm_group_message_classification_gate.sql'),
  read('db/migrations/20261003150001_crm_group_message_suffix_fix.sql'),
  read('src/crm-classification-repository.mjs'),
  read('src/main.jsx'),
  read('supabase/functions/whapi-crm-webhook/index.ts')
 ]);
 assert.match(suffixFix,/RIGHT\(group_chat_id,5\)='@g\.us'/);
 assert.match(migration,/Group Message/);
 assert.match(migration,/group_chat_id/);
 assert.match(repository,/group_message/);
 assert.match(repository,/group_message:'Group Message'/);
 assert.match(ui,/<option value="group_message">Group Message<\/option>/);
 assert.match(webhook,/chatId\.endsWith\('@g\.us'\)/);
 assert.match(suffixFix,/classification_code='group_message'/);
 assert.match(suffixFix,/classification_source='webhook_rule'/);
});

test('non-promoted group classification remains excluded from CRM leads',async()=>{
 const repo=await read('src/crm-classification-repository.mjs');
 assert.match(repo,/if\(code!=='qualified_lead'\)/);
 assert.doesNotMatch(repo,/group_message\s*:\s*'Qualified Lead'/);
});


test('null-phone webhook events persist a message without creating a contact',async()=>{
 const migration=await read('db/migrations/20261112090000_crm_null_phone_webhook_reconciliation.sql');
 const webhook=await read('supabase/functions/whapi-crm-webhook/index.ts');
 assert.match(migration,/IF p_phone IS NULL THEN[\s\S]*?INSERT INTO public\.crm_messages/);
 assert.match(migration,/classification_id,source_number,provider_message_id,source_message_id/);
 assert.match(migration,/processing_error= NULL|processing_error=NULL/);
 assert.match(migration,/processing_error IS NOT NULL AND message_id IS NULL/);
 assert.match(webhook,/supabase\.rpc\('crm_process_webhook_event'/);
 assert.match(webhook,/p_phone:p/);
 assert.doesNotMatch(webhook,/from\('crm_contact_classifications'\)\.insert/);
 assert.match(migration,/processing_error_history=CASE WHEN processing_error IS NULL/);
});

test('group messages are never attached to a promoted lead timeline',async()=>{
 const migration=await read('db/migrations/20261112090000_crm_null_phone_webhook_reconciliation.sql');
 assert.match(migration,/NOT is_group AND c\.status='promoted'/);
});


test('legacy null-phone message backfill is bounded and includes processed missing-message events',async()=>{
 const migration=await read('db/migrations/20261112150000_crm_reconcile_legacy_no_phone_messages.sql');
 assert.match(migration,/processing_status='processed' AND message_id IS NULL/);
 assert.match(migration,/ORDER BY id LIMIT 500 FOR UPDATE SKIP LOCKED/);
});
test('historical group-message reconciliation preserves prior links and removes lead attachment',async()=>{
 const migration=await read('db/migrations/20261112160000_crm_unlink_historical_group_messages.sql');
 assert.match(migration,/reconciliation_history=e\.reconciliation_history/);
 assert.match(migration,/previous_lead_id/);
 assert.match(migration,/SET lead_id=NULL/);
 assert.match(migration,/UPDATE public\.crm_messages m/);
 assert.doesNotMatch(migration,/SET classification_id=NULL/);
});