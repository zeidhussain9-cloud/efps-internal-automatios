export function draftPreflight({draft,workspace}){
 const body=String(draft?.body||'');const warnings=[];const blocking=[];
 const latest=workspace.messages?.reduce((a,m)=>!a||new Date(m.message_at)>new Date(a.message_at)?m:a,null);
 if(latest&&new Date(latest.message_at)>new Date(draft.created_at))blocking.push({code:'stale',message:'New CRM activity arrived after this draft was generated.',messageId:latest.id});
 if(!Array.isArray(draft.evidence_message_ids)||draft.evidence_message_ids.length===0)warnings.push({code:'no_evidence',message:'No source message IDs are attached to this draft.'});
 if(/(available|availability|we have|found (?:a|some|the) options|listing|property available|options for you|show you (?:some|the) options)/i.test(body))blocking.push({code:'inventory_claim',message:'Draft appears to make an inventory/availability claim, but no authoritative inventory facts were supplied to the AI run.'});
 const incoming=(workspace.messages||[]).filter(m=>m.direction==='Incoming').map(m=>String(m.body||'')).join(' ');
 const bkh=body.match(/\b([1-5])\s*bhk\b/i);const supportedBhk=incoming.match(/\b([1-5])\s*bhk\b/i);
 if(bkh&&supportedBhk&&bkh[1]!==supportedBhk[1])blocking.push({code:'bhk_mismatch',message:`Draft mentions ${bkh[1]} BHK but conversation evidence supports ${supportedBhk[1]} BHK.`});
 const amounts=[...body.matchAll(/₹?\s*([0-9]{1,3}(?:,[0-9]{3})*|[0-9]+)(?:\s*[-–]\s*₹?\s*([0-9]{1,3}(?:,[0-9]{3})*|[0-9]+))?\s*(?:k|K|000)?/g)].map(x=>x[0].replace(/\s/g,''));
 const incomingNums=(incoming.match(/\b\d[\d,]*(?:\s*[-–]\s*\d[\d,]*)?\s*(?:k|K|000)?\b/g)||[]).map(x=>x.replace(/\s/g,''));
 for(const amount of amounts){if(!incomingNums.some(x=>x===amount||x.includes(amount)||amount.includes(x)))warnings.push({code:'number_check',message:`Numeric value ${amount} should be verified against the conversation before sending.`});}
 if(/\[(?:your|company|name)[^\]]*\]/i.test(body))blocking.push({code:'placeholder',message:'Draft contains an unresolved placeholder.'});
 return{ready:blocking.length===0,warnings,blocking,latestMessageAt:latest?.message_at||null};
}


