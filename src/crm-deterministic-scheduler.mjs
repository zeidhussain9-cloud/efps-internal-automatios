import crypto from 'node:crypto';
import pg from 'pg';
import {normalizeConnectionString} from './crm-repository.mjs';
import {createCrmClassificationRepository} from './crm-classification-repository.mjs';
import {classifyDeterministically,DETERMINISTIC_ACTOR,DETERMINISTIC_RULE_VERSION} from './crm-deterministic-classifier.mjs';

const SOURCE_NUMBER='+919148338801';
const LOCK_KEY='efps.crm.deterministic.scheduler';

export function createDeterministicScheduler({connectionString=process.env.DATABASE_URL,sslCa=process.env.DATABASE_SSL_CA}={}){
 if(!connectionString)throw Error('DATABASE_URL required');
 const db=new pg.Pool({connectionString:normalizeConnectionString(connectionString),max:4,connectionTimeoutMillis:5000,ssl:{rejectUnauthorized:true,...(sslCa?{ca:sslCa}:{})}});
 const classifications=createCrmClassificationRepository({connectionString,sslCa});

 async function run({dryRun=false,limit=500,actor=DETERMINISTIC_ACTOR}={}){
  if(!Number.isInteger(limit)||limit<1||limit>500)throw Error('Invalid deterministic batch limit');
  const client=await db.connect();
  let locked=false;
  const runId=crypto.randomUUID();
  try{
   locked=Boolean((await client.query("SELECT pg_try_advisory_lock(hashtext($1)) AS locked",[LOCK_KEY])).rows[0]?.locked);
   if(!locked)return{locked:false,run_id:null,status:'skipped',reason:'scheduler_already_running'};
   await client.query('INSERT INTO crm_deterministic_scheduler_runs(id,invocation_source,status,details) VALUES($1,$2,$3,$4::jsonb)',[runId,dryRun?'dry_run':'scheduled_1h',dryRun?'dry_run':'running',JSON.stringify({source_number:SOURCE_NUMBER,batch_limit:limit,rule_version:DETERMINISTIC_RULE_VERSION,no_ai:true})]);
   const candidates=await classifications.listDeterministicCandidates({sourceNumber:SOURCE_NUMBER,limit});
   const counts={candidates_considered:candidates.length,qualified_count:0,unqualified_count:0,pending_count:0,skipped_count:0,failed_count:0};
   for(const candidate of candidates){
    try{
     const contact=await classifications.getDeterministicContact({id:candidate.id,sourceNumber:SOURCE_NUMBER});
     if(!contact.classification){counts.skipped_count++;continue;}
     const decision=classifyDeterministically({messages:contact.messages,webhookEvents:contact.webhookEvents});
     const latest=contact.messages.at(-1)||null;
     const patch={deterministic:{rule_id:decision.rule_id,rule_version:decision.rule_version,reason:decision.reason,signals:decision.signals,evidence_message_ids:decision.evidence_message_ids,evidence_webhook_event_ids:decision.evidence_webhook_event_ids,outcome:decision.outcome,evaluated_at:new Date().toISOString()}};
     if(dryRun){
      if(decision.outcome==='qualified')counts.qualified_count++;
      else if(decision.outcome==='unqualified')counts.unqualified_count++;
      else counts.pending_count++;
      continue;
     }
     if(decision.outcome==='qualified'){
      await classifications.classify({id:candidate.id,code:'qualified_lead',source:'deterministic_rule',confidence:1,actor,autoQualified:true,runId,evidencePatch:patch});
      counts.qualified_count++;
     }else if(decision.outcome==='unqualified'){
      await classifications.classify({id:candidate.id,code:decision.classification_code,source:'deterministic_rule',confidence:1,actor,autoQualified:false,runId,evidencePatch:patch});
      counts.unqualified_count++;
     }else{
      counts.pending_count++;
     }
     if(latest){
      await classifications.markDeterministicEvaluation({id:candidate.id,latestMessageId:latest.id,latestMessageAt:latest.message_at,decision,ruleVersion:DETERMINISTIC_RULE_VERSION});
     }else{
      await classifications.markDeterministicEvaluation({id:candidate.id,decision,ruleVersion:DETERMINISTIC_RULE_VERSION});
     }
     await classifications.appendDeterministicAudit({classificationId:candidate.id,phone:candidate.phone,decision,runId});
    }catch(error){
     counts.failed_count++;
     if(!dryRun)await classifications.appendDeterministicAudit({classificationId:candidate.id,phone:candidate.phone,decision:{outcome:'failed',classification_code:'pending',rule_id:'SYSTEM-ERROR',rule_version:DETERMINISTIC_RULE_VERSION,reason:'Deterministic evaluation failed; contact remains unchanged.',evidence_message_ids:[],evidence_webhook_event_ids:[],signals:[]},runId});
    }
   }
   const status=counts.failed_count?'partial':'completed';
   if(dryRun)await client.query('UPDATE crm_deterministic_scheduler_runs SET status=$1,completed_at=now(),candidates_considered=$2,qualified_count=$3,unqualified_count=$4,pending_count=$5,skipped_count=$6,failed_count=$7,details=details||$8::jsonb WHERE id=$9',['dry_run',counts.candidates_considered,counts.qualified_count,counts.unqualified_count,counts.pending_count,counts.skipped_count,counts.failed_count,JSON.stringify({dry_run:true}),runId]);
   else await client.query('UPDATE crm_deterministic_scheduler_runs SET status=$1,completed_at=now(),candidates_considered=$2,qualified_count=$3,unqualified_count=$4,pending_count=$5,skipped_count=$6,failed_count=$7 WHERE id=$8',[status,counts.candidates_considered,counts.qualified_count,counts.unqualified_count,counts.pending_count,counts.skipped_count,counts.failed_count,runId]);
   return{locked:true,run_id:runId,status,candidates_considered:counts.candidates_considered,qualified_count:counts.qualified_count,unqualified_count:counts.unqualified_count,pending_count:counts.pending_count,skipped_count:counts.skipped_count,failed_count:counts.failed_count,dry_run:dryRun,rule_version:DETERMINISTIC_RULE_VERSION,no_ai:true};
  }catch(error){
   if(locked)await client.query('UPDATE crm_deterministic_scheduler_runs SET status=$1,completed_at=now(),error_summary=$2 WHERE id=$3',['failed','scheduler_failed',runId]).catch(()=>{});
   throw error;
  }finally{
   if(locked)await client.query("SELECT pg_advisory_unlock(hashtext($1))",[LOCK_KEY]).catch(()=>{});
   client.release();
  }
 }
 return{run,close:async()=>{await classifications.close();await db.end()}};
}
