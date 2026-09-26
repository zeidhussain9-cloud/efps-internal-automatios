// Pure, non-PII migration planning. No database connections or external writes.
export const VERIFIED_SOURCE_NUMBERS=Object.freeze(['+919148338801','+917975102130','+919902024973']);
export function normalizeMessage(row){
 if(!row||typeof row!=='object')throw Error('Message row required');
 const source=String(row.source_number||'').trim(),providerId=String(row.provider_message_id||'').trim();
 if(!VERIFIED_SOURCE_NUMBERS.includes(source))throw Error('Unknown source number');
 if(!providerId)throw Error('Stable provider message ID required');
 if(!row.lead_id)throw Error('Lead ID required');
 if(!['Incoming','Outgoing'].includes(row.direction))throw Error('Invalid direction');
 const date=new Date(row.message_at);if(!Number.isFinite(date.valueOf()))throw Error('Invalid message timestamp');
 return{lead_id:String(row.lead_id),source_number:source,provider_message_id:providerId,direction:row.direction,message_type:String(row.message_type||'text'),body:row.body==null?null:String(row.body),message_at:date.toISOString()};
}
export function planMessageImport(rows,existingKeys=[]){
 const seen=new Set(existingKeys),insert=[],duplicates=[];
 for(const row of rows){const normalized=normalizeMessage(row),key=normalized.source_number+'\u0000'+normalized.provider_message_id;if(seen.has(key)){duplicates.push(key);continue}seen.add(key);insert.push(normalized)}
 return{insert,duplicateCount:duplicates.length,sourceCounts:Object.fromEntries(VERIFIED_SOURCE_NUMBERS.map(source=>[source,insert.filter(row=>row.source_number===source).length]))};
}
export function assertHistoricalCoverage({leads,messages,earliest,latest}){
 if(!Number.isInteger(leads)||leads<0||!Number.isInteger(messages)||messages<0)throw Error('Invalid source counts');
 if(!earliest||!latest||new Date(earliest)>new Date(latest))throw Error('Invalid extraction time range');
 return{leads,messages,earliest,latest,approvedForImport:false,requiresSourceReconciliation:true};
}
