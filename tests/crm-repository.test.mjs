import test from 'node:test';
import assert from 'node:assert/strict';
import {createCrmRepository} from '../src/crm-repository.mjs';
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
