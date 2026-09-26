import crypto from 'node:crypto';
import pg from 'pg';
import {readHousingSheet} from './housing-sheet-adapter.mjs';
const FIELDS=['listing_id','status','intake_status','internal_property_type','listing_state','onboarded_on','raw_message_text','locality','society_name','landmark','pincode','google_maps_url','furnish_type','BHK','bathrooms','balconies','floor_number','total_floors','built_up_area','carpet_area','monthly_rent','maintenance','maintenance_included','security_deposit','preferred_tenant_type','bachelor_preference','pet_friendly','servant_room','covered_parking','open_parking','society_amenities','flat_furnishings','property_highlights','catalog_title','cloudinary_image_urls','age_of_property_years','whatsapp_contact_link','whatsapp_group_link','transaction_type','property_subtype','city','posted_url','posted_at','error_notes','meta_catalog_id','meta_catalog_status','source_group','inventory_locked'];
const safeString=v=>v===undefined||v===null?'':String(v);
const hashRow=row=>crypto.createHash('sha256').update(JSON.stringify(row)).digest('hex');
export function projectSheetRows(values){
 const rows=new Map();
 for(const raw of values||[]){
  if(!raw||!safeString(raw[0]).trim())continue;
  const padded=[...raw];while(padded.length<FIELDS.length)padded.push('');
  const row=Object.fromEntries(FIELDS.map((k,i)=>[k,safeString(padded[i])]));
  const id=row.listing_id.trim();
  if(rows.has(id))throw Error('Duplicate listing_id in Housing_Listings: '+id);
  row.cloudinary_image_urls=row.cloudinary_image_urls.split(',').map(x=>x.trim()).filter(Boolean);
  const sourceHash=hashRow(row);
  rows.set(id,{row,sourceHash});
 }
 return [...rows.values()];
}
export function diffInventory(existing, incoming){
 const incomingIds=new Set(incoming.map(x=>x.row.listing_id));
 let changed=0,removed=0;
 for(const x of incoming) if(existing.get(x.row.listing_id)?.source_hash!==x.sourceHash || existing.get(x.row.listing_id)?.deleted_at) changed++;
 for(const [id,row] of existing) if(row.source_kind==='housing_sheet'&&!incomingIds.has(id)&&!row.deleted_at) removed++;
 return {changed,removed,total:incoming.length};
}
export async function readCanonicalInventory(env=process.env){
 const previous=env.CRM_HOUSING_SHEET_READ_ENABLED;
 if(!env.CRM_HOUSING_SHEET_READ_ENABLED)env.CRM_HOUSING_SHEET_READ_ENABLED='true';
 try{return projectSheetRows((await readHousingSheet({env})).rows.slice(1))}
 finally{if(previous===undefined)delete env.CRM_HOUSING_SHEET_READ_ENABLED;else env.CRM_HOUSING_SHEET_READ_ENABLED=previous}
}
export async function syncInventorySnapshot({rows,connectionString=process.env.DATABASE_URL,sslCa=process.env.DATABASE_SSL_CA,pool}={}){
 if(!connectionString&&!pool)throw Error('DATABASE_URL required');
 const db=pool||new pg.Pool({connectionString,ssl:sslCa?{rejectUnauthorized:true,ca:sslCa}:{rejectUnauthorized:true},max:5,connectionTimeoutMillis:5000});
 const runId=crypto.randomUUID(),now=new Date().toISOString();
 try{
  const current=await db.query('SELECT listing_id,source_kind,source_hash,deleted_at FROM crm_inventory_snapshot');
  const existing=new Map(current.rows.map(r=>[r.listing_id,r]));
  const plan=diffInventory(existing,rows);
  const client=await db.connect();
  try{
   await client.query('BEGIN');
   if(rows.length){
    await client.query(`WITH incoming AS (SELECT x.* FROM jsonb_to_recordset($1::jsonb) AS x(listing_id text,source_record jsonb,source_hash text,locality text,society_name text,bhk text,monthly_rent numeric,furnishing text,listing_state text,intake_status text,pet_friendly text,cloudinary_image_urls jsonb))
      INSERT INTO crm_inventory_snapshot(listing_id,source_kind,source_tab,source_record,source_hash,locality,society_name,bhk,monthly_rent,furnishing,listing_state,intake_status,pet_friendly,cloudinary_image_urls,source_snapshot_at,last_synced_at,deleted_at)
      SELECT listing_id,'housing_sheet','Housing_Listings',source_record,source_hash,locality,society_name,bhk,monthly_rent,furnishing,listing_state,intake_status,pet_friendly,cloudinary_image_urls,$2::timestamptz,$2::timestamptz,NULL FROM incoming
      ON CONFLICT(listing_id) DO UPDATE SET source_record=EXCLUDED.source_record,source_hash=EXCLUDED.source_hash,locality=EXCLUDED.locality,society_name=EXCLUDED.society_name,bhk=EXCLUDED.bhk,monthly_rent=EXCLUDED.monthly_rent,furnishing=EXCLUDED.furnishing,listing_state=EXCLUDED.listing_state,intake_status=EXCLUDED.intake_status,pet_friendly=EXCLUDED.pet_friendly,cloudinary_image_urls=EXCLUDED.cloudinary_image_urls,source_snapshot_at=EXCLUDED.source_snapshot_at,last_synced_at=EXCLUDED.last_synced_at,deleted_at=NULL,source_kind='housing_sheet',source_tab='Housing_Listings'`,[
      JSON.stringify(rows.map(x=>({listing_id:x.row.listing_id,source_record:x.row,source_hash:x.sourceHash,locality:x.row.locality,society_name:x.row.society_name,bhk:x.row.BHK,monthly_rent:x.row.monthly_rent?Number(x.row.monthly_rent):null,furnishing:x.row.furnish_type,listing_state:x.row.listing_state,intake_status:x.row.intake_status,pet_friendly:x.row.pet_friendly,cloudinary_image_urls:x.row.cloudinary_image_urls}))),now]);
   }
   const incomingIds=[...new Set(rows.map(x=>x.row.listing_id))];
   if(incomingIds.length) await client.query(`UPDATE crm_inventory_snapshot SET deleted_at=$1,last_synced_at=$1 WHERE source_kind='housing_sheet' AND deleted_at IS NULL AND NOT(listing_id=ANY($2::text[]))`,[now,incomingIds]);
   else await client.query(`UPDATE crm_inventory_snapshot SET deleted_at=$1,last_synced_at=$1 WHERE source_kind='housing_sheet' AND deleted_at IS NULL`,[now]);
   await client.query('INSERT INTO crm_inventory_sync_runs(run_id,source_kind,row_count,changed_count,removed_count) VALUES($1,$2,$3,$4,$5)',[runId,'housing_sheet',plan.total,plan.changed,plan.removed]);
   await client.query('COMMIT');
  }catch(e){try{await client.query('ROLLBACK')}catch{}throw e}finally{client.release()}
  return {...plan,runId,syncedAt:now};
 }finally{if(!pool)await db.end()}
}
