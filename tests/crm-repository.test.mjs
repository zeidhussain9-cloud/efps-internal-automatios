import test from 'node:test';
import assert from 'node:assert/strict';
import {createCrmRepository,normalizeConnectionString} from '../src/crm-repository.mjs';
test('normalizes direct Supabase URL to IPv4 session pooler',()=>{
 const input='postgresql://postgres:p%40ssword@db.qttcutwzehtskfcwxkwj.supabase.co:5432/postgres';
 const out=normalizeConnectionString(input);
 assert.match(out,/@aws-0-ap-south-1\.pooler\.supabase\.com:5432\/postgres/);
 assert.match(out,/postgres\.qttcutwzehtskfcwxkwj:.*@/);
 assert.match(out,/sslmode=require/);
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
