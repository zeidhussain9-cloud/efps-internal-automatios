import test from 'node:test';
import assert from 'node:assert/strict';
import {createCrmRepository,normalizeConnectionString,connectionEndpointClass} from '../src/crm-repository.mjs';
test('normalizes direct Supabase URL to IPv4 session pooler',()=>{
 const input='postgresql://postgres:p%40ssword@db.qttcutwzehtskfcwxkwj.supabase.co:5432/postgres';
 const out=normalizeConnectionString(input);
 assert.match(out,/@aws-0-ap-south-1\.pooler\.supabase\.com:5432\/postgres/);
 assert.match(out,/postgres\.qttcutwzehtskfcwxkwj:.*@/);
 assert.ok(!out.includes('sslmode='));
});
test('normalizes a raw special-character password without exposing it',()=>{
 const input='postgresql://postgres:p@ss#word@db.qttcutwzehtskfcwxkwj.supabase.co:5432/postgres';
 const out=normalizeConnectionString(input);
 assert.equal(out.includes('@aws-0-ap-south-1.pooler.supabase.com:5432/postgres'),true);
 assert.equal(out.includes('postgres.qttcutwzehtskfcwxkwj:'),true);
 assert.match(out,/p%40ss%23word/);
});
test('reports normalized endpoint class without exposing connection details',()=>{
 assert.equal(connectionEndpointClass('postgresql://postgres:fictional@db.qttcutwzehtskfcwxkwj.supabase.co:5432/postgres'),'supabase_session_pooler_ipv4');
 assert.equal(connectionEndpointClass('postgresql://postgres:fictional@db.example.invalid:5432/postgres'),'external_or_unknown');
 assert.equal(connectionEndpointClass('not-a-url'),'invalid_url');
 assert.equal(connectionEndpointClass('postgresql://postgres:p@ss#word@db.qttcutwzehtskfcwxkwj.supabase.co:5432/postgres'),'supabase_session_pooler_ipv4');
});
test('leaves non-Supabase URLs unchanged',()=>{
 const input='postgresql://postgres:fictional@db.example.invalid:5432/postgres';
 assert.equal(normalizeConnectionString(input),input);
});
test('repository validates limits and uses parameterized SQL',async()=>{
 const calls=[];const pool={query:async(sql,args)=>{calls.push({sql,args});return {rows:sql.startsWith('SELECT 1')?[{ok:1}]:[{id:'L-1'}]};}};
 const repo=createCrmRepository({pool});
 assert.equal(await repo.health(),true);
 assert.deepEqual(await repo.listLeads(10),[{id:'L-1'}]);
 assert.deepEqual(await repo.getLead('L-1'),{id:'L-1'});
 assert.deepEqual(calls[1].args,[10]);assert.deepEqual(calls[2].args,['L-1']);
 await assert.rejects(()=>repo.listLeads(101),/Invalid limit/);
 await assert.rejects(()=>repo.getLead(''),/Invalid lead ID/);
});

test('durable lead mutation is transactional and writes an audit event',async()=>{
 const calls=[];
 const client={query:async(sql,args)=>{calls.push(['client',sql,args]);if(sql.startsWith('INSERT INTO crm_leads'))return{rows:[{id:'L-1001',display_name:'A'}]};if(sql.startsWith('INSERT INTO crm_activity'))return{rows:[{id:1}]};return{rows:[]}},release:()=>calls.push(['release'])};
 const pool={connect:async()=>client};
 const repo=createCrmRepository({pool});
 const row=await repo.createLead({id:'L-1001',displayName:'A',actor:'pilot',requirements:{bhk:2}});
 assert.equal(row.id,'L-1001');assert.equal(calls[0][1],'BEGIN');assert.match(calls[1][1],/^INSERT INTO crm_leads/);assert.match(calls[2][1],/^INSERT INTO crm_activity/);assert.equal(calls[3][1],'COMMIT');assert.equal(calls[4][0],'release');
});
test('provider event deduplication relies on a database unique key',async()=>{
 const calls=[];const pool={query:async(sql,args)=>{calls.push([sql,args]);return{rows:[]}}};
 const repo=createCrmRepository({pool});
 const result=await repo.recordProviderEvent({provider:'test',providerEventId:'evt-1',eventType:'message',payload:{id:1}});
 assert.deepEqual(result,{inserted:false,id:null});assert.match(calls[0][0],/ON CONFLICT\(provider,provider_event_id\) DO NOTHING/);
});
test('AI cursor is upserted per source',async()=>{
 const calls=[];const pool={query:async(sql,args)=>{calls.push([sql,args]);return{rows:[{source_number:'wa-1',cursor:'c1'}]}}};
 const repo=createCrmRepository({pool});
 const row=await repo.setAiCursor({sourceNumber:'wa-1',cursor:'c1'});assert.equal(row.cursor,'c1');assert.match(calls[0][0],/ON CONFLICT\(source_number\) DO UPDATE/);
});
