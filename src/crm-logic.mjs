// Synthetic-preview domain logic. No external writes, network calls or customer data.
export const REQUIREMENT_FIELDS=['bhk','location','budget','furnishing','moveIn','pets','parking','occupancy','notes'];
export const DEFAULT_REQUIREMENTS={furnishing:'Unknown',moveIn:'',pets:'Unknown',parking:'Unknown',occupancy:'Unknown',notes:''};
export function withDefaults(lead){return {...DEFAULT_REQUIREMENTS,...lead};}
export function filterLeads(leads,{source='All sources',queue='All',query='',sort='recent'}={}){
 const q=query.trim().toLocaleLowerCase();
 const result=leads.filter(l=>(source==='All sources'||l.source===source)&&(queue==='All'||queue==='Qualified Leads'&&!['Review','Archived'].includes(l.status)||queue==='Review Queue'&&l.status==='Review'||queue==='Archive'&&l.status==='Archived')&&[l.name,l.phone,l.location,l.text,l.status].join(' ').toLocaleLowerCase().includes(q));
 return [...result].sort((a,b)=>sort==='priority'?({High:0,Medium:1,Low:2}[a.priority]??3)-({High:0,Medium:1,Low:2}[b.priority]??3):sort==='name'?a.name.localeCompare(b.name):0);
}
export function evaluateProperty(property,lead,{excluded=[],pinned=[]}={}){
 const available=property.state==='Available',bhk=property.bhk===lead.bhk,location=property.location.toLocaleLowerCase()===lead.location.toLocaleLowerCase();
 const budget=lead.budget==null||lead.budget===''?null:property.rent<=Number(lead.budget);
 const blocked=excluded.includes(property.id);
 return {...property,match:available&&bhk&&budget!==false&&!blocked,locationMatch:location,budgetMatch:budget,excluded:blocked,pinned:pinned.includes(property.id),reasons:[!available?'Unavailable':null,!bhk?'BHK differs':null,budget===false?'Over budget':null,!location?'Location differs':null,blocked?'Excluded by operator':null].filter(Boolean)};
}
export function validateRequirement(key,value){if(key==='budget')return value===''||value===null||Number.isFinite(Number(value))&&Number(value)>=0;if(key==='bhk')return Number.isInteger(Number(value))&&Number(value)>=1&&Number(value)<=10;return typeof value==='string'&&value.length<=2000;}
export function makeFollowup({id,leadId,at,note}){if(!leadId||!at||!Number.isFinite(Date.parse(at)))throw Error('Lead and valid date required');return {id,leadId,at,note:note?.trim()||'',done:false};}
export function createAudit({leadId,action,details='',at=new Date().toISOString()}){return {lead:leadId,action,details,at};}
export function imageUrls(property){return Array.isArray(property.photos)?property.photos.filter(url=>typeof url==='string'&&/^https:\/\//.test(url)):[];}
