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
    if(!response.ok) throw new Error(`WhAPI HTTP ${response.status}: ${String(text||'').slice(0,300)}`);
    return body;
  } finally {clearTimeout(timer);}
}

async function fetchPaged(path,itemKey,{pageSize=100,maxPages=100}={}){
  const items=[]; let offset=0; let total=null;
  for(let page=0;page<maxPages;page++){
    const body=await fetchJson(path,{count:pageSize,offset});
    const pageItems=Array.isArray(body?.[itemKey])?body[itemKey]:[];
    if(total===null&&Number.isFinite(Number(body?.total)))total=Number(body.total);
    items.push(...pageItems);
    if(!pageItems.length)break;
    offset+=pageItems.length;
    if(total!==null&&offset>=total)break;
    if(pageItems.length<pageSize&&total===null)break;
  }
  return {items,total:total??items.length};
}

export async function whapiHealth(){return fetchJson('/health');}
export async function whapiRecentMessages({count=100,fromMe=false,timeFrom,timeTo}={}){
  const body=await fetchJson('/messages/list',{count:Math.min(Math.max(Number(count)||100,1),100),from_me:fromMe,time_from:timeFrom,time_to:timeTo});
  return {messages:Array.isArray(body?.messages)?body.messages:[],total:body?.total??null};
}
export async function whapiMessage(id){if(!id)throw new Error('message id required');return fetchJson(`/messages/${encodeURIComponent(id)}`);}

export function reconcileCatalogProducts(products,collections){
  const assignedProductIds=new Set();
  for(const collection of collections||[]){
    for(const product of collection?.products||[]){
      const productId=String(product?.id||'').trim();
      if(productId)assignedProductIds.add(productId);
    }
  }
  const productIds=new Set((products||[]).map(product=>String(product?.id||'').trim()).filter(Boolean));
  const productsWithCollections=[...assignedProductIds].filter(id=>productIds.has(id)).length;
  const productsWithoutCollections=[...productIds].filter(id=>!assignedProductIds.has(id)).length;
  return {productCount:productIds.size,productsWithCollections,productsWithoutCollections};
}

export async function whapiCatalogAudit(){
  const products=await fetchPaged('/business/products','products',{pageSize:100});
  const collections=await fetchPaged('/business/collections','collections',{pageSize:100});
  const collectionResults=[];
  for(const collection of collections.items){
    const id=String(collection?.id||'').trim();
    if(!id)continue;
    const detail=await fetchJson(`/business/collections/${encodeURIComponent(id)}`);
    const collectionProducts=Array.isArray(detail?.products)?detail.products:[];
    collectionResults.push({id,name:detail?.name||collection?.name||null,productCount:collectionProducts.length,products:collectionProducts});
  }
  const reconciled=reconcileCatalogProducts(products.items,collectionResults);
  return {
    ok:true,
    productCount:reconciled.productCount,
    collectionCount:collections.items.length,
    productsWithCollections:reconciled.productsWithCollections,
    productsWithoutCollections:reconciled.productsWithoutCollections,
    collectionDetails:collectionResults.map(({id,name,productCount})=>({id,name,productCount})),
    complete:true,
    readOnly:true
  };
}

export async function housingSheetSnapshot(){
  const result=await readHousingSheet({env:process.env});
  const rows=Array.isArray(result.rows)?result.rows:[];
  const header=rows[0]||[];
  const dataRows=rows.slice(1).filter(row=>Array.isArray(row)&&String(row?.[0]??'').trim());
  const availableCount=dataRows.filter(row=>String(row?.[1]??'').trim().toLowerCase()==='available').length;
  return {range:result.range||null,rowCount:dataRows.length,columnCount:header.length,availableCatalogCount:availableCount,readOnly:true};
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
  const [whapiHealthResult,whapi,sheet,catalog,crm]=await Promise.allSettled([whapiHealth(),whapiRecentMessages({count:100,fromMe:false}),housingSheetSnapshot(),whapiCatalogAudit(),crmSnapshot()]);
  const latestWhapi=whapi.status==='fulfilled'?whapi.value.messages.reduce((m,x)=>Math.max(m,Number(x?.timestamp||0)),0):0;
  return {checkedAt:new Date().toISOString(),sourceNumber:SOURCE_NUMBER,
    whapi:whapi.status==='fulfilled'?{ok:true,recentInboundCount:whapi.value.messages.length,total:whapi.value.total,latestMessageTimestamp:latestWhapi||null,health:whapiHealthResult.status==='fulfilled'?whapiHealthResult.value:null}:{ok:false,error:whapi.reason?.message||'WhAPI read failed',health:whapiHealthResult.status==='fulfilled'?whapiHealthResult.value:{error:whapiHealthResult.reason?.message||'WhAPI health read failed'}},
    sheet:sheet.status==='fulfilled'?{ok:true,...sheet.value}:{ok:false,error:sheet.reason?.message||'Sheet read failed'},
    catalog:catalog.status==='fulfilled'?catalog.value:{ok:false,error:catalog.reason?.message||'WhAPI catalog read failed'},
    crm:crm.status==='fulfilled'?{ok:true,...crm.value}:{ok:false,error:crm.reason?.message||'CRM read failed'}};
}
