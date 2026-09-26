// Server-side Ollama adapter. Disabled until the synthetic pilot gate is explicitly enabled.
const allowed=new Set(['L-1001','L-1002','L-1003','L-1004']);
export function ollamaSettings(env){const base=env.OLLAMA_BASE_URL||env.OLLAMA_HOST;const model=env.OLLAMA_MODEL||env.OLLAMA_MODEL_NAME;return {ready:Boolean(base&&model),base,model,hasKey:Boolean(env.OLLAMA_API_KEY)};}
export async function analyzeFictionalLead({leadId,env,fetcher=fetch}){
 if(env.CRM_SYNTHETIC_AI_ENABLED!=='true')throw Error('Synthetic AI disabled');
 if(!allowed.has(leadId))throw Error('Unknown fictional lead');
 const config=ollamaSettings(env);if(!config.ready)throw Error('Ollama provider configuration incomplete');
 const fixture={
 'L-1001':'Fictional renter: 2 BHK Harlur, budget INR 50000, pet friendly preferred. Human-confirmed budget INR 52000.',
 'L-1002':'Fictional renter: 1 BHK Bellandur, budget INR 34000, move next month.',
 'L-1003':'Fictional renter: 3 BHK Whitefield, budget INR 80000, availability uncertain.',
 'L-1004':'Fictional renter: 2 BHK Sarjapur Road, budget INR 60000, wants a viewing.'
 }[leadId];
 const endpoint=new URL('/api/chat',config.base);if(endpoint.protocol!=='https:'&&endpoint.hostname!=='localhost'&&endpoint.hostname!=='127.0.0.1')throw Error('Insecure Ollama endpoint');
 const controller=new AbortController();const timeout=setTimeout(()=>controller.abort(),20000);
 try{
  const response=await fetcher(endpoint,{method:'POST',headers:{'Content-Type':'application/json',...(env.OLLAMA_API_KEY?{Authorization:'Bearer '+env.OLLAMA_API_KEY}:{})},body:JSON.stringify({model:config.model,stream:false,format:'json',messages:[{role:'system',content:'Extract fictional rental requirements. Return JSON with keys bhk,location,budget,pets,uncertainties. Do not invent missing facts or propose sending messages.'},{role:'user',content:fixture}]}),signal:controller.signal});
  if(!response.ok)throw Error('Ollama request failed ('+response.status+')');
  const body=await response.json();const parsed=JSON.parse(body?.message?.content||'null');
  if(!parsed||typeof parsed!=='object'||Array.isArray(parsed))throw Error('Invalid model JSON');
  return {leadId,provider:'ollama',model:config.model,proposal:parsed,fictional:true};
 }finally{clearTimeout(timeout)}
}
