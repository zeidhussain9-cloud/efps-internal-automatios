import fs from 'node:fs/promises';
import crypto from 'node:crypto';
import {resolve,dirname} from 'node:path';
import pg from 'pg';
import {normalizeConnectionString} from '../src/crm-repository.mjs';

const ROOT=resolve(dirname(new URL(import.meta.url).pathname),'../..');
const SOURCE='+919148338801';
const EXPORT=resolve(ROOT,'.private-import/9148338801-leads.json');
const BACKUP=resolve(ROOT,'.private-import/crm-preimport-2026-09-27.enc');
const KEYFILE=resolve(ROOT,'.crm-backup-key');
const REQUIRED_APPROVAL='true';

function parseEnv(text){
 const out={};
 for(const raw of text.split(/\r?\n/)){
  const line=raw.trim(); if(!line||line.startsWith('#')||!line.includes('=')) continue;
  const i=line.indexOf('='); let v=line.slice(i+1).trim();
  if((v.startsWith('"')&&v.endsWith('"'))||(v.startsWith("'")&&v.endsWith("'")))v=v.slice(1,-1);
  out[line.slice(0,i).trim()]=v.replace(/\\n/g,'\n');
 }
 return out;
}
function sha256(buf){return crypto.createHash('sha256').update(buf).digest('hex')}
function enc(buf,key){
 const iv=crypto.randomBytes(12),c=crypto.createCipheriv('aes-256-gcm',key,iv);
 const data=Buffer.concat([c.update(buf),c.final()]);
 return Buffer.from(JSON.stringify({magic:'EFPS_CRM_BACKUP_V1',iv:iv.toString('base64'),tag:c.getAuthTag().toString('base64'),data:data.toString('base64')})+'\n');
}
function dec(buf,key){
 const e=JSON.parse(buf.toString()); if(e.magic!=='EFPS_CRM_BACKUP_V1')throw Error('Invalid backup');
 const d=crypto.createDecipheriv('aes-256-gcm',key,Buffer.from(e.iv,'base64')); d.setAuthTag(Buffer.from(e.tag,'base64'));
 return Buffer.concat([d.update(Buffer.from(e.data,'base64')),d.final()]);
}
function idFor(phone){
 return 'L-H914833-'+sha256(Buffer.from(SOURCE+'\0'+phone)).slice(0,20);
}
function nullable(v){return v===null||v===undefined||String(v).trim()===''?null:v}
function requirements(r){
 const pick={};
 for(const [k,v] of Object.entries({
  current_requirement:r.current_requirement,bhk:r.bhk_requirement,preferred_location:r.preferred_location,
  budget_min:r.budget_min,budget_max:r.budget_max,furnishing:r.furnishing_preference,
  occupancy_type:r.occupancy_type,pet_preference:r.pet_preference,parking_required:r.parking_required,
  move_in_date:r.move_in_date,matched_properties:r.matched_properties,tags:r.tags,
  classification:r.classification,last_interaction_date:r.last_interaction_date,
  next_followup_date:r.next_followup_date,followup_count:r.followup_count
 })) if(v!==null&&v!==undefined&&String(v).trim()!=='') pick[k]=v;
 return {provenance:'historical_sqlite',source_number:SOURCE,fields:pick};
}
async function main(){
 if(process.env.CRM_SINGLE_SOURCE_IMPORT_APPROVED!==REQUIRED_APPROVAL)throw Error('Explicit CRM_SINGLE_SOURCE_IMPORT_APPROVED=true required');
 if(process.env.CRM_REAL_DATA_ENABLED==='true')throw Error('CRM_REAL_DATA_ENABLED must remain disabled');
 const raw=await fs.readFile(EXPORT); const source=JSON.parse(raw.toString());
 if(source.source_number!==SOURCE||!Array.isArray(source.leads)||source.leads.length!==228)throw Error('Source export is not the audited 228-row 9148338801 dataset');
 if(source.leads.some(r=>r.extracted_from_phone!==SOURCE))throw Error('Cross-source record detected');
 const keyPath=KEYFILE; let key;
 try{key=Buffer.from((await fs.readFile(keyPath,'utf8')).trim(),'base64')}catch{key=crypto.randomBytes(32);await fs.writeFile(keyPath,key.toString('base64')+'\n',{mode:0o600})}
 if(key.length!==32)throw Error('Backup key invalid');
 const env=parseEnv(await fs.readFile(resolve(ROOT,'.env.local'),'utf8'));
 if(!env.DATABASE_URL||!env.DATABASE_SSL_CA)throw Error('Local database connection configuration missing');
 await fs.mkdir(resolve(ROOT,'.private-import'),{recursive:true,mode:0o700});
 const client=new pg.Client({connectionString:normalizeConnectionString(env.DATABASE_URL),ssl:{rejectUnauthorized:true,ca:env.DATABASE_SSL_CA}});
 await client.connect();
 try{
  const names=(await client.query("select table_name from information_schema.tables where table_schema='public' and table_name like 'crm_%' order by table_name")).rows.map(r=>r.table_name);
  const snap={format:'EFPS_CRM_BACKUP_LOCAL_V1',captured_at:new Date().toISOString(),project:'qttcutwzehtskfcwxkwj',tables:{}};
  for(const n of names)snap.tables[n]=(await client.query('select * from public.'+n)).rows;
  const backup=enc(Buffer.from(JSON.stringify(snap)),key);
  await fs.writeFile(BACKUP,backup,{flag:'wx',mode:0o600});
  const restored=JSON.parse(dec(backup,key).toString());
  const counts=Object.fromEntries(Object.entries(restored.tables).map(([k,v])=>[k,v.length]));
  const digest=sha256(raw);
  await client.query('BEGIN');
  try{
   const lock=await client.query('select pg_advisory_xact_lock(hashtext($1))',[SOURCE]);
   void lock;
   const idemKey='historical-import:'+SOURCE+':'+digest;
   const existing=await client.query('select response from public.crm_idempotency_keys where key=$1',[idemKey]);
   if(existing.rows[0])throw Error('This exact source export has already been imported');
   const existingPhones=await client.query('select id,normalized_phone from public.crm_leads where normalized_phone = any($1::text[])',[source.leads.map(r=>r.phone_number)]);
   if(existingPhones.rows.length)throw Error('One or more source customer phone keys already exist in CRM; refusing partial merge');
   const seen=new Set();
   const validPriorities=new Set(['High','Medium','Low']);
   for(const r of source.leads){
    if(seen.has(r.phone_number)||!r.phone_number||r.phone_number===SOURCE)throw Error('Invalid or duplicate customer identity');
    seen.add(r.phone_number);
    if(r.lead_status!=='New')throw Error('Unexpected legacy status; review mapping before import');
    if(!validPriorities.has(r.priority))throw Error('Unexpected legacy priority; review mapping before import');
   }
   for(const r of source.leads){
    const id=idFor(r.phone_number);
    await client.query(
     'insert into public.crm_leads(id,display_name,normalized_phone,status,priority,requirements,operator_notes,created_at,updated_at) values($1,$2,$3,$4,$5,$6::jsonb,$7,$8,$9)',
     [id,nullable(r.customer_name),r.phone_number,'New',r.priority||'Medium',nullable(r.classification),JSON.stringify(requirements(r)),
      nullable(r.notes)?'[Historical source note] '+r.notes:'Historical import; source +919148338801; source-backed fields preserved as historical data.',
      r.created_at||new Date().toISOString(),r.updated_at||r.created_at||new Date().toISOString()]
    );
    await client.query(
     'insert into public.crm_lead_sources(lead_id,source_number,source_contact_id) values($1,$2,$3)',
     [id,SOURCE,r.phone_number]
    );
    await client.query(
     'insert into public.crm_activity(lead_id,actor,action,details) values($1,$2,$3,$4::jsonb)',
     [id,'historical-import:'+SOURCE,'lead.imported',JSON.stringify({source_number:SOURCE,source_digest:digest})]
    );
   }
   const count=(await client.query('select count(*)::int n from public.crm_leads where id like $1',['L-H914833-%'])).rows[0].n;
   const sourceCount=(await client.query('select count(*)::int n from public.crm_lead_sources where source_number=$1',[SOURCE])).rows[0].n;
   if(count!==228||sourceCount!==228)throw Error('Post-insert count reconciliation failed');
   await client.query(
    'insert into public.crm_idempotency_keys(key,scope,request_hash,response) values($1,$2,$3,$4::jsonb)',
    [idemKey,'historical-lead-import',digest,JSON.stringify({source_number:SOURCE,lead_count:228,source_count:228,backup_sha256:sha256(backup)})]
   );
   await client.query('COMMIT');
   console.log(JSON.stringify({status:'imported',source:SOURCE,leads:228,backup_sha256:sha256(backup),export_sha256:digest,backup_counts:counts}));
  }catch(e){await client.query('ROLLBACK');throw e}
 }finally{await client.end()}
}
main().catch(e=>{console.error('single-source import failed:',e.message);process.exitCode=1});
