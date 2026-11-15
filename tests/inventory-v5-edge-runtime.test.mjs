import fs from'node:fs';import test from'node:test';import assert from'node:assert/strict';import{webcrypto,createHash}from'node:crypto';import{transform}from'esbuild';
import{v5Projection}from'../supabase/functions/notion-inventory-state/inventory-v5-contract.mjs';import{responseForOperation,missingActivePageRows}from'../supabase/functions/notion-inventory-state/response-contract.mjs';
async function runtime(enabled='false'){
 let source=fs.readFileSync(new URL('../supabase/functions/notion-inventory-state/index.ts',import.meta.url),'utf8').replace(/^import .*$/mg,'');
 // Test-only key substitution. Production source keeps the deployed auth hash.
 source=source.replace(/const EXPECTED_INTERNAL_KEY_SHA256 = '[a-f0-9]+'/,'const EXPECTED_INTERNAL_KEY_SHA256 = '+JSON.stringify(createHash('sha256').update('isolated-test-key').digest('hex')));
 const calls=[];let handler;
 const db={rpc:async(name,args)=>{calls.push({name,args});return{data:{lease:'12345678-1234-4234-8234-123456789012'},error:null}},from:()=>({select:()=>({eq:()=>({maybeSingle:async()=>({data:null,error:null})})}),upsert:async row=>{calls.push({upsert:row});return{error:null}}})};
 const Deno={env:{get:name=>name==='EFPS_INVENTORY_V5_ENABLED'?enabled:'isolated'},serve:fn=>{handler=fn}};
 const js=(await transform(source,{loader:'ts',format:'esm',target:'es2022'})).code;
 new Function('Deno','createClient','crypto','v5Projection','responseForOperation','missingActivePageRows',js)(Deno,()=>db,webcrypto,v5Projection,responseForOperation,missingActivePageRows);
 return{calls,send:async(body,auth='isolated-test-key',method='POST')=>handler(new Request('https://isolated.invalid',{method,headers:{'x-efps-intake-auth':auth,'Content-Type':'application/json'},...(method==='POST'?{body:JSON.stringify(body)}:{})}))};
}
const page='12345678-1234-4234-8234-123456789012';
test('actual staged Edge handler rejects unauthenticated and disabled v5 operations',async()=>{
 const r=await runtime();assert.equal((await r.send({},'wrong')).status,401);assert.equal((await r.send({},'', 'GET')).status,405);
 assert.equal((await r.send({operation:'inventory_v5_worker',page_id:page,worker_operation:'claim',listing_id:'EF-2611-ABCD'})).status,409);assert.equal(r.calls.length,0);
});
test('actual staged Edge worker passes fenced arguments only under explicit flag',async()=>{
 const r=await runtime('true');let response=await r.send({operation:'inventory_v5_worker',page_id:page,worker_operation:'prepare',lease:page,revision:3,values:{x:0},patch:{x:1},provenance:{},input_hash:'a'.repeat(64)});
 assert.equal(response.status,200);assert.equal(r.calls[0].name,'inventory_v5_worker_state');assert.equal(r.calls[0].args.p_revision,3);assert.deepEqual(r.calls[0].args.p_values,{x:0});
 response=await r.send({operation:'inventory_v5_worker',page_id:page,worker_operation:'load',lease:'wrong'});assert.equal(response.status,400);assert.equal(r.calls.length,1);
});
test('actual staged Edge v5 mirror keeps typed empty channels and dual-readable status',async()=>{
 const r=await runtime('true');const row={listing_id:'EF-2611-ABCD',inventory_contract_version:5,Availability:'On Hold','Pipeline Status':'Ready to Post','Live On':[],onboarded_at:'2026-11-15T09:11:00Z',monthly_rent:0,cloudinary_image_urls:''};
 const response=await r.send({operation:'sync_inventory',page_id:page,listing_id:row.listing_id,source_hash:'b'.repeat(64),row});assert.equal(response.status,200);
 const saved=r.calls[0].upsert;assert.deepEqual(saved.live_on,[]);assert.equal(saved.monthly_rent,0);assert.equal(saved.listing_state,'On Hold');assert.equal(saved.business_status,'Ready to Post');assert.equal(saved.inventory_contract_version,5);
});
