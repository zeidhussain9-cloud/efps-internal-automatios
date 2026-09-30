import fs from 'node:fs/promises';
import crypto from 'node:crypto';
import {resolve,dirname} from 'node:path';
import pg from 'pg';
import {normalizeConnectionString} from '../src/crm-repository.mjs';

const ROOT=resolve(dirname(new URL(import.meta.url).pathname),'..');
const SOURCE='+919148338801';
const EXPORT=resolve(ROOT,'.private-import/9148338801-conversations.json');
const BACKUP=resolve(ROOT,'.private-import/crm-preconversation-2026-09-30.enc');
const KEYFILE=process.env.CRM_BACKUP_KEY_FILE||resolve(ROOT,'.crm-backup-key');

function parseEnv(text){const out={};for(const raw of text.split(/\r?\n/)){const line=raw.trim();if(!line||line.startsWith('#')||!line.includes('='))continue;const i=line.indexOf('=');let v=line.slice(i+1).trim();if((v.startsWith('"')&&v.endsWith('"'))||(v.startsWith("'")&&v.endsWith("'")))v=v.slice(1,-1);out[line.slice(0,i).trim()]=v.replace(/\\n/g,'\n')}return out}
function sha256(buf){return crypto.createHash('sha256').update(buf).digest('hex')}
function enc(buf,key){const iv=crypto.randomBytes(12),c=crypto.createCipheriv('aes-256-gcm',key,iv),data=Buffer.concat([c.update(buf),c.final()]);return Buffer.from(JSON.stringify({magic:'EFPS_CRM_BACKUP_V1',iv:iv.toString('base64'),tag:c.getAuthTag().toString('base64'),data:data.toString('base64')})+'\n')}
function parseJsonMaybe(v){if(v===null||v===undefined||v==='')return null;try{return JSON.parse(v)}catch{return null}}

async function main(){
 if(process.env.CRM_SINGLE_SOURCE_CONVERSATION_IMPORT_APPROVED!=='true')throw Error('Explicit CRM_SINGLE_SOURCE_CONVERSATION_IMPORT_APPROVED=true required');
 if(process.env.CRM_REAL_DATA_ENABLED==='true')throw Error('CRM_REAL_DATA_ENABLED must remain disabled');
 const raw=await fs.readFile(EXPORT);const source=JSON.parse(raw.toString());
 if(source.source_number!==SOURCE||source.lead_count!==228||source.message_count!==5286||!Array.isArray(source.messages)||source.messages.length!==5286)throw Error('Source conversation export is not the audited 228-lead/5286-message dataset');
 const key=Buffer.from((await fs.readFile(KEYFILE,'utf8')).trim(),'base64');if(key.length!==32)throw Error('Backup key invalid');
 const ENVFILE=process.env.CRM_ENV_FILE||resolve(ROOT,'.env.local'); const env=parseEnv(await fs.readFile(ENVFILE,'utf8'));if(!env.DATABASE_URL||!env.DATABASE_SSL_CA)throw Error('Local database connection configuration missing');
 const client=new pg.Client({connectionString:normalizeConnectionString(env.DATABASE_URL),ssl:{rejectUnauthorized:true,ca:env.DATABASE_SSL_CA}});await client.connect();
 try{
  const names=(await client.query("select table_name from information_schema.tables where table_schema='public' and table_name like 'crm_%' order by table_name")).rows.map(r=>r.table_name);
  const snap={format:'EFPS_CRM_BACKUP_PRECONVERSATION_V1',captured_at:new Date().toISOString(),tables:{}};
  for(const n of names)snap.tables[n]=(await client.query('select * from public.'+n)).rows;
  const backup=enc(Buffer.from(JSON.stringify(snap)),key);await fs.writeFile(BACKUP,backup,{flag:'wx',mode:0o600});
  const digest=sha256(raw);await client.query('BEGIN');
  try{
   await client.query('select pg_advisory_xact_lock(hashtext($1))',[SOURCE]);
   const existing=await client.query('select response from public.crm_idempotency_keys where key=$1',['historical-conversations:'+SOURCE+':'+digest]);
   if(existing.rows[0])throw Error('This exact conversation export has already been imported');
   const sourceLeads=(await client.query('select l.id,l.normalized_phone from public.crm_leads l join public.crm_lead_sources s on s.lead_id=l.id where s.source_number=$1',[SOURCE])).rows;
   if(sourceLeads.length!==228)throw Error('Expected 228 imported source leads before conversation import');
   const leadByPhone=new Map(sourceLeads.map(r=>[r.normalized_phone,r.id]));
   let inserted=0,duplicates=0;
   for(const m of source.messages){
    const phone=String(m.phone_number||'');const leadId=leadByPhone.get(phone);if(!leadId)throw Error('Conversation phone has no imported CRM lead: '+phone);
    const direction=m.direction==='Outgoing'?'Outgoing':m.direction==='Incoming'?'Incoming':null;if(!direction)throw Error('Invalid message direction');
    const at=new Date(m.timestamp);if(!Number.isFinite(at.valueOf()))throw Error('Invalid message timestamp');
    const result=await client.query(
      'insert into public.crm_messages(lead_id,source_number,provider_message_id,source_message_id,direction,message_type,body,sender_name,media_urls,media_filenames,extracted_intent,extracted_entities,sentiment,requires_followup,replied_to_source_message_id,message_at) values($1,$2,$3,$4,$5,$6,$7,$8,$9::jsonb,$10::jsonb,$11,$12::jsonb,$13,$14,$15,$16) on conflict do nothing returning id',
      [leadId,SOURCE,null,String(m.message_id),direction,String(m.message_type||'text'),m.message_body??null,m.sender_name??null,parseJsonMaybe(m.media_urls)?JSON.stringify(parseJsonMaybe(m.media_urls)):null,parseJsonMaybe(m.media_filenames)?JSON.stringify(parseJsonMaybe(m.media_filenames)):null,m.extracted_intent??null,parseJsonMaybe(m.extracted_entities)?JSON.stringify(parseJsonMaybe(m.extracted_entities)):null,m.sentiment??null,Boolean(m.requires_followup),m.replied_to_id==null?null:String(m.replied_to_id),at.toISOString()]
    );
    if(result.rows[0])inserted++;else duplicates++;
   }
   const count=(await client.query('select count(*)::int n from public.crm_messages where source_number=$1 and source_message_id is not null',[SOURCE])).rows[0].n;
   if(count!==5286)throw Error('Post-import source conversation count reconciliation failed: '+count);
   await client.query('insert into public.crm_idempotency_keys(key,scope,request_hash,response) values($1,$2,$3,$4::jsonb)',[
    'historical-conversations:'+SOURCE+':'+digest,'historical-conversation-import',digest,JSON.stringify({source_number:SOURCE,message_count:5286,inserted,duplicates,backup_sha256:sha256(backup)})
   ]);
   await client.query('COMMIT');
   console.log(JSON.stringify({status:'imported',source:SOURCE,messages:5286,inserted,duplicates,export_sha256:digest,backup_sha256:sha256(backup)}));
  }catch(e){await client.query('ROLLBACK');throw e}
 }finally{await client.end()}
}
main().catch(e=>{console.error('conversation import failed:',e.message);process.exitCode=1});
