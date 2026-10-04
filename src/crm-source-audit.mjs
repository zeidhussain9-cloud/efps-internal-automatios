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
  return {ok:true,productCount:reconciled.productCount,productIds:[...new Set(products.items.map(product=>String(product?.id||'').trim()).filter(Boolean))],products:products.items.map(product=>({id:String(product?.id||'').trim(),retailerId:String(product?.product_retailer_id||product?.retailer_id||'').trim(),name:product?.name||null,description:product?.description||null,price:product?.price??null,currency:product?.currency||null,availability:product?.availability||null,url:product?.url||null,isHidden:product?.is_hidden??null,imageCount:Array.isArray(product?.images)?product.images.length:0})),collectionCount:collections.items.length,productsWithCollections:reconciled.productsWithCollections,productsWithoutCollections:reconciled.productsWithoutCollections,collectionDetails:collectionResults.map(c=>({id:c.id,name:c.name,productCount:c.productCount,productIds:c.products.map(p=>String(p?.id||'').trim()).filter(Boolean)})),complete:true,readOnly:true};
}

function countField(rows,index){
  const counts={};
  for(const row of rows){
    const value=String(row?.[index]??'').trim()||'(blank)';
    counts[value]=(counts[value]||0)+1;
  }
  return counts;
}

export async function housingSheetSnapshot(){
  const result=await readHousingSheet({env:process.env});
  const rows=Array.isArray(result.rows)?result.rows:[];
  const header=rows[0]||[];
  const dataRows=rows.slice(1).filter(row=>Array.isArray(row)&&String(row?.[0]??'').trim());
  const statusCounts=countField(dataRows,1);
  const intakeStatusCounts=countField(dataRows,2);
  const listingStateCounts=countField(dataRows,4);
  const metaCatalogStatusCounts=countField(dataRows,45);
  const metaCatalogIdCount=dataRows.filter(row=>String(row?.[44]??'').trim()).length;
  const availableCatalogCount=Number(listingStateCounts.Available||0);
    const availableRows=dataRows.filter(row=>String(row?.[4]??'').trim()==='Available').map(row=>({listingId:String(row?.[0]??'').trim(),catalogTitle:String(row?.[33]??'').trim(),cloudinaryImages:String(row?.[34]??'').split(',').map(x=>x.trim()).filter(Boolean),metaCatalogId:String(row?.[44]??'').trim(),metaCatalogStatus:String(row?.[45]??'').trim(),postedUrl:String(row?.[41]??'').trim(),bhk:String(row?.[13]??'').trim(),listingState:String(row?.[4]??'').trim()}));
  return {range:result.range||null,rowCount:dataRows.length,columnCount:header.length,statusCounts,intakeStatusCounts,listingStateCounts,metaCatalogStatusCounts,metaCatalogIdCount,availableCatalogCount,availableRows,readOnly:true};
}

function reconcileCatalogToSheet(sheet,catalog){
  const rows=Array.isArray(sheet?.availableRows)?sheet.availableRows:[];
  const products=Array.isArray(catalog?.products)?catalog.products:[];
  const byId=new Map(products.map(p=>[String(p.id||'').trim(),p]).filter(([id])=>id));
  const byRetailer=new Map(products.map(p=>[String(p.retailerId||'').trim(),p]).filter(([id])=>id));
  const matches=[]; const missing=[]; const duplicateSheetIds=[]; const used=new Set();
  const seenSheetIds=new Set();
  for(const row of rows){
    if(row.metaCatalogId&&seenSheetIds.has(row.metaCatalogId)) duplicateSheetIds.push(row.metaCatalogId);
    if(row.metaCatalogId) seenSheetIds.add(row.metaCatalogId);
    const product=(row.metaCatalogId&&byId.get(row.metaCatalogId))||byRetailer.get(row.listingId)||null;
    if(!product){missing.push(row);continue;}
    used.add(String(product.id));
    matches.push({row,product});
  }
  const catalogOnly=products.filter(p=>!used.has(String(p.id||'')));
  const fieldMismatches=[];
  for(const {row,product} of matches){
    const checks=[
      ['title',row.catalogTitle,product.name],
      ['url',row.postedUrl,product.url],
      ['availability',row.listingState==='Available'?'in stock':null,product.availability],
      ['image_count',row.cloudinaryImages.length,product.imageCount]
    ];
    for(const [field,a,b] of checks){if(a!==''&&a!==null&&a!==undefined&&b!==null&&b!==undefined&&String(a)!==String(b))fieldMismatches.push({listingId:row.listingId,productId:product.id,field,sheet:a,whapi:b});}
  }
  const expectedCollection=bhk=>{const s=String(bhk||'').toUpperCase().replace(/\\s+/g,'');if(s.includes('1RK')||s.includes('1BHK'))return '1RK & 1BHK';if(s.includes('2BHK'))return '2BHK';if(s.includes('3BHK'))return '3BHK';if(/4\\+BHK|4BHK|5BHK|6BHK/.test(s))return '4+ BHK';return null;};
  const memberships=new Map(); for(const c of (catalog.collectionDetails||[])) for(const id of c.productIds||[]) memberships.set(String(id),c.name);
  const collectionMismatches=[];
  for(const {row,product} of matches){const expected=expectedCollection(row.bhk);if(expected){const actual=memberships.get(String(product.id))||null;if(actual!==expected)collectionMismatches.push({listingId:row.listingId,productId:product.id,expected,actual});}}
  return {sheetAvailable:rows.length,whapiProducts:products.length,identity:{matched:matches.length,missing:missing.length,catalogOnly:catalogOnly.length,duplicateSheetIds:duplicateSheetIds.length},field:{compared:matches.length*4,mismatches:fieldMismatches.length,mismatchDetails:fieldMismatches.slice(0,100)},lifecycle:{sheetAvailableRows:rows.length,productsMarkedInStock:products.filter(p=>p.availability==='in stock'&&!p.isHidden).length,productsHidden:products.filter(p=>p.isHidden===true).length},id:{sheetIds:rows.filter(r=>r.metaCatalogId).length,matchedByMetaId:rows.filter(r=>r.metaCatalogId&&byId.has(r.metaCatalogId)).length,retailerIdFallbackMatches:matches.filter(x=>!x.row.metaCatalogId&&byRetailer.has(x.row.listingId)).length},removed:{sheetRemovedMarked:0,catalogProductsForRemovedSheet:0},missingProducts:missing.map(r=>({listingId:r.listingId,metaCatalogId:r.metaCatalogId})),catalogOnlyProducts:catalogOnly.map(p=>({id:p.id,retailerId:p.retailerId,name:p.name})),collectionExpectation:{derivableBhk:rows.filter(r=>expectedCollection(r.bhk)).length,mismatches:collectionMismatches.length,details:collectionMismatches.slice(0,100)},complete:true};
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
    catalogReconciliation:catalog.status==='fulfilled'&&sheet.status==='fulfilled'?reconcileCatalogToSheet(sheet.value,catalog.value):{complete:false,error:'Sheet or catalog unavailable'},
    crm:crm.status==='fulfilled'?{ok:true,...crm.value}:{ok:false,error:crm.reason?.message||'CRM read failed'}};
}
