import {readHousingSheet} from './housing-sheet-adapter.mjs';
import pg from 'pg';
import {auditRequirementAndMatching} from './crm-requirement-match-audit.mjs';
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
  return {ok:true,productCount:reconciled.productCount,productIds:[...new Set(products.items.map(product=>String(product?.id||'').trim()).filter(Boolean))],products:products.items.map(product=>({id:String(product?.id||'').trim(),retailerId:String(product?.product_retailer_id||product?.retailer_id||'').trim(),name:product?.name||null,description:product?.description||null,price:product?.price??null,currency:product?.currency||null,availability:product?.availability||null,url:product?.url||null,isHidden:product?.is_hidden??null,imageCount:Array.isArray(product?.images)?product.images.length:0,imageUrls:Array.isArray(product?.images)?product.images.map(x=>String(x?.url||x?.original_image_url||x?.image_url||x||'').trim()).filter(Boolean):[]})),collectionCount:collections.items.length,productsWithCollections:reconciled.productsWithCollections,productsWithoutCollections:reconciled.productsWithoutCollections,collectionDetails:collectionResults.map(c=>({id:c.id,name:c.name,productCount:c.productCount,productIds:c.products.map(p=>String(p?.id||'').trim()).filter(Boolean)})),complete:true,readOnly:true};
}

function normalizeCatalogCollectionName(value){return String(value??'').replace(/^\p{Extended_Pictographic}\uFE0F?\s*/u,'').replace(/^\p{Extended_Pictographic}\s*/u,'').replace(/\s+/g,' ').trim();}
function deriveCatalogCollectionName(bhk){
  const s=String(bhk||'').toUpperCase().replace(/\s+/g,'');
  if(s.includes('1RK')||s.includes('1BHK'))return '1RK & 1BHK';
  if(s.includes('2BHK'))return '2BHK';
  if(s.includes('3BHK'))return '3BHK';
  if(/4\+BHK|4BHK|5BHK|6BHK/.test(s))return '4+ BHK';
  return null;
}

export async function repairCatalogCollections({dryRun=true}={}){
  const sheet=await housingSheetSnapshot();
  const catalog=await whapiCatalogAudit();
  const rows=Array.isArray(sheet?.availableRows)?sheet.availableRows:[];
  const products=Array.isArray(catalog?.products)?catalog.products:[];
  const productById=new Map(products.map(product=>[String(product.id||'').trim(),product]).filter(([id])=>id));
  const productByRetailer=new Map(products.map(product=>[String(product.retailerId||'').trim(),product]).filter(([id])=>id));
  const collections=new Map((catalog.collectionDetails||[]).map(collection=>[normalizeCatalogCollectionName(collection.name),collection]).filter(([name])=>name));
  const plan=new Map();
  const unresolved=[];
  for(const row of rows){
    const expected=deriveCatalogCollectionName(row.bhk);
    if(!expected){unresolved.push({listingId:row.listingId,reason:'BHK has no canonical collection'});continue;}
    const collection=collections.get(expected);
    if(!collection){unresolved.push({listingId:row.listingId,expected,reason:'canonical collection does not exist'});continue;}
    const product=(row.metaCatalogId&&productById.get(String(row.metaCatalogId).trim()))||productByRetailer.get(row.listingId);
    if(!product){unresolved.push({listingId:row.listingId,expected,reason:'catalog product not found'});continue;}
    const productId=String(product.id||'').trim();
    const existing=new Set((collection.productIds||[]).map(String));
    if(!existing.has(productId)){
      if(!plan.has(collection.id))plan.set(collection.id,{id:collection.id,name:collection.name,productIds:[]});
      plan.get(collection.id).productIds.push(productId);
    }
  }
  const additions=[...plan.values()].map(item=>({...item,productIds:[...new Set(item.productIds)]}));
  const changedProducts=additions.reduce((n,item)=>n+item.productIds.length,0);
  if(unresolved.length)return {ok:false,dryRun,unresolved,additions,changedProducts};
  if(dryRun)return {ok:true,dryRun,unresolved:[],additions,changedProducts};
  const results=[];
  for(const item of additions){
    const token=String(process.env.WHAPI_API_TOKEN||'').trim();
    const url=WHAPI_BASE_URL+'/business/collections/'+encodeURIComponent(item.id);
    for(let offset=0;offset<item.productIds.length;offset+=5){
      const productIds=item.productIds.slice(offset,offset+5);
      const controller=new AbortController(); const timer=setTimeout(()=>controller.abort(),60000);
      try{
        const res=await fetch(url,{method:'PATCH',headers:{Authorization:'Bearer '+token,Accept:'application/json','Content-Type':'application/json'},body:JSON.stringify({add_products:productIds}),signal:controller.signal});
        const text=await res.text(); let body=null; try{body=text?JSON.parse(text):null}catch{}
        if(!res.ok)throw new Error('WhAPI HTTP '+res.status+': '+String(text||'').slice(0,300));
        results.push({id:item.id,name:item.name,added:productIds.length,status:res.status,body});
      }finally{clearTimeout(timer);}
    }
  }
  const verified=await whapiCatalogAudit();
  return {ok:true,dryRun:false,unresolved:[],additions,changedProducts,results,verified:{productsWithCollections:verified.productsWithCollections,productsWithoutCollections:verified.productsWithoutCollections,collectionDetails:verified.collectionDetails}};
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
    const mapRow=row=>({listingId:String(row?.[0]??'').trim(),catalogTitle:String(row?.[33]??'').trim(),cloudinaryImages:String(row?.[34]??'').split(',').map(x=>x.trim()).filter(Boolean),metaCatalogId:String(row?.[44]??'').trim(),metaCatalogStatus:String(row?.[45]??'').trim(),postedUrl:String(row?.[41]??'').trim(),bhk:String(row?.[13]??'').trim(),listingState:String(row?.[4]??'').trim()});
  const allRows=dataRows.map(mapRow);
  const availableRows=allRows.filter(row=>row.listingState==='Available');
  return {range:result.range||null,rowCount:dataRows.length,columnCount:header.length,statusCounts,intakeStatusCounts,listingStateCounts,metaCatalogStatusCounts,metaCatalogIdCount,availableCatalogCount,allRows,availableRows,readOnly:true};
}

function normalizeCatalogTitle(value){return String(value??'').replace(/^\p{Extended_Pictographic}\uFE0F?\s*/u,'').replace(/^\p{Extended_Pictographic}\s*/u,'').replace(/\s+/g,' ').trim();}
function mediaKey(value){const s=String(value??'').trim();const match=s.match(/(?:^|[\\/])photo_(\\d+)\\.[a-z0-9]+(?:[?#].*)?$/i);return match?`photo_${match[1]}`:s.replace(/[?#].*$/,'');}
function normalizedMediaKeys(values){return [...new Set((values||[]).map(mediaKey).filter(Boolean))].sort();}
function normalizeCollection(value){return String(value??'').replace(/^\p{Extended_Pictographic}\uFE0F?\s*/u,'').replace(/^\p{Extended_Pictographic}\s*/u,'').replace(/\s+/g,' ').trim();}

function reconcileCatalogToSheet(sheet,catalog){
  const rows=Array.isArray(sheet?.availableRows)?sheet.availableRows:[];
  const allRows=Array.isArray(sheet?.allRows)?sheet.allRows:rows;
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
      ['title',normalizeCatalogTitle(row.catalogTitle),normalizeCatalogTitle(product.name)],
      ['url',row.postedUrl,product.url],
      ['availability',row.listingState==='Available'?'in stock':null,product.availability],
      ['image_set',normalizedMediaKeys(row.cloudinaryImages),normalizedMediaKeys(product.imageUrls)]
    ];
    for(const [field,a,b] of checks){
      if(field==='url'&&(a===''||a===null||a===undefined||b===null||b===undefined))continue;
      const equal=field==='image_set'?JSON.stringify(a)===JSON.stringify(b):String(a)===String(b);
      if(!equal)fieldMismatches.push({listingId:row.listingId,productId:product.id,field,sheet:a,whapi:b});
    }
  }
  const expectedCollection=bhk=>{const s=String(bhk||'').toUpperCase().replace(/\s+/g,'');if(s.includes('1RK')||s.includes('1BHK'))return '1RK & 1BHK';if(s.includes('2BHK'))return '2BHK';if(s.includes('3BHK'))return '3BHK';if(/4\+BHK|4BHK|5BHK|6BHK/.test(s))return '4+ BHK';return null;};
  const memberships=new Map(); for(const c of (catalog.collectionDetails||[])) for(const id of c.productIds||[]) memberships.set(String(id),normalizeCollection(c.name));
  const collectionMismatches=[];
  for(const {row,product} of matches){const expected=expectedCollection(row.bhk);if(expected){const actual=memberships.get(String(product.id))||null;if(actual!==expected)collectionMismatches.push({listingId:row.listingId,productId:product.id,expected,actual});}}
  const removedRows=allRows.filter(row=>row.listingState!=='Available'&&row.metaCatalogId);
  const removedStillCatalog=removedRows.filter(row=>byId.has(row.metaCatalogId)||byRetailer.has(row.listingId));
  return {sheetAvailable:rows.length,whapiProducts:products.length,identity:{matched:matches.length,missing:missing.length,catalogOnly:catalogOnly.length,duplicateSheetIds:duplicateSheetIds.length},field:{compared:matches.length*4,mismatches:fieldMismatches.length,mismatchDetails:fieldMismatches.slice(0,100)},lifecycle:{sheetAvailableRows:rows.length,productsMarkedInStock:products.filter(p=>p.availability==='in stock'&&!p.isHidden).length,productsHidden:products.filter(p=>p.isHidden===true).length},id:{sheetIds:rows.filter(r=>r.metaCatalogId).length,matchedByMetaId:rows.filter(r=>r.metaCatalogId&&byId.has(r.metaCatalogId)).length,retailerIdFallbackMatches:matches.filter(x=>!x.row.metaCatalogId&&byRetailer.has(x.row.listingId)).length},removed:{nonAvailableSheetRows:removedRows.length,catalogProductsForNonAvailableSheet:removedStillCatalog.length,removedReconciled:removedStillCatalog.length===0},missingProducts:missing.map(r=>({listingId:r.listingId,metaCatalogId:r.metaCatalogId})),catalogOnlyProducts:catalogOnly.map(p=>({id:p.id,retailerId:p.retailerId,name:p.name})),collectionExpectation:{derivableBhk:rows.filter(r=>expectedCollection(r.bhk)).length,mismatches:collectionMismatches.length,details:collectionMismatches.slice(0,100)},complete:matches.length===rows.length&&missing.length===0&&catalogOnly.length===0&&duplicateSheetIds.length===0&&fieldMismatches.length===0&&removedStillCatalog.length===0&&collectionMismatches.length===0};
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
    const reconciliation=await client.query(`select
      (select count(*) from crm_webhook_events where provider='whapi' and payload->>'chat_id' like '%@s.whatsapp.net' and phone is not null) as eligible_message_events,
      (select count(*) from crm_webhook_events where provider='whapi' and payload->>'chat_id' like '%@s.whatsapp.net' and phone is not null and message_id is not null) as linked_message_events,
      (select count(*) from crm_webhook_events where provider='whapi' and direction='Incoming' and payload->>'chat_id' like '%@s.whatsapp.net' and phone is not null) as eligible_incoming_contacts,
      (select count(*) from crm_webhook_events e where provider='whapi' and direction='Incoming' and payload->>'chat_id' like '%@s.whatsapp.net' and phone is not null and (e.lead_id is not null or exists (select 1 from crm_contact_classifications c where c.phone=e.phone))) as mapped_incoming_contacts,
      (select count(*) from crm_webhook_events e where provider='whapi' and payload->>'chat_id' like '%@s.whatsapp.net' and phone is not null and message_id is not null and not exists (select 1 from crm_messages m where m.id=e.message_id)) as broken_message_links`);
    const requirementRows=await client.query(`select
      c.lead_id,
      l.requirements,
      l.tenant_type,
      r.lead_id as profile_lead_id,
      r.bhk,r.budget,r.preferred_locations,r.tenant_type as profile_tenant_type,r.move_in_date,r.pets,r.veg_nonveg,
      r.furnishing,r.parking,r.property_type,r.bathrooms,r.occupancy_count,r.lease_term_months,
      r.preferred_floor,r.preferred_amenities,r.notes
      from crm_contact_classifications c
      join crm_leads l on l.id=c.lead_id
      left join crm_lead_requirements r on r.lead_id=c.lead_id
      where c.classification_code='qualified_lead' and c.status='promoted'
      order by c.lead_id`);
    const inventory=await client.query(`select listing_id,locality,bhk,monthly_rent,furnishing,pet_friendly,listing_state
      from crm_inventory_snapshot
      where source_kind='housing_sheet' and deleted_at is null and listing_state='Available'`);
    const media=await client.query(`with active as (
      select listing_id,cloudinary_image_urls
      from crm_inventory_snapshot
      where source_kind='housing_sheet' and deleted_at is null and listing_state='Available'
    ), urls as (
      select listing_id,jsonb_array_elements_text(cloudinary_image_urls) url from active
    )
    select
      (select count(*) from active) as active_listings,
      (select count(*) from active where jsonb_typeof(cloudinary_image_urls)='array' and jsonb_array_length(cloudinary_image_urls)>0) as listings_with_images,
      (select count(*) from urls) as image_urls,
      (select count(*) from urls where url like 'https://res.cloudinary.com/%') as valid_cloudinary_urls,
      (select count(*) from (select url from urls group by url having count(*)>1) d) as duplicate_urls,
      (select count(*) from crm_property_media) as property_media_rows`);
    const qualifiedLeads=requirementRows.rows.map(row=>({
      lead_id:row.lead_id,
      requirements:row.requirements,
      tenant_type:row.tenant_type,
      profile:row.profile_lead_id?{
        bhk:row.bhk,budget:row.budget===null?null:Number(row.budget),preferred_locations:row.preferred_locations||[],
        tenant_type:row.profile_tenant_type,move_in_date:row.move_in_date,pets:row.pets,veg_nonveg:row.veg_nonveg,
        furnishing:row.furnishing,parking:row.parking,property_type:row.property_type,bathrooms:row.bathrooms,
        occupancy_count:row.occupancy_count===null?null:Number(row.occupancy_count),
        lease_term_months:row.lease_term_months===null?null:Number(row.lease_term_months),
        preferred_floor:row.preferred_floor,preferred_amenities:row.preferred_amenities||[],notes:row.notes
      }:null
    }));
    const requirementMatchAudit=auditRequirementAndMatching({qualifiedLeads,inventoryRows:inventory.rows});
    await client.query('ROLLBACK');
    const mediaRow=media.rows[0]||{};
    const mediaReconciliation={
      activeListings:Number(mediaRow.active_listings),
      listingsWithImages:Number(mediaRow.listings_with_images),
      imageUrls:Number(mediaRow.image_urls),
      validCloudinaryUrls:Number(mediaRow.valid_cloudinary_urls),
      duplicateUrls:Number(mediaRow.duplicate_urls),
      propertyMediaRows:Number(mediaRow.property_media_rows),
      propertyMediaTableUnused: Number(mediaRow.property_media_rows)===0,
      complete:Number(mediaRow.active_listings)===Number(mediaRow.listings_with_images)&&Number(mediaRow.image_urls)===Number(mediaRow.valid_cloudinary_urls)&&Number(mediaRow.duplicate_urls)===0
    };
    return {...q.rows[0],eventReconciliation:{
      eligibleMessageEvents:Number(reconciliation.rows[0].eligible_message_events),
      linkedMessageEvents:Number(reconciliation.rows[0].linked_message_events),
      eligibleIncomingContacts:Number(reconciliation.rows[0].eligible_incoming_contacts),
      mappedIncomingContacts:Number(reconciliation.rows[0].mapped_incoming_contacts),
      brokenMessageLinks:Number(reconciliation.rows[0].broken_message_links),
      messageReconciled:Number(reconciliation.rows[0].eligible_message_events)===Number(reconciliation.rows[0].linked_message_events)&&Number(reconciliation.rows[0].broken_message_links)===0,
      contactReconciled:Number(reconciliation.rows[0].eligible_incoming_contacts)===Number(reconciliation.rows[0].mapped_incoming_contacts)
    },requirementMatchAudit,mediaReconciliation,source_number:SOURCE_NUMBER,readOnly:true};
  } finally {client.release();await pool.end();}
}

export async function sourceAuditSnapshot(){
  const [whapiHealthResult,whapi,sheet,catalog,crm]=await Promise.allSettled([whapiHealth(),whapiRecentMessages({count:100,fromMe:false}),housingSheetSnapshot(),whapiCatalogAudit(),crmSnapshot()]);
  const latestWhapi=whapi.status==='fulfilled'?whapi.value.messages.reduce((m,x)=>Math.max(m,Number(x?.timestamp||0)),0):0;
  return {checkedAt:new Date().toISOString(),sourceNumber:SOURCE_NUMBER,
    whapi:whapi.status==='fulfilled'?{ok:true,recentInboundCount:whapi.value.messages.length,total:whapi.value.total,latestMessageTimestamp:latestWhapi||null,health:whapiHealthResult.status==='fulfilled'?whapiHealthResult.value:null}:{ok:false,degraded:true,error:whapi.reason?.message||'WhAPI read failed',health:whapiHealthResult.status==='fulfilled'?whapiHealthResult.value:{error:whapiHealthResult.reason?.message||'WhAPI health read failed'},knownLimitation:'WhAPI /messages/list currently returns HTTP 500; catalog and CRM audits remain independently evaluated'},
    sheet:sheet.status==='fulfilled'?{ok:true,...sheet.value}:{ok:false,error:sheet.reason?.message||'Sheet read failed'},
    catalog:catalog.status==='fulfilled'?catalog.value:{ok:false,error:catalog.reason?.message||'WhAPI catalog read failed'},
    catalogReconciliation:catalog.status==='fulfilled'&&sheet.status==='fulfilled'?reconcileCatalogToSheet(sheet.value,catalog.value):{complete:false,error:'Sheet or catalog unavailable'},
    crm:crm.status==='fulfilled'?{ok:true,...crm.value}:{ok:false,error:crm.reason?.message||'CRM read failed'}};
}
