import React,{useEffect,useMemo,useState} from 'react';
import {createRoot} from 'react-dom/client';
import {createClient} from '@supabase/supabase-js';
import {LayoutDashboard,Inbox,Building2,Settings,Search,ChevronLeft,BrainCircuit,CheckCircle2,RefreshCw} from 'lucide-react';
import InventoryPanel from './inventory-panel.jsx';
import './style.css';

const SOURCE_NUMBER='+919148338801';
const TABS=['Overview','Conversation','Requirements','Property Matches','AI & Drafts','Activity & History'];
const MENU=[['Dashboard',LayoutDashboard],['Contact Classification',Inbox],['Leads Inbox',Inbox],['Inventory',Building2],['Settings',Settings]];
const SUPABASE_URL=import.meta.env.VITE_SUPABASE_URL||'';
const SUPABASE_PUBLISHABLE_KEY=import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY||'';
const supabase=SUPABASE_URL&&SUPABASE_PUBLISHABLE_KEY?createClient(SUPABASE_URL,SUPABASE_PUBLISHABLE_KEY):null;
const money=n=>n!==null&&n!==undefined&&n!==''?'₹'+Number(n).toLocaleString('en-IN'):'Not specified';
const leadTitle=lead=>lead?.display_name||lead?.normalized_phone||'Lead';
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
 const[classificationFilter,setClassificationFilter]=useState('');

 useEffect(()=>{try{window.sessionStorage.setItem('efps-crm-active-page',page)}catch{}},[page]);

 useEffect(()=>{
  let active=true;
  async function load(){
   setLoading(true);setError('');
   try{
    const r=await fetch('/api/db/leads?limit=100&offset='+offset,{cache:'no-store'});
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
 },[offset,refreshToken]);

 useEffect(()=>{
  let active=true;
  if(page!=='Contact Classification')return()=>{active=false};
  setClassificationState('loading');
  const qs=new URLSearchParams({limit:'100'});if(classificationFilter)qs.set('classification',classificationFilter);
  fetch('/api/db/classifications?'+qs.toString(),{cache:'no-store'}).then(async r=>{if(!r.ok)throw Error('Classification records unavailable');return r.json()}).then(d=>{if(active){setClassifications(Array.isArray(d.classifications)?d.classifications:[]);setClassificationState('ready')}}).catch(()=>{if(active){setClassifications([]);setClassificationState('unavailable')}});
  return()=>{active=false};
 },[page,classificationFilter,refreshToken]);

 useEffect(()=>{
  let active=true;
  async function load(){
   try{
    const r=await fetch('/api/inventory/overview',{cache:'no-store'});
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
    const r=await fetch('/api/db/leads/'+encodeURIComponent(selectedId)+'/workspace',{cache:'no-store'});
    if(!r.ok)throw Error('Lead workspace unavailable');
    const data=await r.json();
    if(!active)return;
    setWorkspace(data);setWorkspaceState('ready');
    const raw=data.lead?.requirements;
    const req=raw?.fields&&typeof raw.fields==='object'?raw.fields:(raw&&typeof raw==='object'?raw:{});
    const bhkMatch=String(req.bhk||'').match(/\d+/);
    const bhk=bhkMatch?bhkMatch[0]:'';
    const budgetMatch=String(req.budget??req.max_budget??req.budget_max??'').replace(/,/g,'').match(/\d+(?:\.\d+)?/);
    const budget=budgetMatch?budgetMatch[0]:null;
    const locality=String(req.locality||req.location||'').trim();
    if(!(bhk||budget||locality)){setMatchState('insufficient');return}
    const qs=new URLSearchParams({limit:'50'});
    if(bhk)qs.set('bhk',bhk+' BHK');
    if(budget)qs.set('budget',budget);
    if(locality)qs.set('locality',locality);
    const mr=await fetch('/api/inventory/matches?'+qs.toString(),{cache:'no-store'});
    if(!mr.ok)throw Error('Inventory match lookup unavailable');
    const md=await mr.json();
    if(active){setMatches(Array.isArray(md.rows)?md.rows:[]);setMatchState('ready')}
   }catch(e){if(active){setWorkspaceState('unavailable');setMatchState('unavailable')}}
  }
  load();
  return()=>{active=false};
 },[selectedId,refreshToken]);

 useEffect(()=>{
  if(!supabase){setRealtimeState('unconfigured');return()=>{}}
  let active=true;
  const channel=supabase.channel('crm:live')
   .on('broadcast',{event:'message_inserted'},()=>{if(active)setRefreshToken(v=>v+1)})
   .subscribe(status=>{if(!active)return;setRealtimeState(status==='SUBSCRIBED'?'live':status==='CHANNEL_ERROR'?'error':'connecting')});
  return()=>{active=false;supabase.removeChannel(channel)};
 },[]);

 const visibleLeads=useMemo(()=>{
  const q=query.trim().toLowerCase();
  return leads.filter(l=>!q||[l.display_name,l.normalized_phone,l.status,l.priority,l.classification].some(v=>String(v||'').toLowerCase().includes(q)));
 },[leads,query]);

 function openLead(id){setSelectedId(id);setTab('Overview');setPage('Leads Inbox')}
 function backToInbox(){setSelectedId(null);setWorkspace(null);setTab('Overview');setPage('Leads Inbox')}
 function refresh(){setRefreshToken(v=>v+1)}
 function runAi(){
  if(!workspace?.lead?.id)return;
  setAiState('running');setAi(null);
  fetch('/api/ai/analyze-real',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({leadId:workspace.lead.id})})
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

    {page==='Contact Classification'&&<section><div className="heading"><div><h1>Contact Classification</h1><p>Layer 1: classify the WhatsApp contact before it enters the Lead CRM.</p></div><button className="primary" onClick={refresh}><RefreshCw size={14}/> Refresh</button></div><div className="panel standalone"><div className="production-toolbar"><label>Classification <select value={classificationFilter} onChange={e=>setClassificationFilter(e.target.value)}><option value="">All</option><option value="pending">Pending</option><option value="qualified_lead">Qualified Lead</option><option value="personal_family">Personal / Family</option><option value="agent_partner">Agent / Partner</option><option value="business">Business</option><option value="promotion">Promotion / Marketing</option><option value="vendor_supplier">Vendor / Supplier</option><option value="internal">Internal</option><option value="cold_inquiry">Cold Inquiry</option><option value="property_listing_sent">Property Listing Sent</option><option value="unknown">Unknown</option></select></label><span>Every webhook event is retained first. Only Qualified Lead is eligible for CRM promotion.</span></div>{classificationState==='loading'&&<div className="empty">Loading contact classifications…</div>}{classificationState==='unavailable'&&<div className="notice">Classification records are unavailable. No fallback data is shown.</div>}{classificationState==='ready'&&(classifications.length?classifications.map(c=><article className="event" key={c.id}><div><b>{c.phone}</b><small>{c.classification_label} · {c.status} · {c.classification_source}</small></div></article>):<div className="empty">No contact classifications recorded.</div>)}</div><div className="notice">Layer 2 is the operational Lead Type inside the CRM and is separate from contact classification.</div></section>}
    {page==='Inventory'&&<InventoryPanel data={inventoryData} state={inventoryState} refresh={refresh} query={inventoryQuery} setQuery={setInventoryQuery}/>}
    {page==='Settings'&&<><div className="heading"><div><h1>Settings</h1><p>Production CRM configuration</p></div></div><div className="panel standalone"><h3>Live data scope</h3><p>This dashboard is connected only to the lead source <b>{SOURCE_NUMBER}</b>. Production data modes are enforced.</p><p>New WhatsApp activity creates or updates a lead directly. The browser does not send WhatsApp messages automatically.</p></div></>}
    {(page==='Dashboard'||page==='Leads Inbox')&&selectedId&&workspaceState==='ready'&&<section className="panel live-detail">
      <div className="detailhead">
       <button className="back" onClick={backToInbox}><ChevronLeft size={18}/> Leads Inbox</button>
       <div className="identity"><span className="initial">{leadTitle(workspace.lead).split(/\s+/).map(x=>x[0]).join('').slice(0,3)}</span><div><h2>{leadTitle(workspace.lead)}</h2><span>{workspace.lead.normalized_phone||'No phone stored'} · {SOURCE_NUMBER}</span></div></div>
       <div className="headcontrols"><span className="chip blue">{workspace.lead.status}</span><span className="chip">{workspace.lead.priority}</span><span className="chip classification">{classificationLabel(workspace.lead.classification||workspace.lead.requirements?.fields?.classification||workspace.lead.requirements?.classification)}</span></div>
      </div>
      <div className="tabs">{TABS.map(t=><button className={tab===t?'active':''} key={t} onClick={()=>setTab(t)}>{t}</button>)}</div>
      <div className="tabbody">
       {tab==='Overview'&&<><div className="two"><div className="inner"><h3>Lead classification</h3><div className="classification-large">{classificationLabel(workspace.lead.classification||workspace.lead.requirements?.fields?.classification||workspace.lead.requirements?.classification)}</div><p className="muted">Historical classification is retained. New live leads may remain unclassified until an operator classifies them.</p></div><div className="inner"><h3>Stored requirements</h3><pre className="jsonview">{JSON.stringify(workspace.lead.requirements||{},null,2)}</pre></div><div className="inner"><h3>Operator action</h3><p>{workspace.lead.operator_notes||'No operator note stored.'}</p><a className="primary inlinebutton" href={'https://wa.me/'+String(workspace.lead.normalized_phone||'').replace(/\D/g,'')} target="_blank" rel="noopener noreferrer">Open WhatsApp</a></div></div><div className="inner"><h3>Imported data</h3><p>Messages: <b>{workspace.messages.length}</b> · Activity: <b>{workspace.activity.length}</b> · Follow-ups: <b>{workspace.followups.length}</b></p><div className="notice">{workspace.messages.length?'Historical messages are available.':'No historical messages are imported yet. The production UI does not fabricate conversation history.'}</div></div></>}
       {tab==='Conversation'&&(workspace.messages.length?<div className="conversation">{workspace.messages.map(m=><div className={'bubble '+(m.direction==='Outgoing'?'out':'')} key={m.id}><small>{m.direction} · {new Date(m.message_at).toLocaleString()} · {m.sender_name||m.source_number}</small><p>{m.body||'['+m.message_type+']'}</p>{(m.media_urls||m.media_filenames)?.length>0&&<small>Media attached</small>}</div>)}</div>:<div className="empty">No imported conversation for this lead. Historical message import is separate from the 228-lead import.</div>)}
       {tab==='Requirements'&&<><div className="notice">Read-only production view. Browser writes are disabled.</div><pre className="jsonview">{JSON.stringify(workspace.lead.requirements||{},null,2)}</pre></>}
       {tab==='Property Matches'&&<>{matchState==='loading'&&<div className="empty">Matching against current Supabase inventory…</div>}{matchState==='insufficient'&&<div className="empty">No structured BHK, budget or locality is stored for this lead, so no inventory match is inferred.</div>}{matchState==='unavailable'&&<div className="empty">Live inventory matching is unavailable.</div>}{matchState==='ready'&&(filteredMatches.length?<div className="properties">{filteredMatches.map(p=><article className="property" key={p.listing_id}><div className="photo-fallback">{(p.cloudinary_image_urls||[]).length?<img src={p.cloudinary_image_urls[0]} alt={'Property '+p.listing_id}/>:<span>No property images available</span>}</div><div className="rowtop"><b>{p.bhk} · {p.locality}</b><span className="chip green">{p.listing_state}</span></div><p className="price">{money(p.monthly_rent)} <small>/ month</small></p><p>{p.furnishing||'Furnishing not recorded'} · Pets: {p.pet_friendly||'Not recorded'}</p><small>{p.listing_id} · {p.society_name||'Society not recorded'}</small></article>)}</div>:<div className="empty">No live inventory matches were returned.</div>)}</>}
       {tab==='AI & Drafts'&&<><div className="notice">Real AI is on-demand and grounded only in this stored lead record. It does not send WhatsApp messages.</div><div className="inner"><h3><BrainCircuit size={18}/> AI review</h3><p>Run a server-side review using the configured production Ollama provider.</p><button className="primary" disabled={aiState==='running'} onClick={runAi}>{aiState==='running'?'Running…':'Run AI review'}</button>{aiState==='unavailable'&&<p className="error">Real AI is unavailable or disabled. No generated result is shown.</p>}{ai&&<pre className="jsonview">{JSON.stringify(ai.proposal,null,2)}</pre>}</div></>}
       {tab==='Activity & History'&&(workspace.activity.length?workspace.activity.map(a=><div className="event" key={a.id}><CheckCircle2 size={17}/><div><b>{a.action}</b><small>{a.occurred_at?new Date(a.occurred_at).toLocaleString():''} · {a.actor}</small></div></div>):<div className="empty">No activity recorded for this lead.</div>)}
      </div>
     </section>}
    {(page==='Dashboard'||page==='Leads Inbox')&&!selectedId&&<section>
      <div className="heading"><div><h1>{page==='Dashboard'?'CRM Dashboard':'Leads Inbox'}</h1><p>Live production records from {SOURCE_NUMBER}</p></div><div className="headcontrols"><span className="chip green">228-source scope</span><button className="primary" onClick={refresh}><RefreshCw size={14}/> Refresh</button></div></div>
      {error&&<div className="notice">Live CRM unavailable. {error}</div>}
      {page==='Dashboard'&&<div className="stats"><div className="stat"><small>Real leads</small><b>{total}</b><span>Imported from {SOURCE_NUMBER}</span></div><div className="stat"><small>Lead records on page</small><b>{leads.length}</b><span>Current live page</span></div><div className="stat"><small>Historical messages</small><b>5,286</b><span>Source-backed conversation records</span></div><div className="stat"><small>Inventory records</small><b>{inventoryData?.rows?.length??'—'}</b><span>Supabase inventory mirror</span></div></div>}
      <div className="panel leadlist-production">
       <div className="production-toolbar"><label className="search"><Search size={16}/><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search name or phone" aria-label="Search live leads"/></label><span>{total} real leads</span></div>
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
