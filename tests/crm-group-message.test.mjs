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
 assert.match(webhook,/classification_code:'group_message'/);
 assert.match(webhook,/classification_source:'webhook_rule'/);
});

test('non-promoted group classification remains excluded from CRM leads',async()=>{
 const repo=await read('src/crm-classification-repository.mjs');
 assert.match(repo,/if\(code!=='qualified_lead'\)/);
 assert.doesNotMatch(repo,/group_message\s*:\s*'Qualified Lead'/);
});
