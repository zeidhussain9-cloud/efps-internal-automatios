import pg from 'pg';
import {createCrmRepository,normalizeConnectionString} from './crm-repository.mjs';

const SOURCE_NUMBERS=['+919148338801','+917975102130','+919902024973'];
const SOURCE_NUMBER=SOURCE_NUMBERS[0];
export const normalizeDisplayName=value=>{const v=String(value??'').replace(/\s+/g,' ').trim();if(!v||/^(?:you|easyfind(?: property solutions)?)$/i.test(v)||!/[A-Za-z]/.test(v)||v.replace(/[^A-Za-z]/g,'').length<3)return null;return v};

export function createCrmClassificationRepository({connectionString=process.env.DATABASE_URL,sslCa=process.env.DATABASE_SSL_CA}={}){
 if(!connectionString)throw Error('DATABASE_URL required');
 const db=new pg.Pool({connectionString:normalizeConnectionString(connectionString),max:3,connectionTimeoutMillis:5000,ssl:{rejectUnauthorized:true,...(sslCa?{ca:sslCa}:{})}});
 const withTx=async fn=>{const c=await db.connect();try{await c.query('BEGIN');const v=await fn(c);await c.query('COMMIT');return v}catch(e){try{await c.query('ROLLBACK')}catch{}throw e}finally{c.release()}};
 return {
  async list({limit=100,offset=0,status='',classification='',sourceNumber=SOURCE_NUMBER}={}){
   if(!SOURCE_NUMBERS.includes(sourceNumber))throw Error('Invalid source number');
   if(!Number.isInteger(limit)||limit<1||limit>100||!Number.isInteger(offset)||offset<0)throw Error('Invalid pagination');
   const params=[sourceNumber];let where='WHERE source_number=$1';
   if(status==='not_pushed')where+=" AND status='pending'";else if(status==='promoted')where+=" AND status='promoted'";else if(status==='unqualified')where+=" AND status='excluded'";else if(status){params.push(status);where+=' AND status=$'+params.length}
   if(classification){params.push(classification);where+=' AND classification_code=$'+params.length}
   const countParams=params.slice(),limitPos=params.push(limit),offsetPos=params.push(offset);
   const r=await db.query('SELECT id,source_number,phone,classification_code,classification_label,classification_source,confidence,status,evidence,first_seen_at,last_seen_at,classified_at,promoted_at,lead_id FROM crm_contact_classifications '+where+' ORDER BY last_seen_at DESC,id DESC LIMIT $'+limitPos+' OFFSET $'+offsetPos,params);
   const n=await db.query('SELECT count(*)::int AS total FROM crm_contact_classifications '+where,countParams);
   return{classifications:r.rows,total:n.rows[0].total};
  },

  async listDeterministicCandidates({sourceNumber=SOURCE_NUMBER,limit=100}={}){
   if(!SOURCE_NUMBERS.includes(sourceNumber)||!Number.isInteger(limit)||limit<1||limit>500)throw Error('Invalid deterministic candidate query');
   const r=await db.query(`SELECT c.id,c.source_number,c.phone,c.classification_code,c.status,c.last_seen_at,c.deterministic_last_evaluated_at,c.deterministic_last_evaluated_message_id
     FROM crm_contact_classifications c
     WHERE c.source_number=$1 AND c.status='pending'
       AND (c.deterministic_last_evaluated_at IS NULL OR c.last_seen_at>c.deterministic_last_evaluated_at)
     ORDER BY c.last_seen_at ASC,c.id ASC
     LIMIT $2`,[sourceNumber,limit]);
   return r.rows;
  },

  async getDeterministicContact({id,sourceNumber=SOURCE_NUMBER}={}){
   const contactId=Number(id);if(!Number.isInteger(contactId)||contactId<1||!SOURCE_NUMBERS.includes(sourceNumber))throw Error('Invalid deterministic contact');
   const [classification,messages,events]=await Promise.all([
    db.query('SELECT * FROM crm_contact_classifications WHERE id=$1 AND source_number=$2',[contactId,sourceNumber]),
    db.query('SELECT id,classification_id,source_number,provider_message_id,source_message_id,direction,message_type,body,sender_name,replied_to_source_message_id,message_at FROM crm_messages WHERE classification_id=$1 ORDER BY message_at ASC,id ASC',[contactId]),
    db.query('SELECT id,provider_event_id,direction,message_type,payload,message_at FROM crm_webhook_events WHERE source_number=$1 AND phone=(SELECT phone FROM crm_contact_classifications WHERE id=$2) ORDER BY message_at ASC,id ASC',[sourceNumber,contactId])
   ]);
   return{classification:classification.rows[0]||null,messages:messages.rows,webhookEvents:events.rows};
  },

  async markDeterministicEvaluation({id,latestMessageId=null,latestMessageAt=null,decision,ruleVersion}={}){
   const contactId=Number(id);if(!Number.isInteger(contactId)||contactId<1)throw Error('Invalid deterministic evaluation');
   const evidence={deterministic:{rule_id:decision?.rule_id||'PENDING-01-INSUFFICIENT',rule_version:ruleVersion||null,reason:decision?.reason||'',signals:decision?.signals||[],evidence_message_ids:decision?.evidence_message_ids||[],evidence_webhook_event_ids:decision?.evidence_webhook_event_ids||[],evaluated_at:new Date().toISOString()}};
   const r=await db.query(`UPDATE crm_contact_classifications
     SET deterministic_last_evaluated_at=now(),deterministic_last_evaluated_message_id=$1,deterministic_last_evaluated_message_at=$2,deterministic_rule_version=$3,
         evidence=COALESCE(evidence,'{}'::jsonb)||$4::jsonb
     WHERE id=$5 RETURNING id,status,classification_code,deterministic_last_evaluated_at`,[latestMessageId,latestMessageAt,ruleVersion,JSON.stringify(evidence),contactId]);
   return r.rows[0]||null;
  },

  async appendDeterministicAudit({classificationId,phone,decision,runId}={}){
   return (await db.query('INSERT INTO crm_activity(lead_id,actor,action,details) VALUES(NULL,$1,$2,$3::jsonb) RETURNING *',[
    'system:deterministic-classifier','classification.deterministic_evaluated',
    JSON.stringify({classification_id:classificationId,phone,run_id:runId,outcome:decision?.outcome||'pending',classification:decision?.classification_code||'pending',rule_id:decision?.rule_id||null,rule_version:decision?.rule_version||null,reason:decision?.reason||'',evidence_message_ids:decision?.evidence_message_ids||[],evidence_webhook_event_ids:decision?.evidence_webhook_event_ids||[],signals:decision?.signals||[]})
   ])).rows[0];
  },

  async classify({id,code,source='operator',confidence=null,actor='operator',evidencePatch=null,autoQualified=false,runId=null}){
   const allowed=new Set(['qualified_lead','personal_family','agent_partner','business','promotion','vendor_supplier','internal','cold_inquiry','property_listing_sent','group_message','unknown']);
   if(!allowed.has(code))throw Error('Invalid classification');
   if(source==='deterministic_rule'&&code==='property_listing_sent')throw Error('Deterministic engine cannot generate Property Listing Sent');
   return withTx(async c=>{
    const row=(await c.query('SELECT * FROM crm_contact_classifications WHERE id=$1 AND source_number=$2 FOR UPDATE',[id,SOURCE_NUMBER])).rows[0];
    if(!row)throw Object.assign(Error('Classification not found'),{statusCode:404});
    const labels={qualified_lead:'Qualified Lead',personal_family:'Family / personal',agent_partner:'Agent / Partner',business:'Business',promotion:'Promotion / Marketing',vendor_supplier:'Vendor / Supplier',internal:'Internal',cold_inquiry:'Cold Inquiry',property_listing_sent:'Property Listing Sent',group_message:'Group Message',unknown:'Unknown'};
    const label=labels[code],patch=evidencePatch?JSON.stringify(evidencePatch):null;

    if(code!=='qualified_lead'){
     await c.query(`UPDATE crm_contact_classifications
       SET classification_code=$1,classification_label=$2,classification_source=$3,confidence=$4,status='excluded',classified_at=now(),last_seen_at=greatest(last_seen_at,now()),evidence=CASE WHEN $5::jsonb IS NULL THEN evidence ELSE COALESCE(evidence,'{}'::jsonb)||$5::jsonb END
       WHERE id=$6`,[code,label,source,confidence,patch,id]);
     await c.query('UPDATE crm_messages SET classification_id=$1 WHERE classification_id=$1',[id]);
     await c.query('INSERT INTO crm_activity(lead_id,actor,action,details) VALUES(NULL,$1,$2,$3::jsonb)',[actor,'contact.classified',JSON.stringify({classification_id:id,phone:row.phone,classification:code,status:'excluded',classification_source:source,run_id:runId,evidence:evidencePatch||null})]);
     return{status:'excluded',classification:code,lead_id:null};
    }

    const nameRow=(await c.query("SELECT trim(sender_name) AS name FROM crm_messages WHERE classification_id=$1 AND direction='Incoming' AND sender_name IS NOT NULL AND trim(sender_name)<>'' ORDER BY message_at DESC,id DESC LIMIT 1",[id])).rows[0];
    const contactName=normalizeDisplayName(nameRow?.name);
    let lead=(await c.query('SELECT l.* FROM crm_leads l JOIN crm_lead_sources s ON s.lead_id=l.id WHERE s.source_number=$1 AND s.source_contact_id=$2 LIMIT 1 FOR UPDATE OF l',[SOURCE_NUMBER,row.phone])).rows[0];
    if(!lead){
     const leadId='L-LIVE-'+(await c.query("SELECT substr(encode(digest($1||chr(124)||$2,'sha256'),'hex'),1,20) AS h",[SOURCE_NUMBER,row.phone])).rows[0].h;
     await c.query(`INSERT INTO crm_leads(id,display_name,normalized_phone,status,priority,classification,classification_id,lead_type,requirements,operator_notes,auto_qualified)
       VALUES($1,$2,$3,'New','Medium','Qualified Lead',$4,'New',jsonb_build_object('provenance','whatsapp_classification','source_number',$5::text),$6,$7)
       ON CONFLICT(id) DO NOTHING`,[leadId,contactName,row.phone,id,SOURCE_NUMBER,'Classified by '+actor,Boolean(autoQualified)]);
     await c.query('INSERT INTO crm_lead_sources(lead_id,source_number,source_contact_id) VALUES($1,$2,$3) ON CONFLICT DO NOTHING',[leadId,SOURCE_NUMBER,row.phone]);
     lead=(await c.query('SELECT * FROM crm_leads WHERE id=$1 FOR UPDATE',[leadId])).rows[0];
    }else{
     await c.query('UPDATE crm_leads SET classification=\'Qualified Lead\',classification_id=$1,auto_qualified=$2,display_name=CASE WHEN (display_name IS NULL OR btrim(display_name)=\'\') THEN $3 ELSE display_name END,updated_at=now() WHERE id=$4',[id,Boolean(autoQualified),contactName,lead.id]);
    }
    await c.query(`UPDATE crm_contact_classifications
      SET classification_code='qualified_lead',classification_label='Qualified Lead',classification_source=$1,confidence=$2,status='promoted',classified_at=now(),promoted_at=coalesce(promoted_at,now()),lead_id=$3,
          evidence=CASE WHEN $4::jsonb IS NULL THEN evidence ELSE COALESCE(evidence,'{}'::jsonb)||$4::jsonb END
      WHERE id=$5`,[source,confidence,lead.id,patch,id]);
    await c.query('UPDATE crm_messages SET lead_id=$1,classification_id=$2 WHERE classification_id=$2',[lead.id,id]);
    await c.query(`UPDATE crm_webhook_events e
      SET lead_id=$1,message_id=coalesce(e.message_id,m.id)
      FROM crm_messages m
      WHERE e.source_number=$2 AND e.phone=$3 AND m.source_number=e.source_number
        AND m.provider_message_id=e.provider_event_id AND m.lead_id=$1
        AND (e.lead_id IS DISTINCT FROM $1 OR e.message_id IS DISTINCT FROM m.id)`,[lead.id,SOURCE_NUMBER,row.phone]);
    const events=(await c.query('SELECT id,provider_event_id,direction,message_type,payload,message_at FROM crm_webhook_events WHERE source_number=$1 AND phone=$2 AND provider_event_id IS NOT NULL ORDER BY message_at ASC,id ASC',[SOURCE_NUMBER,row.phone])).rows;
    await c.query('INSERT INTO crm_activity(lead_id,actor,action,details) VALUES($1,$2,$3,$4::jsonb)',[lead.id,actor,'contact.classified',JSON.stringify({classification_id:id,classification:'qualified_lead',status:'promoted',source_number:SOURCE_NUMBER,classification_source:source,auto_qualified:Boolean(autoQualified),run_id:runId,evidence:evidencePatch||null})]);
    for(const e of events){
     const m=e.payload||{};let body=null;if(m.text&&typeof m.text==='object')body=String(m.text.body||'').trim()||null;
     const media=[];for(const k of ['image','video','document','audio'])if(m[k]&&typeof m[k]==='object'&&(m[k].link||m[k].url))media.push(String(m[k].link||m[k].url));
     await c.query('INSERT INTO crm_messages(lead_id,classification_id,source_number,provider_message_id,direction,message_type,body,sender_name,media_urls,message_at) VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10) ON CONFLICT DO NOTHING',[lead.id,id,SOURCE_NUMBER,e.provider_event_id,e.direction||'Incoming',e.message_type||'text',body,null,media.length?media:null,e.message_at]);
    }
    return{status:'promoted',classification:'qualified_lead',lead_id:lead.id};
   });
  },

  async close(){await db.end()}
 };
}
