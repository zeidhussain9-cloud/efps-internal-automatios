import React,{useEffect,useMemo,useState} from 'react';
import {createRoot} from 'react-dom/client';
import {createClient} from '@supabase/supabase-js';
import {LayoutDashboard,Inbox,Building2,Settings,Search,ChevronLeft,BrainCircuit,CheckCircle2,RefreshCw} from 'lucide-react';
import InventoryPanel from './inventory-panel.jsx';
import './style.css';

const SOURCE_NUMBERS=['+919148338801','+917975102130','+919902024973'];
const SOURCE_NUMBER=SOURCE_NUMBERS[0];
const LEAD_STATUSES=['New','Active Follow-up','Waiting on Customer','Waiting on Us','Nurture','Dormant','Converted','Lost','On Hold'];
const TABS=['Overview','Conversation','Requirements','Property Matches','AI & Drafts','Activity & History'];
const MENU=[['Dashboard',LayoutDashboard],['Contact Classification',Inbox],['Leads Inbox',Inbox],['Inventory',Building2],['Settings',Settings]];
const SUPABASE_URL=import.meta.env.VITE_SUPABASE_URL||'';
const SUPABASE_PUBLISHABLE_KEY=import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY||'';
const supabase=SUPABASE_URL&&SUPABASE_PUBLISHABLE_KEY?createClient(SUPABASE_URL,SUPABASE_PUBLISHABLE_KEY):null;
const money=n=>n!==null&&n!==undefined&&n!==''?'₹'+Number(n).toLocaleString('en-IN'):'Not specified';
const leadTitle=lead=>lead?.display_name||lead?.normalized_phone||'Lead';
const normalizeRequirements=raw=>{
 const r=raw?.fields&&typeof raw.fields==='object'?raw.fields:(raw&&typeof raw==='object'?raw:{});
 const first=(...keys)=>keys.map(k=>r[k]).find(v=>v!==null&&v!==undefined&&String(v).trim()!=='');
 return {
  bhk:first('bhk','bhk_requirement'),
  budget:first('budget','budget_max','max_budget'),
  locality:first('locality','preferred_location','location'),
  furnishing:first('furnishing','furnishing_preference'),
  pet_friendly:first('pet_friendly','pet_preference'),
  tenant_type:first('tenant_type','profile'),
  move_in:first('move_in_date'),
  parking:first('parking_required'),
  current:first('current_requirement'),
 };
};
const requirementEntries=raw=>Object.entries(normalizeRequirements(raw)).filter(([,v])=>v!==null&&v!==undefined&&String(v).trim()!=='');
const classificationLabel=value=>({
 'Qualified Lead':'Actual lead',
 'Agent/Partner':'Agent / broker',
 'Personal/Family':'Family / personal',
 'Vendor/Supplier':'Vendor / supplier',
 'Internal':'Internal / team',
 'Spam/Marketing':'Marketing / spam',
 'Property Listing Sent':'Property listing sent',
 'Cold Inquiry':'Cold inquiry'
}[value]||value||'Unclassified');

function LeadCard({lead,onClick}){
 return <button className="lead-card" onClick={onClick} type="button">
  <div className="lead-card-main"><b>{leadTitle(lead)}</b><span>{lead.display_name?lead.normalized_phone||'No phone stored':''}</span></div>
  <div className="lead-card-meta"><span>{lead.status}</span><span>{lead.priority}</span><span className="classification-chip">{classificationLabel(lead.classification)}</span><span>{lead.source_number||SOURCE_NUMBER}</span></div>
 </button>;
}

function App(){
 const[page,setPage]=useState(()=>{try{return window.sessionStorage.getItem('efps-crm-active-page')||'Dashboard'}catch{return'Dashboard'}});
 const[tab,setTab]=useState('Overview');
 const[query,setQuery]=useState('');
 const[offset,setOffset]=useState(0);
 const[leads,setLeads]=useState([]);
 const[total,setTotal]=useState(0);
 const[loading,setLoading]=useState(true);
 const[error,setError]=useState('');
 const[selectedId,setSelectedId]=useState(null);
 const[workspace,setWorkspace]=useState(null);
 const[workspaceState,setWorkspaceState]=useState('idle');
 const[ai,setAi]=useState(null);
 const[aiState,setAiState]=useState('idle');
 const[inventoryData,setInventoryData]=useState(null);
 const[inventoryState,setInventoryState]=useState('loading');
 const[inventoryQuery,setInventoryQuery]=useState('');
 const[matches,setMatches]=useState([]);
 const[matchState,setMatchState]=useState('idle');
 const[refreshToken,setRefreshToken]=useState(0);
 const[realtimeState,setRealtimeState]=useState('connecting');
 const[classifications,setClassifications]=useState([]);
 const[classificationState,setClassificationState]=useState('idle');
 const[classificationFilter,setClassificationFilter]=useState('not_pushed');
 const[classificationTotal,setClassificationTotal]=useState(0);
 const[sourceFilter,setSourceFilter]=useState(SOURCE_NUMBER);
 const[leadStatusFilter,setLeadStatusFilter]=useState('');
 const[leadStatus,setLeadStatus]=useState('');
 const[realtimeError,setRealtimeError]=useState('');
 const[classificationDrafts,setClassificationDrafts]=useState({});
 const[classificationSaving,setClassificationSaving]=useState({});
 const[classificationErrors,setClassificationErrors]=useState({});
 const[classificationError,setClassificationError]=useState('');
 const[dashboardStats,setDashboardStats]=useState(null);

 useEffect(()=>{try{window.sessionStorage.setItem('efps-crm-active-page',page)}catch{}},[page]);

 useEffect(()=>{
  let active=true;
  async function load(){
   setLoading(true);setError('');
   try{
    const r=await fetch('/api/db/leads?limit=100&offset='+offset+'&source_number='+encodeURIComponent(sourceFilter)+'&lead_status='+encodeURIComponent(leadStatusFilter),{cache:'no-store',credentials:'include'});
    if(!r.ok)throw Error('Live CRM records unavailable');
    const d=await r.json();
    if(!active)return;
    setLeads(Array.isArray(d.leads)?d.leads:[]);
    setTotal(Number(d.total)||0);
   }catch(e){if(active){setError(e.message);setLeads([]);setTotal(0)}}
   finally{if(active)setLoading(false)}
  }
  load();
  return()=>{active=false};
 },[offset,sourceFilter,leadStatusFilter,refreshToken]);

 useEffect(()=>{
  let active=true;
  if(page!=='Contact Classification')return()=>{active=false};
  setClassificationState('loading');
  const qs=new URLSearchParams({limit:'100'});if(['not_pushed','promoted','unqualified'].includes(classificationFilter))qs.set('status',classificationFilter);if(sourceFilter)qs.set('source_number',sourceFilter);
  fetch('/api/db/classifications?'+qs.toString(),{cache:'no-store',credentials:'include'}).then(async r=>{const d=await r.json().catch(()=>({}));if(!r.ok)throw Error(d.error||('Classification records unavailable (HTTP '+r.status+')'));return d}).then(d=>{if(active){const rows=Array.isArray(d.classifications)?d.classifications:[];setClassifications(rows);setClassificationTotal(Number(d.total)||0);setClassificationDrafts(prev=>{const next={...prev};for(const row of rows)next[row.id]=row.classification_code;return next});setClassificationError('');setClassificationState('ready')}}).catch(e=>{if(active){setClassifications([]);setClassificationError(e.message||'Classification records unavailable');setClassificationState('unavailable')}});
  return()=>{active=false};
 },[page,classificationFilter,sourceFilter,refreshToken]);

 useEffect(()=>{
  let active=true;
  fetch('/api/db/stats?source_number='+encodeURIComponent(sourceFilter),{cache:'no-store',credentials:'include'}).then(async r=>{if(!r.ok)throw Error('Dashboard stats unavailable');return r.json()}).then(d=>{if(active)setDashboardStats(d)}).catch(()=>{if(active)setDashboardStats(null)});
  return()=>{active=false};
 },[sourceFilter,refreshToken]);

 useEffect(()=>{
  let active=true;
  async function load(){
   try{
    const r=await fetch('/api/inventory/overview',{cache:'no-store',credentials:'include'});
    if(!r.ok)throw Error('Inventory unavailable');
    const data=await r.json();
    if(active)setInventoryData(data),setInventoryState('live');
   }catch{if(active)setInventoryState('unavailable')}
  }
  load();
  return()=>{active=false};
 },[refreshToken]);

 useEffect(()=>{
  let active=true;
  if(!selectedId){setWorkspace(null);setWorkspaceState('idle');setMatches([]);setMatchState('idle');return()=>{active=false}};
  setWorkspaceState('loading');setAi(null);setAiState('idle');setMatches([]);setMatchState('loading');
  async function load(){
   try{
    const r=await fetch('/api/db/leads/'+encodeURIComponent(selectedId)+'/workspace?source_number='+encodeURIComponent(sourceFilter),{cache:'no-store',credentials:'include'});
    if(!r.ok)throw Error('Lead workspace unavailable');
    const data=await r.json();
    if(!active)return;
    setWorkspace(data);setLeadStatus(data.lead?.lead_type||'New');setWorkspaceState('ready');
    const req=normalizeRequirements(data.lead?.requirements);
    const bhkMatch=String(req.bhk||'').match(/\d+/);
    const bhk=bhkMatch?bhkMatch[0]:'';
    const budgetMatch=String(req.budget??'').replace(/,/g,'').match(/\d+(?:\.\d+)?/);
    const budget=budgetMatch?budgetMatch[0]:null;
    const locality=String(req.locality||'').trim();
    if(!(bhk||budget||locality)){setMatchState('insufficient');return}
    const qs=new URLSearchParams({limit:'50'});
    if(bhk)qs.set('bhk',bhk+' BHK');
    if(budget)qs.set('budget',budget);
    if(locality)qs.set('locality',locality);
    if(req.furnishing)qs.set('furnishing',String(req.furnishing));
    if(req.pet_friendly)qs.set('pet_friendly',String(req.pet_friendly));
    const mr=await fetch('/api/inventory/matches?'+qs.toString(),{cache:'no-store',credentials:'include'});
    if(!mr.ok)throw Error('Inventory match lookup unavailable');
    const md=await mr.json();
    if(active){setMatches(Array.isArray(md.rows)?md.rows:[]);setMatchState('ready')}
   }catch(e){if(active){setWorkspaceState('unavailable');setMatchState('unavailable')}}
  }
  load();
  return()=>{active=false};
 },[selectedId,sourceFilter,refreshToken]);

 useEffect(()=>{
  if(!supabase){setRealtimeState('unconfigured');return()=>{}}
  let active=true;
  const channel=supabase.channel('crm:live')
   .on('broadcast',{event:'message_inserted'},()=>{if(active)setRefreshToken(v=>v+1)})
   .subscribe((status,err)=>{if(!active)return;setRealtimeState(status==='SUBSCRIBED'?'live':status==='CHANNEL_ERROR'?'error':'connecting');setRealtimeError(status==='SUBSCRIBED'?'':(err?.message||String(err||status)))})
  return()=>{active=false;supabase.removeChannel(channel)};
 },[]);

 const visibleLeads=useMemo(()=>{
  const q=query.trim().toLowerCase();
  return leads.filter(l=>!q||[l.display_name,l.normalized_phone,l.status,l.priority,l.classification].some(v=>String(v||'').toLowerCase().includes(q)));
 },[leads,query]);

 function openLead(id){setSelectedId(id);setTab('Overview');setPage('Leads Inbox')}
 function backToInbox(){setSelectedId(null);setWorkspace(null);setTab('Overview');setPage('Leads Inbox')}
 function refresh(){setRefreshToken(v=>v+1)}
 function classifyContact(id,classification){setClassificationDrafts(prev=>({...prev,[id]:classification}));setClassificationErrors(prev=>{const next={...prev};delete next[id];return next})}
 async function saveClassification(row){const classification=classificationDrafts[row.id];if(!classification||classification==='pending'||classification===row.classification_code)return;setClassificationSaving(prev=>({...prev,[row.id]:true}));setClassificationErrors(prev=>{const next={...prev};delete next[row.id];return next});try{const r=await fetch('/api/db/classifications/'+row.id,{method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify({classification,source:'operator'})});const d=await r.json().catch(()=>({}));if(!r.ok)throw Error(d.error||('Classification update failed (HTTP '+r.status+')'));refresh()}catch(e){setClassificationErrors(prev=>({...prev,[row.id]:e.message||'Classification update failed'}))}finally{setClassificationSaving(prev=>{const next={...prev};delete next[row.id];return next})}}
 function updateLead(id,patch){return fetch('/api/db/leads/'+encodeURIComponent(id),{method:'PATCH',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify(patch)}).then(async r=>{const d=await r.json().catch(()=>({}));if(!r.ok)throw Error(d.error||'Lead update failed');return d}).then(()=>refresh())}
 function runAi(){
  if(!workspace?.lead?.id)return;
  setAiState('running');setAi(null);
  fetch('/api/ai/analyze-real',{method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify({leadId:workspace.lead.id})})
   .then(async r=>{const d=await r.json().catch(()=>({}));if(!r.ok)throw Error(d.error||'Real AI unavailable');setAi(d);setAiState('ready')})
   .catch(()=>setAiState('unavailable'));
 }

 const filteredMatches=matches;
 return <div className="app">
  <aside className="sidebar">
   <div className="brand"><span className="brandmark">EF</span><span>EasyFind<small>LEADS WORKSPACE</small></span></div>
   <nav>{MENU.map(([name,Icon])=><button className={page===name?'nav active':'nav'} key={name} onClick={()=>{setPage(name);if(name!=='Leads Inbox')setSelectedId(null)}}><Icon size={19}/>{name}</button>)}</nav>
   <div className="sidebottom"><CheckCircle2 size={16}/> Production CRM<br/><small>Live source: {SOURCE_NUMBER}</small></div>
  </aside>
  <main className="main">
   <header className="top">
    <div className="top-title">{selectedId&&<button className="header-back" onClick={backToInbox} type="button"><ChevronLeft size={17}/> Leads Inbox</button>}<div><strong>{selectedId?'Lead Workspace':page}</strong><small>EasyFind Property Solutions / CRM</small></div></div>
    <div className="topright"><span className="chip green">● Production data</span><span className={"chip "+(realtimeState==='live'?'green':'')}>Realtime: {realtimeState}</span><span className="chip source">{SOURCE_NUMBER}</span><span className="avatar">ZH</span></div>
   </header>
   <div className="content">

    {page==='Contact Classification'&&<section><div className="heading"><div><h1>Contact Classification</h1><p>Classify new WhatsApp contacts once. Qualified contacts move to CRM; other classifications stay outside CRM.</p></div><button className="primary" onClick={refresh}><RefreshCw size={14}/> Refresh</button></div><div className="panel standalone"><div className="classification-header"><div><h3>Simple qualification queue</h3><p>Use the two tabs below. No separate classification filter is needed.</p></div><label>Lead source <select value={sourceFilter} onChange={e=>setSourceFilter(e.target.value)}>{SOURCE_NUMBERS.map(n=><option key={n} value={n}>{n}</option>)}</select></label></div><div className="classification-tabs"><button className={classificationFilter==='not_pushed'?'selected':''} type="button" onClick={()=>setClassificationFilter('not_pushed')}>Not pushed to CRM <b>{dashboardStats?.notPushedClassificationCount??(classificationFilter==='not_pushed'?classificationTotal:0)}</b></button><button className={classificationFilter==='promoted'?'selected':''} type="button" onClick={()=>setClassificationFilter('promoted')}>Qualified lead pushed to CRM <b>{dashboardStats?.qualifiedClassificationCount??0}</b></button><button className={classificationFilter==='unqualified'?'selected':''} type="button" onClick={()=>setClassificationFilter('unqualified')}>Unqualified leads <b>{dashboardStats?.unqualifiedClassificationCount??0}</b></button></div>{classificationFilter==='not_pushed'&&<div className="notice">This tab contains every contact not pushed into CRM: pending contacts plus contacts already classified as non-qualified. A non-qualified Update stays here and also appears in <b>Unqualified leads</b>. A <b>Qualified Lead</b> Update moves the contact to the CRM tab after the database confirms the write.</div>}{classificationFilter==='promoted'&&<div className="notice">These contacts have already been promoted to CRM. Their preserved WhatsApp messages are linked to the CRM lead.</div>}{classificationFilter==='unqualified'&&<div className="notice">These contacts were explicitly classified as something other than <b>Qualified Lead</b>. They remain outside CRM.</div>}{classificationState==='loading'&&<div className="empty">Loading classifications...</div>}{classificationState==='unavailable'&&<div className="notice">Classification records are unavailable. {classificationError||'No fallback data is shown.'}</div>}{classificationState==='ready'&&(classifications.length?classifications.map(c=>{const draft=classificationDrafts[c.id]??c.classification_code;const saving=Boolean(classificationSaving[c.id]);const changed=draft&&draft!=='pending'&&draft!==c.classification_code;const promoted=c.status==='promoted';return <article className="event classification-row" key={c.id}><div className="classification-contact"><b>{c.phone}</b><small>{promoted?'Qualified Lead · CRM lead':'Pending / '+(c.classification_label||'classification')} · {c.source_number}</small><a className="whatsapp-link" href={'https://wa.me/'+String(c.phone||'').replace(/\D/g,'')} target="_blank" rel="noreferrer">Open WhatsApp</a>{classificationErrors[c.id]&&<small className="error">Update failed: {classificationErrors[c.id]}</small>}</div>{!promoted?<div className="classification-actions"><select value={draft==='pending'?'pending':draft} disabled={saving} onChange={e=>classifyContact(c.id,e.target.value)}><option value="pending" disabled>Choose classification</option><option value="qualified_lead">Qualified Lead</option><option value="promotion">Promotion / Marketing</option><option value="cold_inquiry">Cold Inquiry</option><option value="property_listing_sent">Property Listing Sent</option><option value="vendor_supplier">Vendor / Supplier</option><option value="agent_partner">Agent / Partner</option><option value="personal_family">Family / personal</option><option value="internal">Internal</option><option value="business">Business</option><option value="unknown">Unknown</option></select><button className="primary" type="button" disabled={!changed||saving} onClick={()=>saveClassification(c)}>{saving?'Saving...':'Update'}</button></div>:<span className="chip green">In Leads Inbox</span>}</article>}):<div className="empty">No contacts in this queue.</div>)}</div></section>}
    {page==='Inventory'&&<InventoryPanel data={inventoryData} state={inventoryState} refresh={refresh} query={inventoryQuery} setQuery={setInventoryQuery}/>}
    {page==='Settings'&&<><div className="heading"><div><h1>Settings</h1><p>Production CRM configuration</p></div></div><div className="panel standalone"><h3>WhatsApp sources</h3><p>Verified EFPS source numbers:</p><div className="source-list">{SOURCE_NUMBERS.map(n=><span className="chip source" key={n}>{n}</span>)}</div><p>New WhatsApp activity is held in Contact Classification until an operator promotes it. The browser does not send WhatsApp messages automatically.</p></div></>}
    {(page==='Dashboard'||page==='Leads Inbox')&&selectedId&&workspaceState==='ready'&&<section className="panel live-detail">
      <div className="detailhead">
       <button className="back" onClick={backToInbox}><ChevronLeft size={18}/> Leads Inbox</button>
       <div className="identity"><span className="initial">{leadTitle(workspace.lead).split(/\s+/).map(x=>x[0]).join('').slice(0,3)}</span><div><h2>{leadTitle(workspace.lead)}</h2><span>{workspace.lead.normalized_phone||'No phone stored'} · {SOURCE_NUMBER}</span></div></div>
       <div className="headcontrols"><label className="inline-field">Lead Status <select value={leadStatus||workspace.lead.lead_type||'New'} onChange={e=>{setLeadStatus(e.target.value);updateLead(workspace.lead.id,{leadType:e.target.value}).catch(()=>{})}}>{LEAD_STATUSES.map(s=><option key={s} value={s}>{s}</option>)}</select></label><span className="chip">{workspace.lead.priority}</span><span className="chip classification">{classificationLabel(workspace.lead.classification||workspace.lead.requirements?.fields?.classification||workspace.lead.requirements?.classification)}</span></div>
      </div>
      <div className="tabs">{TABS.map(t=><button className={tab===t?'active':''} key={t} onClick={()=>setTab(t)}>{t}</button>)}</div>
      <div className="tabbody">
       {tab==='Overview'&&<><div className="two"><div className="inner"><h3>Lead classification</h3><div className="classification-large">{classificationLabel(workspace.lead.classification||workspace.lead.requirements?.fields?.classification||workspace.lead.requirements?.classification)}</div><p className="muted">Historical classification is retained. New live leads may remain unclassified until an operator classifies them.</p></div><div className="inner"><h3>Stored requirements</h3><div className="requirements-grid">{requirementEntries(workspace.lead.requirements).length?requirementEntries(workspace.lead.requirements).map(([k,v])=><div className="requirement-item" key={k}><small>{k.replaceAll('_',' ')}</small><b>{String(v)}</b></div>):<div className="empty">No structured requirements recorded.</div>}</div><details className="raw-details"><summary>Source record</summary><pre className="jsonview">{JSON.stringify(workspace.lead.requirements||{},null,2)}</pre></details></div><div className="inner"><h3>Operator action</h3><p>{workspace.lead.operator_notes||'No operator note stored.'}</p><a className="primary inlinebutton" href={'https://wa.me/'+String(workspace.lead.normalized_phone||'').replace(/\D/g,'')} target="_blank" rel="noopener noreferrer">Open WhatsApp</a></div></div><div className="inner"><h3>Imported data</h3><p>Messages: <b>{workspace.messages.length}</b> · Activity: <b>{workspace.activity.length}</b> · Follow-ups: <b>{workspace.followups.length}</b></p><div className="notice">{workspace.messages.length?'Historical messages are available.':'No historical messages are imported yet. The production UI does not fabricate conversation history.'}</div></div></>}
       {tab==='Conversation'&&(workspace.messages.length?<div className="conversation">{workspace.messages.map(m=><div className={'bubble '+(m.direction==='Outgoing'?'out':'')} key={m.id}><small>{m.direction} · {new Date(m.message_at).toLocaleString()} · {m.sender_name||m.source_number}</small><p>{m.body||'['+m.message_type+']'}</p>{(m.media_urls||m.media_filenames)?.length>0&&<small>Media attached</small>}</div>)}</div>:<div className="empty">No imported conversation for this lead. Historical message import is separate from the 228-lead import.</div>)}
       {tab==='Requirements'&&<><div className="notice">Read-only production view. Values below are mapped from the source-backed lead record; no requirement is inferred by the browser.</div><div className="requirements-grid full">{requirementEntries(workspace.lead.requirements).length?requirementEntries(workspace.lead.requirements).map(([k,v])=><div className="requirement-item" key={k}><small>{k.replaceAll('_',' ')}</small><b>{String(v)}</b></div>):<div className="empty">No structured requirements recorded for this lead.</div>}</div><details className="raw-details"><summary>Raw source-backed JSON</summary><pre className="jsonview">{JSON.stringify(workspace.lead.requirements||{},null,2)}</pre></details></>}
       {tab==='Property Matches'&&<>{matchState==='loading'&&<div className="empty">Matching against current Supabase inventory…</div>}{matchState==='insufficient'&&<div className="empty">No structured BHK, budget or locality is stored for this lead, so no inventory match is inferred.</div>}{matchState==='unavailable'&&<div className="empty">Live inventory matching is unavailable.</div>}{matchState==='ready'&&(filteredMatches.length?<div className="properties">{filteredMatches.map(p=><article className="property" key={p.listing_id}><div className="photo-fallback">{(p.cloudinary_image_urls||[]).length?<img src={p.cloudinary_image_urls[0]} alt={'Property '+p.listing_id}/>:<span>No property images available</span>}</div><div className="rowtop"><b>{p.bhk} · {p.locality}</b><span className="chip green">{p.listing_state}</span></div><p className="price">{money(p.monthly_rent)} <small>/ month</small></p><p>{p.furnishing||'Furnishing not recorded'} · Pets: {p.pet_friendly||'Not recorded'}</p><small>{p.listing_id} · {p.society_name||'Society not recorded'}</small></article>)}</div>:<div className="empty">No live inventory matches were returned.</div>)}</>}
       {tab==='AI & Drafts'&&<><div className="notice">Real AI is on-demand and grounded only in this stored lead record. It does not send WhatsApp messages.</div><div className="inner"><h3><BrainCircuit size={18}/> AI review</h3><p>Run a server-side review using the configured production Ollama provider.</p><button className="primary" disabled={aiState==='running'} onClick={runAi}>{aiState==='running'?'Running…':'Run AI review'}</button>{aiState==='unavailable'&&<p className="error">Real AI is unavailable or disabled. No generated result is shown.</p>}{ai&&<pre className="jsonview">{JSON.stringify(ai.proposal,null,2)}</pre>}</div></>}
       {tab==='Activity & History'&&<>{workspace.followups?.length?<div className="inner"><h3>Follow-ups</h3>{workspace.followups.map(f=><div className="event" key={f.id}><CheckCircle2 size={17}/><div><b>{f.completed_at?'Completed':'Scheduled'}</b><small>{f.due_at?new Date(f.due_at).toLocaleString():''} · {f.note||'No note recorded'}</small></div></div>)}</div>:<div className="notice">No follow-up records are stored for this lead.</div>}{workspace.activity.length?workspace.activity.map(a=><div className="event" key={a.id}><CheckCircle2 size={17}/><div><b>{a.action}</b><small>{a.occurred_at?new Date(a.occurred_at).toLocaleString():''} · {a.actor}</small></div></div>):<div className="empty">No activity recorded for this lead.</div>}</>}
      </div>
     </section>}
    {(page==='Dashboard'||page==='Leads Inbox')&&!selectedId&&<section>
      <div className="heading"><div><h1>{page==='Dashboard'?'CRM Dashboard':'Leads Inbox'}</h1><p>Live production records across the verified WhatsApp source numbers.</p></div><div className="headcontrols"><label className="inline-field">Lead source <select value={sourceFilter} onChange={e=>{setSourceFilter(e.target.value);setOffset(0)}}>{SOURCE_NUMBERS.map(n=><option key={n} value={n}>{n}</option>)}</select></label><button className="primary" onClick={refresh}><RefreshCw size={14}/> Refresh</button></div></div>
      {error&&<div className="notice">Live CRM unavailable. {error}</div>}
      {page==='Dashboard'&&realtimeState==='error'&&<div className="notice">Realtime connection error: {realtimeError||'channel subscription failed'}. Live webhook ingestion is independent and continues server-side.</div>}
      {page==='Dashboard'&&<><div className="stats"><button className="stat stat-link" onClick={()=>{setPage('Leads Inbox');setOffset(0)}}><small>CRM leads</small><b>{dashboardStats?.leadCount??total}</b><span>Qualified leads · Open Leads Inbox</span></button><button className="stat stat-link" onClick={()=>{setPage('Contact Classification');setClassificationFilter('not_pushed')}}><small>Not pushed to CRM</small><b>{dashboardStats?.notPushedClassificationCount??dashboardStats?.pendingClassificationCount??0}</b><span>Contacts needing classification</span></button><button className="stat stat-link" onClick={()=>setPage('Contact Classification')}><small>Qualified leads pushed</small><b>{dashboardStats?.qualifiedClassificationCount??0}</b><span>Classification audit queue</span></button><button className="stat stat-link" onClick={()=>{setPage('Leads Inbox');setOffset(0)}}><small>Follow-ups today</small><b>{dashboardStats?.followupTodayCount??0}</b><span>{dashboardStats?.overdueFollowupCount??0} overdue · Open Leads Inbox</span></button></div><div className="panel daily-actions"><div className="daily-actions-head"><div><h3>Today's follow-ups</h3><p>Only the next actions that need your attention.</p></div>{dashboardStats?.webhookErrorCount>0&&<span className="chip red">{dashboardStats.webhookErrorCount} webhook errors</span>}</div>{(dashboardStats?.nextFollowups||[]).length?dashboardStats.nextFollowups.map(f=><button type="button" className="followup-row" key={f.id} onClick={()=>openLead(f.lead_id)}><span className="followup-time">{new Date(f.due_at).toLocaleString([], {day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit'})}</span><span><b>{f.display_name||f.normalized_phone||'Lead'}</b><small>{f.note||'Follow-up due'}</small></span><span className="chip">Open</span></button>):<div className="empty">No open follow-ups are scheduled. New activity will appear here when a follow-up is created.</div>}</div></>}
      <div className="panel leadlist-production">
       <div className="production-toolbar"><label className="search"><Search size={16}/><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search name or phone" aria-label="Search live leads"/></label><label>Lead status <select value={leadStatusFilter} onChange={e=>{setLeadStatusFilter(e.target.value);setOffset(0)}}><option value="">All statuses</option>{LEAD_STATUSES.map(s=><option key={s} value={s}>{s}</option>)}</select></label><label>Lead source <select value={sourceFilter} onChange={e=>{setSourceFilter(e.target.value);setOffset(0)}}>{SOURCE_NUMBERS.map(n=><option key={n} value={n}>{n}</option>)}</select></label><span>{total} leads</span></div>
       {loading?<div className="empty">Loading live leads…</div>:visibleLeads.length?visibleLeads.map(l=><LeadCard key={l.id} lead={l} onClick={()=>openLead(l.id)}/>):<div className="empty">No live leads match this search.</div>}
      </div>
      <div className="pagination"><button disabled={offset===0} onClick={()=>setOffset(Math.max(0,offset-100))}>Previous</button><span>{total?offset+1:0}–{Math.min(offset+leads.length,total)} of {total}</span><button disabled={offset+100>=total} onClick={()=>setOffset(offset+100)}>Next</button></div>
    </section>}
    {(page==='Dashboard'||page==='Leads Inbox')&&selectedId&&workspaceState==='loading'&&<div className="panel standalone"><div className="backlink"><button className="back" onClick={backToInbox}><ChevronLeft size={18}/> Leads Inbox</button></div><div className="empty">Loading the live lead workspace…</div></div>}
    {(page==='Dashboard'||page==='Leads Inbox')&&selectedId&&workspaceState==='unavailable'&&<div className="panel standalone"><div className="backlink"><button className="back" onClick={backToInbox}><ChevronLeft size={18}/> Leads Inbox</button></div><div className="notice">The live lead workspace could not be loaded. No fallback data is used.</div><button className="primary" onClick={refresh}>Retry</button></div>}
   </div>
  </main>
 </div>
}

createRoot(document.getElementById('root')).render(<App/>);
