import {readHousingSheet} from './housing-sheet-adapter.mjs';
import pg from 'pg';
const {Pool}=pg;

const WHAPI_BASE_URL=(process.env.WHAPI_BASE_URL||'https://gate.whapi.cloud').replace(/\/$/,'');
const SOURCE_NUMBER=process.env.CRM_WHATSAPP_SOURCE_NUMBER||'+919148338801';

async function fetchJson(path,query={}){
  const token=String(process.env.WHAPI_API_TOKEN||'').trim();
  if(!token) throw new Error('WHAPI_API_TOKEN is not configured');
  const url=new URL(WHAPI_BASE_URL+path);
  for(const [k,v] of Object.entries(query)){if(v!==undefined&&v!==null&&v!=='')url.searchParams.set(k,String(v));}
  const controller=new AbortController(); const timer=setTimeout(()=>controller.abort(),15000);
  try{
    const response=await fetch(url,{headers:{Authorization:`Bearer ${token}`,Accept:'application/json'},signal:controller.signal});
    const text=await response.text(); let body=null; try{body=text?JSON.parse(text):null}catch{}
    if(!response.ok) throw new Error(`WhAPI HTTP ${response.status}`);
    return body;
  } finally {clearTimeout(timer);}
}

export async function whapiHealth(){return fetchJson('/health');}
export async function whapiRecentMessages({count=100,fromMe=false,timeFrom,timeTo}={}){
  const body=await fetchJson('/messages/list',{count:Math.min(Math.max(Number(count)||100,1),100),from_me:fromMe,time_from:timeFrom,time_to:timeTo});
  return {messages:Array.isArray(body?.messages)?body.messages:[],total:body?.total??null};
}
export async function whapiMessage(id){if(!id)throw new Error('message id required');return fetchJson(`/messages/${encodeURIComponent(id)}`);}export async function housingSheetSnapshot(){
  const result=await readHousingSheet({env:process.env});
  const rows=Array.isArray(result.rows)?result.rows:[];
  const header=rows[0]||[];
  return {range:result.range||null,rowCount:Math.max(rows.length-1,0),columnCount:header.length,readOnly:true};
}

async function crmSnapshot(){
  if(!process.env.DATABASE_URL) throw new Error('DATABASE_URL is not configured');
  const pool=new Pool({connectionString:process.env.DATABASE_URL,ssl:process.env.DATABASE_SSL_CA?{ca:process.env.DATABASE_SSL_CA,rejectUnauthorized:true}:{rejectUnauthorized:true},max:1});
  const client=await pool.connect();
  try{
    await client.query('BEGIN'); await client.query('SET TRANSACTION READ ONLY');
    const q=await client.query(`select
      (select count(*) from crm_webhook_events where provider='whapi') as webhook_total,
      (select max(received_at) from crm_webhook_events where provider='whapi') as webhook_latest,
      (select count(*) from crm_webhook_events where provider='whapi' and processing_status='error') as webhook_errors,
      (select count(*) from crm_messages) as message_total,
      (select max(message_at) from crm_messages) as message_latest,
      (select row_count from crm_inventory_sync_runs where source_kind='housing_sheet' order by created_at desc limit 1) as sheet_sync_rows,
      (select created_at from crm_inventory_sync_runs where source_kind='housing_sheet' order by created_at desc limit 1) as sheet_sync_latest`);
    await client.query('ROLLBACK'); return {...q.rows[0],source_number:SOURCE_NUMBER,readOnly:true};
  } finally {client.release();await pool.end();}
}

export async function sourceAuditSnapshot(){
  const [whapi,sheet,crm]=await Promise.allSettled([whapiRecentMessages({count:100,fromMe:false}),housingSheetSnapshot(),crmSnapshot()]);
  const latestWhapi=whapi.status==='fulfilled'?whapi.value.messages.reduce((m,x)=>Math.max(m,Number(x?.timestamp||0)),0):0;
  return {checkedAt:new Date().toISOString(),sourceNumber:SOURCE_NUMBER,
    whapi:whapi.status==='fulfilled'?{ok:true,recentInboundCount:whapi.value.messages.length,total:whapi.value.total,latestMessageTimestamp:latestWhapi||null}:{ok:false,error:whapi.reason?.message||'WhAPI read failed'},
    sheet:sheet.status==='fulfilled'?{ok:true,...sheet.value}:{ok:false,error:sheet.reason?.message||'Sheet read failed'},
    crm:crm.status==='fulfilled'?{ok:true,...crm.value}:{ok:false,error:crm.reason?.message||'CRM read failed'}};
}