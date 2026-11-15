// Test-only process: real Edge TypeScript + isolated PostgreSQL, no network.
import fs from'node:fs';import readline from'node:readline';import{PGlite}from'@electric-sql/pglite';import{transform}from'esbuild';import{webcrypto,createHash}from'node:crypto';
import{v5Projection}from'../../supabase/functions/notion-inventory-state/inventory-v5-contract.mjs';
import{responseForOperation,missingActivePageRows}from'../../supabase/functions/notion-inventory-state/response-contract.mjs';
const db=new PGlite();await db.exec(`CREATE ROLE anon;CREATE ROLE authenticated;CREATE ROLE service_role;CREATE TABLE crm_inventory_intake_events(source_page_id text PRIMARY KEY,listing_id text,listing_page_id text,payload_hash text);CREATE TABLE crm_inventory_snapshot(listing_id text PRIMARY KEY,source_kind text,source_tab text,locality text,society_name text,bhk text,monthly_rent numeric,furnishing text,listing_state text,business_status text,intake_status text,pet_friendly text,cloudinary_image_urls jsonb,source_snapshot_at timestamptz,last_synced_at timestamptz,source_record jsonb,source_hash text,deleted_at timestamptz);`);
for(const name of ['20261115145500_inventory_v5_staged.sql','20261115145600_inventory_v5_worker_state.sql','20261115145700_inventory_v5_reference_order.sql','20261115145800_inventory_v5_atomic_mirror.sql','20261115145900_inventory_v5_recovery.sql','20261115150000_inventory_v5_intake_submission.sql'])await db.exec(fs.readFileSync(new URL('../../supabase/migrations/'+name,import.meta.url),'utf8'));
const supabase={rpc:async(name,args)=>{try{let keys=Object.keys(args);let result=await db.query(`SELECT ${name}(${keys.map((key,i)=>key+'=> $'+(i+1)).join(',')}) v`,Object.values(args));return{data:result.rows[0].v,error:null}}catch(error){return{data:null,error:{code:'TEST',message:error.message}}}}};
let handler;let source=fs.readFileSync(new URL('../../supabase/functions/notion-inventory-state/index.ts',import.meta.url),'utf8').replace(/^import .*$/mg,'').replace(/const EXPECTED_INTERNAL_KEY_SHA256 = '[a-f0-9]+'/,'const EXPECTED_INTERNAL_KEY_SHA256 = '+JSON.stringify(createHash('sha256').update('test-key').digest('hex')));
const Deno={env:{get:name=>name==='EFPS_INVENTORY_V5_ENABLED'?'true':'test'},serve:fn=>{handler=fn}};
new Function('Deno','createClient','crypto','v5Projection','responseForOperation','missingActivePageRows',(await transform(source,{loader:'ts',format:'esm',target:'es2022'})).code)(Deno,()=>supabase,webcrypto,v5Projection,responseForOperation,missingActivePageRows);
for await(const line of readline.createInterface({input:process.stdin})){
 try{let input=JSON.parse(line);let result;
  if(input.operation==='__seed'){
   await db.query('INSERT INTO inventory_processing_revisions(listing_id,page_id,last_acknowledged_values,field_provenance,revision) VALUES($1,$2,$3,$4,1)',[input.row.listing_id,input.page_id,input.row,input.provenance??{}]);
   await db.query(`INSERT INTO crm_inventory_snapshot(listing_id,source_record,source_hash,availability,pipeline_status,business_status,live_on,inventory_contract_version,inventory_revision) VALUES($1,$2,'seed','Available','Ready to Post','Ready to Post',ARRAY[]::text[],5,0)`,[input.row.listing_id,{...input.row,inventory_contract_version:5,notion_page_id:input.page_id}]);result={ok:true};
  }else if(input.operation==='__legacy_binding'){
   await db.query('INSERT INTO crm_inventory_intake_events(source_page_id,listing_id,listing_page_id,payload_hash) VALUES($1,$2,$3,$4)',[input.source_page_id,input.listing_id,input.page_id,input.payload_hash]);result={ok:true};
  }else if(input.operation==='__expire'){
   await db.exec("UPDATE inventory_processing_revisions SET lease_until=now()-interval '1 second';UPDATE inventory_renumber_jobs SET lease_until=now()-interval '1 second';UPDATE inventory_intake_submissions SET lease_until=now()-interval '1 second'");result={ok:true};
  }else if(input.operation==='__attest'){
   result=(await db.query("INSERT INTO inventory_effect_recovery_attestations(scope,page_id,effect,job_id,writer_reference,remote_reference,request_reference) VALUES($1,$2,$3,$4,'synthetic writer terminal','synthetic remote terminal','synthetic exact request') RETURNING id",[input.scope??'worker',input.page_id,input.effect,input.job_id??null])).rows[0];
  }else if(input.operation==='__inspect'){
   result={submissions:(await db.query('SELECT * FROM inventory_intake_submissions')).rows,jobs:(await db.query('SELECT * FROM inventory_renumber_jobs ORDER BY job_id')).rows,incidents:(await db.query('SELECT * FROM inventory_effect_recovery_incidents')).rows,state:(await db.query('SELECT * FROM inventory_processing_revisions')).rows[0],mirror:(await db.query('SELECT * FROM crm_inventory_snapshot')).rows[0]};
  }else{
   const response=await handler(new Request('https://test.invalid',{method:'POST',headers:{'x-efps-intake-auth':'test-key','Content-Type':'application/json'},body:JSON.stringify(input)}));
   const value=await response.json();if(!response.ok)throw Error('HTTP '+response.status+': '+JSON.stringify(value));result=value;
  }
  console.log(JSON.stringify({result}));
 }catch(error){console.log(JSON.stringify({error:error.message}))}
}
await db.close();
