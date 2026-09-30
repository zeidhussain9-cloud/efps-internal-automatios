import React,{useEffect,useMemo,useState} from 'react';
import {createRoot} from 'react-dom/client';
import {LayoutDashboard,Inbox,Building2,Settings,Search,ChevronLeft,BrainCircuit,CheckCircle2,RefreshCw} from 'lucide-react';
import InventoryPanel from './inventory-panel.jsx';
import './style.css';

const SOURCE_NUMBER='+919148338801';
const TABS=['Overview','Conversation','Requirements','Property Matches','AI & Drafts','Activity & History'];
const MENU=[['Dashboard',LayoutDashboard],['Leads Inbox',Inbox],['Inventory',Building2],['Settings',Settings]];
const money=n=>n!==null&&n!==undefined&&n!==''?'₹'+Number(n).toLocaleString('en-IN'):'Not specified';

function LeadCard({lead,onClick}){
 return <button className="lead-card" onClick={onClick} type="button">
  <div className="lead-card-main"><b>{lead.display_name||'Unnamed lead'}</b><span>{lead.normalized_phone||'No phone stored'}</span></div>
  <div className="lead-card-meta"><span>{lead.status}</span><span>{lead.priority}</span><span>{lead.source_number||SOURCE_NUMBER}</span></div>
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

 const visibleLeads=useMemo(()=>{
  const q=query.trim().toLowerCase();
  return leads.filter(l=>!q||[l.display_name,l.normalized_phone,l.status,l.priority].some(v=>String(v||'').toLowerCase().includes(q)));
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
    <div><strong>{selectedId?'Lead Workspace':page}</strong><small>EasyFind Property Solutions / CRM</small></div>
    <div className="topright"><span className="chip green">● Production data</span><span className="chip source">{SOURCE_NUMBER}</span><span className="avatar">ZH</span></div>
   </header>
   <div className="content">
    {page==='Inventory'&&<InventoryPanel data={inventoryData} state={inventoryState} refresh={refresh} query={inventoryQuery} setQuery={setInventoryQuery}/>}
    {page==='Settings'&&<><div className="heading"><div><h1>Settings</h1><p>Production CRM configuration</p></div></div><div className="panel standalone"><h3>Live data scope</h3><p>This dashboard is connected only to the imported lead source <b>{SOURCE_NUMBER}</b>. Synthetic lead fixtures and synthetic AI previews are disabled.</p><p>Customer writes remain disabled from the browser. WhatsApp opens the operator's composer; the CRM does not send messages automatically.</p></div></>}
    {(page==='Dashboard'||page==='Leads Inbox')&&selectedId&&workspaceState==='ready'&&<section className="panel live-detail">
      <div className="detailhead">
       <button className="back" onClick={backToInbox}><ChevronLeft size={18}/> Leads Inbox</button>
       <div className="identity"><span className="initial">{(workspace.lead.display_name||'Lead').split(' ').map(x=>x[0]).join('').slice(0,3)}</span><div><h2>{workspace.lead.display_name||'Unnamed lead'}</h2><span>{workspace.lead.normalized_phone||'No phone stored'} · {SOURCE_NUMBER}</span></div></div>
       <div className="headcontrols"><span className="chip blue">{workspace.lead.status}</span><span className="chip">{workspace.lead.priority}</span></div>
      </div>
      <div className="tabs">{TABS.map(t=><button className={tab===t?'active':''} key={t} onClick={()=>setTab(t)}>{t}</button>)}</div>
      <div className="tabbody">
       {tab==='Overview'&&<><div className="two"><div className="inner"><h3>Stored requirements</h3><pre className="jsonview">{JSON.stringify(workspace.lead.requirements||{},null,2)}</pre></div><div className="inner"><h3>Operator action</h3><p>{workspace.lead.operator_notes||'No operator note stored.'}</p><a className="primary inlinebutton" href={'https://wa.me/'+String(workspace.lead.normalized_phone||'').replace(/\D/g,'')} target="_blank" rel="noopener noreferrer">Open WhatsApp</a></div></div><div className="inner"><h3>Imported data</h3><p>Messages: <b>{workspace.messages.length}</b> · Activity: <b>{workspace.activity.length}</b> · Follow-ups: <b>{workspace.followups.length}</b></p><div className="notice">{workspace.messages.length?'Historical messages are available.':'No historical messages are imported yet. The production UI does not fabricate conversation history.'}</div></div></>}
       {tab==='Conversation'&&(workspace.messages.length?<div className="conversation">{workspace.messages.map(m=><div className={'bubble '+(m.direction==='Outgoing'?'out':'')} key={m.id}><small>{m.direction} · {new Date(m.message_at).toLocaleString()} · {m.source_number}</small><p>{m.body||'['+m.message_type+']'}</p></div>)}</div>:<div className="empty">No imported conversation for this lead. Historical message import is separate from the 228-lead import.</div>)}
       {tab==='Requirements'&&<><div className="notice">Read-only production view. Browser writes are disabled.</div><pre className="jsonview">{JSON.stringify(workspace.lead.requirements||{},null,2)}</pre></>}
       {tab==='Property Matches'&&<>{matchState==='loading'&&<div className="empty">Matching against current Supabase inventory…</div>}{matchState==='insufficient'&&<div className="empty">No structured BHK, budget or locality is stored for this lead, so no inventory match is inferred.</div>}{matchState==='unavailable'&&<div className="empty">Live inventory matching is unavailable.</div>}{matchState==='ready'&&(filteredMatches.length?<div className="properties">{filteredMatches.map(p=><article className="property" key={p.listing_id}><div className="photo-fallback">{(p.cloudinary_image_urls||[]).length?<img src={p.cloudinary_image_urls[0]} alt={'Property '+p.listing_id}/>:<span>No property images available</span>}</div><div className="rowtop"><b>{p.bhk} · {p.locality}</b><span className="chip green">{p.listing_state}</span></div><p className="price">{money(p.monthly_rent)} <small>/ month</small></p><p>{p.furnishing||'Furnishing not recorded'} · Pets: {p.pet_friendly||'Not recorded'}</p><small>{p.listing_id} · {p.society_name||'Society not recorded'}</small></article>)}</div>:<div className="empty">No live inventory matches were returned.</div>)}</>}
       {tab==='AI & Drafts'&&<><div className="notice">Real AI is on-demand and grounded only in this stored lead record. It does not send WhatsApp messages.</div><div className="inner"><h3><BrainCircuit size={18}/> AI review</h3><p>Run a server-side review using the configured production Ollama provider.</p><button className="primary" disabled={aiState==='running'} onClick={runAi}>{aiState==='running'?'Running…':'Run AI review'}</button>{aiState==='unavailable'&&<p className="error">Real AI is unavailable or disabled. No synthetic result is shown.</p>}{ai&&<pre className="jsonview">{JSON.stringify(ai.proposal,null,2)}</pre>}</div></>}
       {tab==='Activity & History'&&(workspace.activity.length?workspace.activity.map(a=><div className="event" key={a.id}><CheckCircle2 size={17}/><div><b>{a.action}</b><small>{a.occurred_at?new Date(a.occurred_at).toLocaleString():''} · {a.actor}</small></div></div>):<div className="empty">No activity recorded for this lead.</div>)}
      </div>
     </section>}
    {(page==='Dashboard'||page==='Leads Inbox')&&!selectedId&&<section>
      <div className="heading"><div><h1>{page==='Dashboard'?'CRM Dashboard':'Leads Inbox'}</h1><p>Live production records from {SOURCE_NUMBER}</p></div><div className="headcontrols"><span className="chip green">228-source scope</span><button className="primary" onClick={refresh}><RefreshCw size={14}/> Refresh</button></div></div>
      {error&&<div className="notice">Live CRM unavailable. {error}</div>}
      {page==='Dashboard'&&<div className="stats"><div className="stat"><small>Real leads</small><b>{total}</b><span>Imported from {SOURCE_NUMBER}</span></div><div className="stat"><small>Lead records on page</small><b>{leads.length}</b><span>Current live page</span></div><div className="stat"><small>Messages imported</small><b>0</b><span>No synthetic conversations</span></div><div className="stat"><small>Inventory records</small><b>{inventoryData?.rows?.length??'—'}</b><span>Supabase inventory mirror</span></div></div>}
      <div className="panel leadlist-production">
       <div className="production-toolbar"><label className="search"><Search size={16}/><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search name or phone" aria-label="Search live leads"/></label><span>{total} real leads</span></div>
       {loading?<div className="empty">Loading live leads…</div>:visibleLeads.length?visibleLeads.map(l=><LeadCard key={l.id} lead={l} onClick={()=>openLead(l.id)}/>):<div className="empty">No live leads match this search.</div>}
      </div>
      <div className="pagination"><button disabled={offset===0} onClick={()=>setOffset(Math.max(0,offset-100))}>Previous</button><span>{total?offset+1:0}–{Math.min(offset+leads.length,total)} of {total}</span><button disabled={offset+100>=total} onClick={()=>setOffset(offset+100)}>Next</button></div>
    </section>}
    {(page==='Dashboard'||page==='Leads Inbox')&&selectedId&&workspaceState==='loading'&&<div className="panel standalone"><div className="backlink"><button className="back" onClick={backToInbox}><ChevronLeft size={18}/> Leads Inbox</button></div><div className="empty">Loading the live lead workspace…</div></div>}
    {(page==='Dashboard'||page==='Leads Inbox')&&selectedId&&workspaceState==='unavailable'&&<div className="panel standalone"><div className="backlink"><button className="back" onClick={backToInbox}><ChevronLeft size={18}/> Leads Inbox</button></div><div className="notice">The live lead workspace could not be loaded. No synthetic fallback is used.</div><button className="primary" onClick={refresh}>Retry</button></div>}
   </div>
  </main>
 </div>
}

createRoot(document.getElementById('root')).render(<App/>);
