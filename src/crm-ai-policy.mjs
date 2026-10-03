const VALID_STATUSES=new Set(['New','Active Follow-up','Waiting on Customer','Waiting on Us','Nurture','Dormant','Converted','Lost','On Hold','Out of Coverage Area']);
const SAFE_AUTO_STATUSES=new Set(['New','Active Follow-up','Waiting on Customer','Waiting on Us','Nurture','Dormant']);
const HIGH_CONSEQUENCE_STATUSES=new Set(['Converted','Lost','Out of Coverage Area','On Hold']);
export function latestMessage(messages=[]){return Array.isArray(messages)&&messages.length?messages[messages.length-1]:null}
export function evaluationSignals({workspace,now=new Date()}={}){
 const c=workspace?.ai_cursor||{}, lea=c.last_evaluated_at?new Date(c.last_evaluated_at):null, lma=c.last_evaluated_message_at?new Date(c.last_evaluated_message_at):null, lmi=Number(c.last_evaluated_message_id||0), latest=latestMessage(workspace?.messages||[]);
 const hasNewMessage=Boolean(latest&&(!lma||new Date(latest.message_at)>lma||(new Date(latest.message_at).getTime()===lma.getTime()&&Number(latest.id)>lmi)));
 const requirementUpdatedAt=workspace?.requirement_profile?.updated_at?new Date(workspace.requirement_profile.updated_at):null;
 const requirementsChanged=Boolean(requirementUpdatedAt&&(!lea||requirementUpdatedAt>lea));
 const overdueFollowupChanged=Boolean((workspace?.followups||[]).some(f=>!f.completed_at&&new Date(f.due_at)<now&&(!lea||new Date(f.due_at)>lea)));
 const activityChanged=Boolean((workspace?.activity||[]).some(a=>!String(a.action||'').startsWith('ai.')&&(!lea||new Date(a.occurred_at)>lea)));
 return{hasNewMessage,requirementsChanged,overdueFollowupChanged,activityChanged,latestMessageId:latest?.id??null,latestMessageAt:latest?.message_at??null,reason:[hasNewMessage?'new_reconciled_message':null,requirementsChanged?'requirements_changed':null,overdueFollowupChanged?'overdue_followup':null,activityChanged?'meaningful_crm_activity':null].filter(Boolean).join(',')||'no_meaningful_change'};
}
export function hasMeaningfulDelta(args){return evaluationSignals(args).reason!=='no_meaningful_change'}
export function deterministicStatus({lead,messages=[]}={}){
 const current=String(lead?.lead_type||'');
 if(HIGH_CONSEQUENCE_STATUSES.has(current))return{status:null,action:'review_required',reason:'Current status is a higher-consequence state and is not changed automatically.',evidence_message_ids:[]};
 const last=latestMessage(messages); if(!last||!['Incoming','Outgoing'].includes(last.direction))return{status:null,action:'no_change',reason:'No deterministic message-direction status is available.',evidence_message_ids:[]};
 const status=last.direction==='Incoming'?'Waiting on Us':'Waiting on Customer';
 if(status===current)return{status:null,action:'no_change',reason:'Latest reconciled message already matches the operational lead status.',evidence_message_ids:[last.id]};
 return{status,action:'auto_apply',reason:`Latest reconciled ${last.direction.toLowerCase()} message establishes the operational waiting state without requiring conversation interpretation.`,evidence_message_ids:[last.id]};
}
export function normalizeStatusSuggestion(value){
 const raw=value&&typeof value==='object'?value:{}, requested=typeof raw.status==='string'?raw.status.trim():typeof value==='string'?value.trim():'';
 const status=VALID_STATUSES.has(requested)?requested:null, evidenceRaw=Array.isArray(raw.evidence_message_ids)?raw.evidence_message_ids:Array.isArray(raw.source_message_ids)?raw.source_message_ids:[];
 const evidence_message_ids=[...new Set(evidenceRaw.map(Number).filter(Number.isInteger))], confidence=Number.isFinite(Number(raw.confidence))?Math.max(0,Math.min(1,Number(raw.confidence))):null;
 return{status,reason:String(raw.reason||'No supported status change was established.'),evidence_message_ids,confidence,needs_review:raw.needs_review===false?false:true};
}
export function statusDecision({lead,statusSuggestion}={}){
 const current=String(lead?.lead_type||''), suggestion=normalizeStatusSuggestion(statusSuggestion);
 if(!suggestion.status||suggestion.status===current)return{...suggestion,action:'no_change'};
 const autoSafe=SAFE_AUTO_STATUSES.has(suggestion.status)&&suggestion.confidence!==null&&suggestion.confidence>=0.85&&!suggestion.needs_review&&suggestion.evidence_message_ids.length>0;
 return{...suggestion,action:autoSafe?'auto_apply':'review_required'};
}
export const COVERAGE_AREAS=new Set(['HSR Layout','Kudlu Gate','Bellandur','Sarjapur Road','Whitefield','Hoodi','Mahadevapura','Marathahalli','ITPL','Varthur','Kasavanahalli','Harlur','Panathur','Yemalur','Old Airport Road']);
const SELECTIVE_COVERAGE_AREAS=new Set(['Koramangala','Bommanahalli','Old Airport Road']);
const OUT_OF_COVERAGE_AREAS=new Set(['Jayanagar','BTM Layout','JP Nagar','Electronic City','Carmelaram','Parappana Agrahara','Viman Nagar','Ulsoor','Fraser Town','Jeevanbhima Nagar']);
const COVERAGE_ALIASES=new Map([
 ['hsr','HSR Layout'],['haralur','Harlur'],['harlur','Harlur'],['kudlu','Kudlu Gate'],['marathalli','Marathahalli'],
 ['yemlur','Yemalur'],['mahadevpura','Mahadevapura'],['brookefield','Whitefield'],['brookfield','Whitefield'],
 ['old hal airport road','Old Airport Road'],['old airport road','Old Airport Road']
]);
function normalizeCoverageTerm(value=''){const raw=String(value??'').trim().replace(/\\s+/g,' ');if(!raw)return'';const key=raw.toLocaleLowerCase().replace(/[.]/g,'').trim();if(COVERAGE_ALIASES.has(key))return COVERAGE_ALIASES.get(key);for(const area of [...COVERAGE_AREAS,...SELECTIVE_COVERAGE_AREAS,...OUT_OF_COVERAGE_AREAS])if(area.toLocaleLowerCase()===key)return area;return raw;}
export function coverageDecision({lead,requirements={}}={}){
 const current=String(lead?.lead_type||'');
 if(HIGH_CONSEQUENCE_STATUSES.has(current))return{status:null,action:'review_required',reason:'Current status is a higher-consequence state and is not changed automatically.',coverage:'protected',evidence:[]};
 const raw=Array.isArray(requirements?.preferred_locations)?requirements.preferred_locations:[];
 const terms=[...new Set(raw.flatMap(v=>String(v??'').split(/[,;|/]+/).map(x=>x.trim()).filter(Boolean).map(normalizeCoverageTerm)))];
 if(!terms.length)return{status:null,action:'no_change',reason:'No structured preferred location is stored; coverage is not inferred.',coverage:'unknown',evidence:[]};
 const hasSelective=terms.some(t=>SELECTIVE_COVERAGE_AREAS.has(t));
 const knownIn=terms.filter(t=>COVERAGE_AREAS.has(t));
 const knownOut=terms.filter(t=>OUT_OF_COVERAGE_AREAS.has(t));
 const unknown=terms.filter(t=>!COVERAGE_AREAS.has(t)&&!SELECTIVE_COVERAGE_AREAS.has(t)&&!OUT_OF_COVERAGE_AREAS.has(t));
 if(hasSelective)return{status:null,action:'review_required',reason:'A selective service area is requested; automatic geographic assignment is not deterministic for this location.',coverage:'selective',evidence:terms};
 if(knownOut.length&&knownIn.length)return{status:null,action:'review_required',reason:'Requested locations span both in-coverage and out-of-coverage areas; operator review is required.',coverage:'mixed',evidence:terms};
 if(knownOut.length&&!knownIn.length&&!unknown.length)return{status:'Out of Coverage Area',action:current==='Out of Coverage Area'?'no_change':'auto_apply',reason:'All requested preferred locations exactly match the approved deterministic out-of-coverage vocabulary.',coverage:'out_of_coverage',evidence:knownOut};
 if(knownIn.length&&!knownOut.length&&!unknown.length)return{status:null,action:'no_change',reason:'All requested preferred locations exactly match the approved in-coverage vocabulary.',coverage:'in_coverage',evidence:knownIn};
 return{status:null,action:'review_required',reason:'Preferred locations include terms outside the controlled coverage vocabulary; coverage is not inferred from free text.',coverage:'unknown',evidence:terms};
}
export const AI_STATUS_POLICY={VALID_STATUSES,SAFE_AUTO_STATUSES,HIGH_CONSEQUENCE_STATUSES,COVERAGE_AREAS,SELECTIVE_COVERAGE_AREAS,OUT_OF_COVERAGE_AREAS,coverageDecision};
