import pg from 'pg';
import {createCrmRepository,normalizeConnectionString} from './crm-repository.mjs';

const SOURCE_NUMBERS=['+919148338801','+917975102130','+919902024973'];
const SOURCE_NUMBER=SOURCE_NUMBERS[0];

export function createCrmClassificationRepository({connectionString=process.env.DATABASE_URL,sslCa=process.env.DATABASE_SSL_CA}={}){
  if(!connectionString)throw Error('DATABASE_URL required');
  const db=new pg.Pool({connectionString:normalizeConnectionString(connectionString),max:3,connectionTimeoutMillis:5000,ssl:{rejectUnauthorized:true,...(sslCa?{ca:sslCa}:{})}});
  const withTx=async fn=>{const c=await db.connect();try{await c.query('BEGIN');const v=await fn(c);await c.query('COMMIT');return v}catch(e){try{await c.query('ROLLBACK')}catch{}throw e}finally{c.release()}};
  return {
    async list({limit=100,offset=0,status='',classification='',sourceNumber=SOURCE_NUMBER}={}){
      if(!SOURCE_NUMBERS.includes(sourceNumber))throw Error('Invalid source number');
      const params=[sourceNumber,limit,offset];let where='WHERE source_number=$1';
      if(status==='not_pushed'){where+=" AND status IN ('pending','excluded')"} else if(status==='promoted'){where+=" AND status='promoted'"} else if(status){params.push(status);where+=' AND status=$'+params.length}
      if(classification){params.push(classification);where+=' AND classification_code=$'+params.length}
      const r=await db.query('SELECT id,source_number,phone,classification_code,classification_label,classification_source,confidence,status,evidence,first_seen_at,last_seen_at,classified_at,promoted_at,lead_id FROM crm_contact_classifications '+where+' ORDER BY last_seen_at DESC,id DESC LIMIT $2 OFFSET $3',params);
      const n=await db.query('SELECT count(*)::int AS total FROM crm_contact_classifications WHERE source_number=$1',[sourceNumber]);
      return {classifications:r.rows,total:n.rows[0].total};
    },
    async classify({id,code,source='operator',confidence=null,actor='operator'}){
      const allowed=new Set(['qualified_lead','personal_family','agent_partner','business','promotion','vendor_supplier','internal','cold_inquiry','property_listing_sent','unknown']);
      if(!allowed.has(code))throw Error('Invalid classification');
      return withTx(async c=>{
        let stage='lock classification';
        try {
        const row=(await c.query('SELECT * FROM crm_contact_classifications WHERE id=$1 AND source_number=$2 FOR UPDATE',[id,SOURCE_NUMBER])).rows[0];
        if(!row)throw Object.assign(Error('Classification not found'),{statusCode:404});
        const labels={
          qualified_lead:'Qualified Lead',
          personal_family:'Family / personal',
          agent_partner:'Agent / Partner',
          business:'Business',
          promotion:'Promotion / Marketing',
          vendor_supplier:'Vendor / Supplier',
          internal:'Internal',
          cold_inquiry:'Cold Inquiry',
          property_listing_sent:'Property Listing Sent',
          unknown:'Unknown'
        };
        const label=labels[code];
        stage='excluded classification';
        if(code!=='qualified_lead'){
          stage='promote classification';
        await c.query('UPDATE crm_contact_classifications SET classification_code=$1,classification_label=$2,classification_source=$3,confidence=$4,status=\'excluded\',classified_at=now(),last_seen_at=greatest(last_seen_at,now()) WHERE id=$5',[code,label,source,confidence,id]);
          stage='link existing messages';
        await c.query('UPDATE crm_messages SET classification_id=$1 WHERE classification_id=$1',[id]);
          return {status:'excluded',classification:code,lead_id:null};
        }
        stage='find existing lead';
        let lead=(await c.query('SELECT l.* FROM crm_leads l JOIN crm_lead_sources s ON s.lead_id=l.id WHERE s.source_number=$1 AND s.source_contact_id=$2 LIMIT 1 FOR UPDATE OF l',[SOURCE_NUMBER,row.phone])).rows[0];
        if(!lead){
          stage='generate lead id';
          const leadId='L-LIVE-'+(await c.query("SELECT substr(encode(digest($1||chr(124)||$2,'sha256'),'hex'),1,20) AS h",[SOURCE_NUMBER,row.phone])).rows[0].h;
          stage='insert lead';
          await c.query('INSERT INTO crm_leads(id,display_name,normalized_phone,status,priority,classification,classification_id,lead_type,requirements,operator_notes) VALUES($1,$2,$3,\'New\',\'Medium\',\'Qualified Lead\',$4,\'New\',jsonb_build_object(\'provenance\',\'whatsapp_classification\',\'source_number\',$5),$6) ON CONFLICT(id) DO NOTHING',[leadId,null,row.phone,id,SOURCE_NUMBER,'Classified by '+actor]);
          stage='insert lead source';
          await c.query('INSERT INTO crm_lead_sources(lead_id,source_number,source_contact_id) VALUES($1,$2,$3) ON CONFLICT DO NOTHING',[leadId,SOURCE_NUMBER,row.phone]);
          stage='reload lead';
          lead=(await c.query('SELECT * FROM crm_leads WHERE id=$1 FOR UPDATE',[leadId])).rows[0];
        }else{
          stage='update existing lead';
          await c.query('UPDATE crm_leads SET classification=\'Qualified Lead\',classification_id=$1 WHERE id=$2',[id,lead.id]);
        }
        await c.query('UPDATE crm_contact_classifications SET classification_code=$1,classification_label=$2,classification_source=$3,confidence=$4,status=\'promoted\',classified_at=now(),promoted_at=coalesce(promoted_at,now()),lead_id=$5 WHERE id=$6',[code,label,source,confidence,lead.id,id]);
        await c.query('UPDATE crm_messages SET lead_id=$1,classification_id=$2 WHERE classification_id=$2',[lead.id,id]);
        stage='load webhook events';
        const events=(await c.query('SELECT id,provider_event_id,direction,message_type,payload,message_at FROM crm_webhook_events WHERE source_number=$1 AND phone=$2 AND provider_event_id IS NOT NULL ORDER BY message_at ASC,id ASC',[SOURCE_NUMBER,row.phone])).rows;
        for(const e of events){
          const m=e.payload||{};let body=null;
          if(m.text&&typeof m.text==='object')body=String(m.text.body||'').trim()||null;
          const media=[];
          for(const k of ['image','video','document','audio'])if(m[k]&&typeof m[k]==='object'&&(m[k].link||m[k].url))media.push(String(m[k].link||m[k].url));
          stage='insert webhook message';
          await c.query('INSERT INTO crm_messages(lead_id,classification_id,source_number,provider_message_id,direction,message_type,body,sender_name,media_urls,message_at) VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10) ON CONFLICT DO NOTHING',[lead.id,id,SOURCE_NUMBER,e.provider_event_id,e.direction||'Incoming',e.message_type||'text',body,null,media.length?media:null,e.message_at]);
        }
        return {status:'promoted',classification:'qualified_lead',lead_id:lead.id};
        } catch (e) {
          console.error(JSON.stringify({event:'crm_classification_failure',classification_id:id,code,stage,error_code:e?.code||null,error_message:e?.message||String(e),detail:e?.detail||null,hint:e?.hint||null,table:e?.table||null,column:e?.column||null,constraint:e?.constraint||null}));
          throw e;
        }
      });
    },
    async close(){await db.end()}
  };
}