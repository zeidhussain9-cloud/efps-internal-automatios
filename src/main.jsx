import React,{useEffect,useMemo,useRef,useState} from 'react';
import {Component} from 'react';
import {createRoot} from 'react-dom/client';
import {createClient} from '@supabase/supabase-js';
import {LayoutDashboard,Inbox,Building2,Settings,Search,ChevronLeft,BrainCircuit,CheckCircle2,RefreshCw,ShieldCheck,LogOut,Download,Archive,RotateCcw,Activity as ActivityIcon,WifiOff,Clock3} from 'lucide-react';
import {maskPhone,maskMessage} from './privacy.mjs';
import InventoryPanel from './inventory-panel.jsx';
import {INVENTORY_PAGE_SIZE,normalizeInventorySort} from './inventory-logic.mjs';
import {buildCrmPath,CRM_PAGE_PATHS,parseCrmPath} from './crm-ui-routes.mjs';
import './style.css';

const SOURCE_NUMBERS=['+919148338801','+917975102130','+919902024973'];
const SOURCE_NUMBER=SOURCE_NUMBERS[0];
const LEAD_STATUSES=['New','Active Follow-up','Waiting on Customer','Waiting on Us','Nurture','Dormant','Converted','Lost','On Hold','Out of Coverage Area'];
const LEAD_STATUS_LABELS={'Out of Coverage Area':'OOC'};
const TENANT_TYPES=['Family','Bachelors','Couples','Students','Working Professionals','Corporate','Other','Not specified'];
const LEAD_SORT_OPTIONS=[['last_message_desc','Last message — newest'],['customer_waiting','Customer replied — newest'],['first_customer_desc','First contacted — newest'],['last_message_asc','Last message — oldest'],['name_asc','Name — A–Z']];
const LEAD_STATUS_TONES={'Active Follow-up':'active','Waiting on Customer':'waiting-customer','Waiting on Us':'waiting-us','Dormant':'dormant','Converted':'converted'};
const LEAD_CLASSIFICATION_TONES={'Qualified Lead':'qualified','Cold Inquiry':'cold'};
const formatLeadDate=value=>{if(!value)return'Not recorded';const d=new Date(value);if(!Number.isFinite(d.valueOf()))return'Not recorded';const parts=new Intl.DateTimeFormat('en-IN',{day:'2-digit',month:'long',year:'numeric',hour:'2-digit',minute:'2-digit',hourCycle:'h23',timeZone:'Asia/Kolkata'}).formatToParts(d);const part=name=>parts.find(p=>p.type===name)?.value||'';return part('day')+'-'+part('month')+'-'+part('year')+' / '+part('hour')+':'+part('minute')};
const TABS=['Overview','Conversation','Requirements','Property Matches','AI & Drafts','Activity & History'];
const MENU=[['Dashboard',LayoutDashboard],['Contact Classification',Inbox],['Leads Inbox',Inbox],['Inventory',Building2],['Activity',ActivityIcon],['Settings',Settings]];
const SUPABASE_URL=import.meta.env.VITE_SUPABASE_URL||'';
const SUPABASE_PUBLISHABLE_KEY=import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY||'';
const supabase=SUPABASE_URL&&SUPABASE_PUBLISHABLE_KEY?createClient(SUPABASE_URL,SUPABASE_PUBLISHABLE_KEY):null;
const money=n=>n!==null&&n!==undefined&&n!==''?'₹'+Number(n).toLocaleString('en-IN'):'Not specified';
const tokenCount=n=>Number.isFinite(Number(n))?Number(n).toLocaleString('en-IN'):'Not recorded';
const estimatedCost=usd=>usd===null||usd===undefined?'Not available':'$'+Number(usd).toFixed(6);
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

const REQUIREMENT_FIELDS=[
 ['bhk','BHK','text'],['budget','Budget','number'],['preferred_locations','Preferred locations','text'],['tenant_type','Tenant Type','select'],['move_in_date','Move In date','date'],['pets','Pets','select'],['veg_nonveg','Veg / Non-Veg','select'],['furnishing','Furnishing','select'],['parking','Parking','select'],['property_type','Property type','text'],['bathrooms','Bathrooms','text'],['occupancy_count','Occupants','number'],['lease_term_months','Lease term (months)','number'],['preferred_floor','Preferred floor','text'],['preferred_amenities','Preferred amenities','text'],['notes','Notes','textarea']
];
const requirementProfile=profile=>profile?{...profile,preferred_locations:Array.isArray(profile.preferred_locations)?profile.preferred_locations.join(', '):profile.preferred_locations||'',preferred_amenities:Array.isArray(profile.preferred_amenities)?profile.preferred_amenities.join(', '):profile.preferred_amenities||''}:{bhk:'',budget:'',preferred_locations:'',tenant_type:'Not specified',move_in_date:'',pets:'Unknown',veg_nonveg:'Unknown',furnishing:'Unknown',parking:'Unknown',property_type:'Any',bathrooms:'',occupancy_count:'',lease_term_months:'',preferred_floor:'',preferred_amenities:'',notes:''};

const requirementEntries=raw=>Object.entries(normalizeRequirements(raw)).filter(([,v])=>v!==null&&v!==undefined&&String(v).trim()!=='');
function PropertyMatchMedia({property}){
 const [failed,setFailed]=useState(false);
 const url=Array.isArray(property?.cloudinary_image_urls)?property.cloudinary_image_urls.find(v=>/^https:\/\/res\.cloudinary\.com\//.test(String(v))):null;
 if(!url||failed)return <div className="photo-fallback"><span>{url?'Property photo unavailable':'No property images available'}</span>{url&&<button type="button" className="secondary" onClick={()=>setFailed(false)}>Retry image</button>}</div>;
 return <div className="photo-fallback"><img src={url} alt={'Property '+property.listing_id} loading="lazy" decoding="async" referrerPolicy="no-referrer" onError={()=>setFailed(true)}/></div>;
}
const PROPERTY_URL_RE=/(https?:\/\/(?:www\.)?(?:housing\.com|99acres\.com|magicbricks\.com)\/[^\s<]+)/gi;
const propertyRefsForMessages=messages=>{
 const refs=[];const grouped=new Set();
 for(const message of messages){
  const urls=[...(String(message.body||'').matchAll(PROPERTY_URL_RE))].map(m=>m[1].replace(/[),.]+$/,''));
  if(!urls.length)continue;
  const key=`property-${message.id}`;const linkedIds=new Set([message.id]);
  for(const child of messages){if(child.replied_to_source_message_id===message.source_message_id)linkedIds.add(child.id)}
  refs.push({key,message,urls:[...new Set(urls)],messageIds:linkedIds});
  linkedIds.forEach(id=>grouped.add(id));
 }
 return {refs,general:messages.filter(m=>!grouped.has(m.id))};
};
const propertyLabel=url=>{try{const u=new URL(url);const slug=decodeURIComponent(u.pathname.split('/').filter(Boolean).pop()||'').replace(/[-_]+/g,' ').replace(/\b\d+\b/g,' ').replace(/\s+/g,' ').trim();return slug?slug.replace(/\b\w/g,c=>c.toUpperCase()):u.hostname.replace(/^www\./,'')}catch{return'Property reference'}};
const auditDateRange=(from,to)=>({from:from?`${from}T00:00:00+05:30`:null,to:to?`${to}T23:59:59.999+05:30`:null});
const auditCategory=action=>{const a=String(action||'').toLowerCase();if(a.startsWith('webhook.')||a.includes('webhook'))return 'Webhook';if(a.startsWith('message.')||a.includes('message'))return 'Message';if(a.startsWith('classification')||a.includes('classif'))return 'Classification';if(a.startsWith('ai.')||a.startsWith('draft.')||a.includes('ai'))return 'AI';if(a.startsWith('inventory.'))return 'Inventory';if(a.startsWith('followup.'))return 'Follow-up';if(a.startsWith('requirements.')||a.includes('requirement'))return 'Requirements';if(a.startsWith('lead.'))return 'Lead';return 'System / Operator'};
function LeadCard({lead,onClick,privacyMode}){
 const displayPhone=lead.normalized_phone?(privacyMode?maskPhone(lead.normalized_phone):lead.normalized_phone):'No phone stored';
 const title=lead.display_name||displayPhone||'Lead';
 const lastMessageBy=lead.last_message_direction==='Incoming'?'Customer':lead.last_message_direction==='Outgoing'?'Us':'Not recorded';
 const status=lead.lead_type||'';
 const overdueFollowups=Number(lead.overdue_followup_count)||0;
 return <button className="lead-card" onClick={onClick} type="button">
  <div className="lead-card-main"><div className="lead-card-identity"><b>{title}</b>{lead.display_name&&<span className="lead-card-phone">{displayPhone}</span>}</div></div>
  <div className={'lead-card-classification lead-card-classification-'+(LEAD_CLASSIFICATION_TONES[lead.classification]||'neutral')}><small>Classification</small><strong>{lead.classification||'Not recorded'}</strong></div>
  <div className="lead-card-meta lead-card-meta-minimal"><span className={'lead-card-status lead-card-status-'+(LEAD_STATUS_TONES[status]||'neutral')}>Lead status · {LEAD_STATUS_LABELS[status]||status||'Not recorded'}</span><span>Source number · {lead.source_number||SOURCE_NUMBER}</span>{overdueFollowups>0&&<span className="lead-card-attention"><Clock3 size={13} aria-hidden="true"/>Overdue follow-up · {overdueFollowups}</span>}</div>
  <div className="lead-card-activity" aria-label="Lead conversation activity">
   <div><small>Contacted date</small><strong>{formatLeadDate(lead.contacted_at)}</strong></div>
   <div><small>Last message sent by</small><strong>{lastMessageBy}</strong></div>
   <div><small>Last message date</small><strong>{formatLeadDate(lead.last_message_at)}</strong></div>
  </div>
 </button>;
}

class AppErrorBoundary extends Component{
 static getDerivedStateFromError(){return{hasError:true}}
 constructor(props){super(props);this.state={hasError:false}}
 componentDidCatch(error){console.error('CRM UI render error',error)}
 render(){if(this.state.hasError)return <div className="app-error-shell"><div className="auth-card"><h1>CRM workspace error</h1><p>The lead workspace hit a display error. Your saved CRM/AI data is not deleted. Reload the workspace to continue.</p><button className="primary" type="button" onClick={()=>window.location.reload()}>Reload CRM</button></div></div>;return this.props.children}
}

function App(){
 const[initialRoute]=useState(()=>{
  const route=parseCrmPath(window.location.pathname);
  if(!route.isRoot)return route;
  try{const stored=window.sessionStorage.getItem('efps-crm-active-page');if(Object.hasOwn(CRM_PAGE_PATHS,stored))return{...route,page:stored}}catch{}
  return route;
 });
 const[authReady,setAuthReady]=useState(false);
 const[authenticated,setAuthenticated]=useState(false);
 const[operator,setOperator]=useState('');
 const[authError,setAuthError]=useState('');
 const[authBusy,setAuthBusy]=useState(false);
 const[privacyMode,setPrivacyMode]=useState(()=>{try{const v=window.sessionStorage.getItem('efps-crm-privacy-mode');return v===null?true:v==='masked'}catch{return true}});
 const[online,setOnline]=useState(()=>typeof navigator==='undefined'||navigator.onLine!==false);
 const[page,setPage]=useState(initialRoute.page);
 const[routeNotFound,setRouteNotFound]=useState(initialRoute.notFound);
 const[tab,setTab]=useState(initialRoute.tab);
 const[query,setQuery]=useState('');
 const[debouncedQuery,setDebouncedQuery]=useState('');
 const[offset,setOffset]=useState(0);
 const[leads,setLeads]=useState([]);
 const[total,setTotal]=useState(0);
 const[loading,setLoading]=useState(true);
 const[error,setError]=useState('');
 const[selectedId,setSelectedId]=useState(initialRoute.leadId);
 const[workspace,setWorkspace]=useState(null);
 const[workspaceState,setWorkspaceState]=useState('idle');
 const[ai,setAi]=useState(null);
 const[aiState,setAiState]=useState('idle');
 const[inventoryData,setInventoryData]=useState(null);
 const[inventoryState,setInventoryState]=useState('loading');
 const[inventoryQuery,setInventoryQuery]=useState('');
 const[debouncedInventoryQuery,setDebouncedInventoryQuery]=useState('');
 const[inventorySort,setInventorySort]=useState('latest');
 const[inventoryOffset,setInventoryOffset]=useState(0);
 const[inventoryFilters,setInventoryFilters]=useState({status:'All',bhk:'All',locality:'All',withPhotos:null});
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
 const[actionError,setActionError]=useState('');
 const[leadSort,setLeadSort]=useState('last_message_desc');
 const[leadStatus,setLeadStatus]=useState('');
 const[tenantType,setTenantType]=useState('Not specified');
 const[realtimeError,setRealtimeError]=useState('');
 const[classificationDrafts,setClassificationDrafts]=useState({});
 const[classificationSaving,setClassificationSaving]=useState({});
 const[classificationErrors,setClassificationErrors]=useState({});
 const[classificationError,setClassificationError]=useState('');
 const[dashboardStats,setDashboardStats]=useState(null);
 const[dashboardState,setDashboardState]=useState('loading');
 const[auditRows,setAuditRows]=useState([]);
 const[auditState,setAuditState]=useState('idle');
 const[auditFrom,setAuditFrom]=useState('');
 const[auditTo,setAuditTo]=useState('');
 const[auditRangePreset,setAuditRangePreset]=useState('all');
 const[auditOffset,setAuditOffset]=useState(0);
 const[auditHasMore,setAuditHasMore]=useState(false);
 const[leadAuditRows,setLeadAuditRows]=useState([]);
 const[leadAuditState,setLeadAuditState]=useState('idle');
 const[leadAuditOffset,setLeadAuditOffset]=useState(0);
 const[leadAuditHasMore,setLeadAuditHasMore]=useState(false);
 const[classificationOffset,setClassificationOffset]=useState(0);
 const classificationFilterKeyRef=useRef(classificationFilter+'|'+sourceFilter);
 const[archiveState,setArchiveState]=useState('');
 const[requirementsDraft,setRequirementsDraft]=useState(null);
 const[requirementsState,setRequirementsState]=useState('idle');
 const[draftBody,setDraftBody]=useState('');
 const[selectedDraftId,setSelectedDraftId]=useState(null);
 const[draftCheck,setDraftCheck]=useState(null);
 const[draftState,setDraftState]=useState('idle');
 const[followupDueAt,setFollowupDueAt]=useState('');
 const[followupNote,setFollowupNote]=useState('');
 const[followupState,setFollowupState]=useState('idle');
 const[aiError,setAiError]=useState('');

 useEffect(()=>{let active=true;fetch('/api/auth/session',{cache:'no-store',credentials:'include'}).then(async r=>{const d=await r.json().catch(()=>({}));if(!r.ok)throw Error('Authentication unavailable');return d}).then(d=>{if(active){setAuthenticated(Boolean(d.authenticated));setOperator(d.user||'');setAuthReady(true)}}).catch(e=>{if(active){setAuthError(e.message||'Authentication unavailable');setAuthReady(true)}});return()=>{active=false}},[authenticated]);
 useEffect(()=>{try{window.sessionStorage.setItem('efps-crm-active-page',page);window.sessionStorage.setItem('efps-crm-privacy-mode',privacyMode?'masked':'revealed')}catch{}},[page,privacyMode]);
 useEffect(()=>{const on=()=>setOnline(true),off=()=>setOnline(false);window.addEventListener('online',on);window.addEventListener('offline',off);return()=>{window.removeEventListener('online',on);window.removeEventListener('offline',off)}},[]);
 const apiFetch=(url,options={})=>fetch(url,{...options,credentials:'include'}).then(r=>{if(r.status===401){setAuthenticated(false);setAuthReady(true)}return r});
 function navigateRoute(route,{replace=false}={}){
  const next=route?.notFound?{page:'Not Found',leadId:null,tab:'Overview',notFound:true}:{page:route?.page||'Dashboard',leadId:route?.leadId??null,tab:route?.tab||'Overview',notFound:false};
  if(!next.notFound){
   const path=buildCrmPath(next);
   if(window.location.pathname!==path)window.history[replace?'replaceState':'pushState']({crmUiRoute:true},'',path);
  }
  setRouteNotFound(next.notFound);
  setPage(next.page);
  setSelectedId(next.leadId);
  setTab(next.tab);
  setWorkspace(previous=>previous?.lead?.id===next.leadId?previous:null);
  setActionError('');
 }
 useEffect(()=>{
  if(initialRoute.notFound)return;
  const path=buildCrmPath(initialRoute);
  if(window.location.pathname!==path)window.history.replaceState({crmUiRoute:true},'',path);
 },[]);
 useEffect(()=>{
  const onPopState=()=>{
   const next=parseCrmPath(window.location.pathname);
   setRouteNotFound(next.notFound);
   setPage(next.page);
   setSelectedId(next.leadId);
   setTab(next.tab);
   setWorkspace(previous=>previous?.lead?.id===next.leadId?previous:null);
   setActionError('');
  };
  window.addEventListener('popstate',onPopState);
  return()=>window.removeEventListener('popstate',onPopState);
 },[]);
 useEffect(()=>{const timeout=setTimeout(()=>setDebouncedQuery(query),220);return()=>clearTimeout(timeout)},[query]);
 useEffect(()=>{const timeout=setTimeout(()=>{setDebouncedInventoryQuery(inventoryQuery);setInventoryOffset(0)},220);return()=>clearTimeout(timeout)},[inventoryQuery]);
 const signIn=async e=>{e.preventDefault();setAuthBusy(true);setAuthError('');try{const r=await fetch('/api/auth/login',{method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:e.currentTarget.username.value,password:e.currentTarget.password.value})});const d=await r.json().catch(()=>({}));if(!r.ok)throw Error(d.error||'Sign-in failed');setAuthenticated(true);setOperator(d.user||'')}catch(err){setAuthError(err.message)}finally{setAuthBusy(false)}};
 const signOut=async()=>{try{await fetch('/api/auth/logout',{method:'POST',credentials:'include'})}finally{navigateRoute({page:'Dashboard'},{replace:true});setAuthenticated(false);setOperator('')}};
 const togglePrivacy=()=>setPrivacyMode(v=>!v);
 const updateInventoryQuery=(value,immediate=false)=>{setInventoryQuery(value);if(immediate){setDebouncedInventoryQuery(value);setInventoryOffset(0)}};
 const exportCurrentSource=async()=>{if(!online)return;setActionError('');try{const r=await apiFetch('/api/db/export?source_number='+encodeURIComponent(sourceFilter));if(!r.ok){const d=await r.json().catch(()=>({}));throw Error(d.error||'Export unavailable')}const blob=await r.blob();const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='easyfind-crm-export.csv';document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),0)}catch(e){setActionError(e?.message||'Export unavailable')}};
 const setAuditRange=(from,to,preset='custom')=>{setAuditFrom(from||'');setAuditTo(to||'');setAuditRangePreset(preset);setAuditOffset(0);setLeadAuditOffset(0)};
 const applyAuditPreset=preset=>{const d=new Date();const iso=x=>x.toISOString().slice(0,10);if(preset==='all')return setAuditRange('','','all');if(preset==='today'){const v=iso(d);return setAuditRange(v,v,'today')}if(preset==='7d'){const from=new Date(d);from.setDate(d.getDate()-6);return setAuditRange(iso(from),iso(d),'7d')}if(preset==='30d'){const from=new Date(d);from.setDate(d.getDate()-29);return setAuditRange(iso(from),iso(d),'30d')}if(preset==='this_month')return setAuditRange(iso(new Date(d.getFullYear(),d.getMonth(),1)),iso(new Date(d.getFullYear(),d.getMonth()+1,0)),'this_month');if(preset==='previous_month')return setAuditRange(iso(new Date(d.getFullYear(),d.getMonth()-1,1)),iso(new Date(d.getFullYear(),d.getMonth(),0)),'previous_month');setAuditRange(auditFrom,auditTo,'custom')};
 const loadAudit=async(isCurrent=()=>true)=>{if(typeof isCurrent!=='function')isCurrent=()=>true;setAuditState('loading');try{const range=auditDateRange(auditFrom,auditTo);const qs=new URLSearchParams({limit:'100',offset:String(auditOffset)});if(range.from)qs.set('from',range.from);if(range.to)qs.set('to',range.to);const r=await apiFetch('/api/audit/recent?'+qs.toString());if(!r.ok)throw Error('Audit unavailable');const d=await r.json();if(!isCurrent())return;setAuditRows(d.rows||[]);setAuditHasMore(Boolean(d.hasMore));setAuditState('ready')}catch{if(isCurrent()){setAuditRows([]);setAuditHasMore(false);setAuditState('unavailable')}}};
 const loadLeadAudit=async(isCurrent=()=>true)=>{if(!selectedId)return;setLeadAuditState('loading');try{const range=auditDateRange(auditFrom,auditTo);const qs=new URLSearchParams({limit:'100',offset:String(leadAuditOffset)});if(range.from)qs.set('from',range.from);if(range.to)qs.set('to',range.to);const r=await apiFetch('/api/audit/lead/'+encodeURIComponent(selectedId)+'?'+qs.toString());if(!r.ok)throw Error('Lead audit unavailable');const d=await r.json();if(!isCurrent())return;setLeadAuditRows(d.rows||[]);setLeadAuditHasMore(Boolean(d.hasMore));setLeadAuditState('ready')}catch{if(isCurrent()){setLeadAuditRows([]);setLeadAuditHasMore(false);setLeadAuditState('unavailable')}}};
 const createFollowup=async()=>{if(!selectedId||!online||followupState==='saving'||!followupDueAt)return;setFollowupState('saving');setActionError('');try{const dueAt=new Date(followupDueAt).toISOString();const r=await apiFetch('/api/db/followups',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({leadId:selectedId,dueAt,note:followupNote})});const d=await r.json().catch(()=>({}));if(!r.ok)throw Error(d.error||'Follow-up could not be scheduled');setFollowupDueAt('');setFollowupNote('');setFollowupState('saved');setRefreshToken(v=>v+1)}catch(e){setFollowupState('error');setActionError(e?.message||'Follow-up could not be scheduled')}finally{setTimeout(()=>setFollowupState('idle'),2000)}};
 const completeFollowup=async id=>{if(!online)return;setActionError('');try{const r=await apiFetch('/api/db/followups/'+encodeURIComponent(id)+'/complete',{method:'POST'});const d=await r.json().catch(()=>({}));if(!r.ok)throw Error(d.error||'Follow-up could not be completed');setRefreshToken(v=>v+1)}catch(e){setActionError(e?.message||'Follow-up could not be completed')}};
 useEffect(()=>{if(!authenticated||page!=='Activity')return;let active=true;loadAudit(()=>active);return()=>{active=false}},[authenticated,page,refreshToken,auditFrom,auditTo,auditOffset]);
 useEffect(()=>{if(!authenticated||!selectedId||tab!=='Activity & History')return;let active=true;loadLeadAudit(()=>active);return()=>{active=false}},[authenticated,selectedId,tab,refreshToken,auditFrom,auditTo,leadAuditOffset]);

 useEffect(()=>{
  let active=true;
  if(!authenticated)return()=>{active=false};
  async function load(){
   setLoading(true);setError('');
   try{
    const r=await apiFetch('/api/db/leads?limit=100&offset='+offset+'&source_number='+encodeURIComponent(sourceFilter)+'&lead_status='+encodeURIComponent(leadStatusFilter)+'&lead_sort='+encodeURIComponent(leadSort)+'&lead_search='+encodeURIComponent(debouncedQuery.trim()),{cache:'no-store',credentials:'include'});
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
 },[authenticated,offset,sourceFilter,leadStatusFilter,leadSort,debouncedQuery,refreshToken]);

 useEffect(()=>{
  let active=true;
  if(!authenticated||page!=='Contact Classification')return()=>{active=false};
  setClassificationState('loading');
   const filterKey=classificationFilter+'|'+sourceFilter;
   if(classificationFilterKeyRef.current!==filterKey){classificationFilterKeyRef.current=filterKey;if(classificationOffset!==0){setClassificationOffset(0);return()=>{active=false}}}
  const qs=new URLSearchParams({limit:'100',offset:String(classificationOffset)});if(['not_pushed','promoted','unqualified'].includes(classificationFilter))qs.set('status',classificationFilter);if(sourceFilter)qs.set('source_number',sourceFilter);
  apiFetch('/api/db/classifications?'+qs.toString(),{cache:'no-store',credentials:'include'}).then(async r=>{const d=await r.json().catch(()=>({}));if(!r.ok)throw Error(d.error||('Classification records unavailable (HTTP '+r.status+')'));return d}).then(d=>{if(active){const rows=Array.isArray(d.classifications)?d.classifications:[];setClassifications(rows);setClassificationTotal(Number(d.total)||0);setClassificationDrafts(prev=>{const next={...prev};for(const row of rows)next[row.id]=row.classification_code;return next});setClassificationError('');setClassificationState('ready')}}).catch(e=>{if(active){setClassifications([]);setClassificationError(e.message||'Classification records unavailable');setClassificationState('unavailable')}});
  return()=>{active=false};
 },[authenticated,page,classificationFilter,sourceFilter,classificationOffset,refreshToken]);

 useEffect(()=>{
  let active=true;
  if(!authenticated)return()=>{active=false};
  setDashboardState('loading');
  apiFetch('/api/db/stats?source_number='+encodeURIComponent(sourceFilter),{cache:'no-store',credentials:'include'}).then(async r=>{if(!r.ok)throw Error('Dashboard stats unavailable');return r.json()}).then(d=>{if(active){setDashboardStats(d);setDashboardState('ready')}}).catch(()=>{if(active){setDashboardStats(null);setDashboardState('unavailable')}});
  return()=>{active=false};
 },[authenticated,sourceFilter,refreshToken]);

 useEffect(()=>{
  let active=true;
  if(!authenticated||page!=='Inventory')return()=>{active=false};
  async function load(){
   try{
    const qs=new URLSearchParams({limit:String(INVENTORY_PAGE_SIZE),offset:String(inventoryOffset),inventory_sort:normalizeInventorySort(inventorySort),status:inventoryFilters.status==='All'?'':inventoryFilters.status,bhk:inventoryFilters.bhk==='All'?'':inventoryFilters.bhk,locality:inventoryFilters.locality==='All'?'':inventoryFilters.locality,with_photos:inventoryFilters.withPhotos===null?'':String(inventoryFilters.withPhotos),search:debouncedInventoryQuery.trim()});
    const r=await apiFetch('/api/inventory/overview?'+qs.toString(),{cache:'no-store',credentials:'include'});
    if(!r.ok)throw Error('Inventory unavailable');
    const data=await r.json();
    if(!Array.isArray(data.rows)||!data.summary||!data.facets||!Number.isFinite(Number(data.total)))throw Error('Inventory response incomplete');
    if(active)setInventoryData(data),setInventoryState('live');
   }catch{if(active)setInventoryState('unavailable')}
  }
  load();
  return()=>{active=false};
 },[authenticated,page,inventoryOffset,inventorySort,inventoryFilters,debouncedInventoryQuery,refreshToken]);

 useEffect(()=>{
  let active=true;
  if(!authenticated)return()=>{active=false};
  if(!selectedId){setWorkspace(null);setWorkspaceState('idle');setMatches([]);setMatchState('idle');return()=>{active=false}};
  setWorkspaceState('loading');setAi(null);setAiState('idle');setMatches([]);setMatchState('loading');
  async function load(){
   try{
    const r=await apiFetch('/api/db/leads/'+encodeURIComponent(selectedId)+'/workspace?source_number='+encodeURIComponent(sourceFilter),{cache:'no-store',credentials:'include'});
    if(!r.ok)throw Error('Lead workspace unavailable');
    const data=await r.json();
    if(!active)return;
    setWorkspace(data);setSelectedDraftId(data.drafts?.[0]?.id||null);setDraftCheck(null);setLeadStatus(data.lead?.lead_type||'New');setTenantType(data.lead?.tenant_type||'Not specified');setRequirementsDraft(requirementProfile(data.requirement_profile));setDraftBody(data.drafts?.[0]?.body||'');setAiError('');setWorkspaceState('ready');
    const req=requirementProfile(data.requirement_profile);
    const bhkMatch=String(req.bhk||'').match(/\d+/);
    const bhk=bhkMatch?bhkMatch[0]:'';
    const budgetMatch=String(req.budget??'').replace(/,/g,'').match(/\d+(?:\.\d+)?/);
    const budget=budgetMatch?budgetMatch[0]:null;
    const locality=String(req.preferred_locations||'').trim();
    if(!(bhk||budget||locality)){setMatchState('insufficient');return}
    const qs=new URLSearchParams({limit:'50'});
    if(bhk)qs.set('bhk',bhk+' BHK');
    if(budget)qs.set('budget',budget);
    if(locality)qs.set('locality',locality);
    if(req.furnishing)qs.set('furnishing',String(req.furnishing));
    if(req.pet_friendly)qs.set('pet_friendly',String(req.pet_friendly));
    const mr=await apiFetch('/api/inventory/matches?'+qs.toString(),{cache:'no-store',credentials:'include'});
    if(!mr.ok)throw Error('Inventory match lookup unavailable');
    const md=await mr.json();
    if(active){setMatches(Array.isArray(md.rows)?md.rows:[]);setMatchState('ready')}
   }catch(e){if(active){setWorkspaceState('unavailable');setMatchState('unavailable')}}
  }
  load();
  return()=>{active=false};
 },[authenticated,selectedId,sourceFilter,refreshToken]);

 useEffect(()=>{
  if(!authenticated){setRealtimeState('unconfigured');setRealtimeError('');return()=>{}}
  if(!supabase){setRealtimeState('unconfigured');setRealtimeError('Supabase browser Realtime is not configured');return()=>{}}
  let active=true;
  setRealtimeState('connecting');setRealtimeError('');
  const channel=supabase.channel('crm:live')
   .on('broadcast',{event:'message_inserted'},()=>{if(active)setRefreshToken(v=>v+1)})
   .subscribe((status,err)=>{if(!active)return;setRealtimeState(status==='SUBSCRIBED'?'live':status==='CHANNEL_ERROR'?'error':'connecting');setRealtimeError(status==='SUBSCRIBED'?'':(err?.message||String(err||status)))})
  return()=>{active=false;supabase.removeChannel(channel)};
 },[authenticated]);

 const visibleLeads=useMemo(()=>leads,[leads]);

 function openLead(id){navigateRoute({page:'Leads Inbox',leadId:id,tab:'Overview'})}
 async function toggleArchive(){
  if(!selectedId||!online||archiveState==='saving')return;
  const archived=workspace?.lead?.status==='Archived';
  if(!window.confirm(archived?'Restore this lead to its previous record status?':'Archive this lead? It stays stored and can be restored.'))return;
  setArchiveState('saving');
  try{const r=await apiFetch('/api/db/leads/'+encodeURIComponent(selectedId)+'/'+(archived?'restore':'archive'),{method:'POST'});const d=await r.json().catch(()=>({}));if(!r.ok)throw Error(d.error||'Lead action failed');setActionError('');setArchiveState(archived?'restored':'archived');setWorkspace(prev=>prev?{...prev,lead:d}:prev);refresh()}catch(e){setActionError(e?.message||'Lead action failed');setArchiveState('error')}finally{setTimeout(()=>setArchiveState(''),2500)}
 }
 function backToInbox(){setSelectedDraftId(null);navigateRoute({page:'Leads Inbox'})}
 function refresh(){setRefreshToken(v=>v+1)}
 function classifyContact(id,classification){setClassificationDrafts(prev=>({...prev,[id]:classification}));setClassificationErrors(prev=>{const next={...prev};delete next[id];return next})}
 async function saveClassification(row){const classification=classificationDrafts[row.id];if(!classification||classification==='pending'||classification===row.classification_code)return;setClassificationSaving(prev=>({...prev,[row.id]:true}));setClassificationErrors(prev=>{const next={...prev};delete next[row.id];return next});try{const r=await apiFetch('/api/db/classifications/'+row.id,{method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify({classification,source:'operator'})});const d=await r.json().catch(()=>({}));if(!r.ok)throw Error(d.error||('Classification update failed (HTTP '+r.status+')'));setClassificationOffset(0);refresh()}catch(e){setClassificationErrors(prev=>({...prev,[row.id]:e.message||'Classification update failed'}))}finally{setClassificationSaving(prev=>{const next={...prev};delete next[row.id];return next})}}
 function updateLead(id,patch){setActionError('');return apiFetch('/api/db/leads/'+encodeURIComponent(id),{method:'PATCH',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify(patch)}).then(async r=>{const d=await r.json().catch(()=>({}));if(!r.ok)throw Error(d.error||'Lead update failed');return d}).then(()=>refresh()).catch(error=>{setActionError(error?.message||'Lead update failed');setRefreshToken(v=>v+1);throw error})}
 async function saveRequirements(){
  if(!workspace?.lead?.id||!requirementsDraft)return;
  setActionError('');setRequirementsState('saving');
  try{const profile={...requirementsDraft,preferred_locations:String(requirementsDraft.preferred_locations||'').split(',').map(x=>x.trim()).filter(Boolean),preferred_amenities:String(requirementsDraft.preferred_amenities||'').split(',').map(x=>x.trim()).filter(Boolean)};const r=await apiFetch('/api/db/leads/'+encodeURIComponent(workspace.lead.id)+'/requirements',{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({profile})});const d=await r.json().catch(()=>({}));if(!r.ok)throw Error(d.error||'Requirements update failed');setRequirementsDraft(requirementProfile(d));setRequirementsState('saved');setRefreshToken(v=>v+1);setTimeout(()=>setRequirementsState('idle'),1500)}
  catch(e){setRequirementsState('error');setActionError(e?.message||'Requirements update failed')}
 }
 async function runAi(){
  if(!workspace?.lead?.id)return;
  setAiState('running');setAi(null);setAiError('');
  try{
   const r=await apiFetch('/api/ai/analyze-real',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({leadId:workspace.lead.id})});
   const d=await r.json().catch(()=>({}));
   if(!r.ok)throw Error(d.error||'Real AI unavailable');
   if(!d.run||!d.proposal)throw Error('AI returned an incomplete result');
   setAi(d);
   if(typeof d.draft?.body==='string')setDraftBody(d.draft.body);
   setWorkspace(prev=>prev?{...prev,ai_runs:d.run?[d.run,...(prev.ai_runs||[])]:prev.ai_runs,drafts:d.draft?[d.draft,...(prev.drafts||[])]:prev.drafts}:prev);
   setAiState('ready');
  }catch(e){
   setAiError(e?.message||'Real AI unavailable');
   setAiState('unavailable');
  }
 }
 async function acceptAiRequirements(runId){
  setActionError('');
  try{const r=await apiFetch('/api/ai/runs/'+encodeURIComponent(runId)+'/accept',{method:'POST'});const d=await r.json().catch(()=>({}));if(!r.ok)throw Error(d.error||'Could not accept AI requirement changes');setRefreshToken(v=>v+1)}
  catch(e){setActionError(e?.message||'Could not accept AI requirement changes')}
 }
 async function rejectAiRequirements(runId){
  setActionError('');
  try{const r=await apiFetch('/api/ai/runs/'+encodeURIComponent(runId)+'/reject',{method:'POST'});const d=await r.json().catch(()=>({}));if(!r.ok)throw Error(d.error||'Could not reject AI requirement changes');setRefreshToken(v=>v+1)}
  catch(e){setActionError(e?.message||'Could not reject AI requirement changes')}
 }
 async function saveDraftVersion(){if(!workspace?.lead?.id||!draftBody.trim())return;setDraftState('saving');try{const r=await apiFetch('/api/db/leads/'+encodeURIComponent(workspace.lead.id)+'/drafts',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({body:draftBody,aiRunId:workspace?.drafts?.find(d=>d.id===selectedDraftId)?.ai_run_id||workspace?.drafts?.[0]?.ai_run_id||null,aiProvider:workspace?.drafts?.find(d=>d.id===selectedDraftId)?.ai_provider||workspace?.drafts?.[0]?.ai_provider||'operator-edit',modelName:workspace?.drafts?.find(d=>d.id===selectedDraftId)?.model_name||workspace?.drafts?.[0]?.model_name||'operator-edit',evidenceMessageIds:workspace?.drafts?.find(d=>d.id===selectedDraftId)?.evidence_message_ids||[],evidenceSummary:workspace?.drafts?.find(d=>d.id===selectedDraftId)?.evidence_summary||''})});if(!r.ok)throw Error();const d=await r.json();setWorkspace(prev=>prev?{...prev,drafts:[d,...(prev.drafts||[])]}:prev);setSelectedDraftId(d.id);setDraftCheck(null);setDraftState('saved');setTimeout(()=>setDraftState('idle'),1200)}catch{setDraftState('error')}}
 async function markDraft(id,status){
  try{
   const r=await apiFetch('/api/drafts/'+encodeURIComponent(id)+'/status',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({status})});
   const d=await r.json().catch(()=>null);
   if(!r.ok)throw Error(d?.error||'Draft status update failed');
   if(d)setWorkspace(prev=>prev?{...prev,drafts:(prev.drafts||[]).map(x=>x.id===d.id?{...x,...d}:x)}:prev);
   return true;
  }catch(e){setActionError(e?.message||'Draft status update failed');return false}
 }
 async function copyDraft(){
  const draft=workspace?.drafts?.find(d=>d.id===selectedDraftId)||workspace?.drafts?.[0];
  if(!draft)return;
  if(!navigator.clipboard?.writeText){setActionError('Clipboard access is unavailable. Use the draft editor to copy the message manually.');return}
  try{await navigator.clipboard.writeText(draftBody);await markDraft(draft.id,'copied')}catch(e){setActionError(e?.message||'Could not copy draft')}
 }
 async function openDraftInWhatsApp(){
  const draft=workspace?.drafts?.find(d=>d.id===selectedDraftId)||workspace?.drafts?.[0];if(!draft)return;
  setDraftCheck({loading:true});
  try{const r=await apiFetch('/api/drafts/'+encodeURIComponent(draft.id)+'/preflight');const d=await r.json().catch(()=>({}));if(!r.ok)throw Error(d.error||'Pre-send check failed');setDraftCheck(d);if(!d.ready)return;const phone=String(workspace?.lead?.normalized_phone||'').replace(/\D/g,'');if(!phone)return;window.open('https://wa.me/'+phone,'_blank','noopener,noreferrer');await markDraft(draft.id,'opened');}catch(e){setDraftCheck({ready:false,blocking:[{code:'check_failed',message:e.message||'Pre-send check failed'}],warnings:[]})}
 }

 const filteredMatches=matches;
 if(!authReady)return <div className="auth-shell"><div className="auth-card"><div className="brand"><span className="brandmark">EF</span><span>EasyFind<small>PRIVATE CRM</small></span></div><p>Checking operator session…</p></div></div>;
 if(!authenticated)return <div className="auth-shell"><form className="auth-card" onSubmit={signIn}><div className="brand"><span className="brandmark">EF</span><span>EasyFind<small>PRIVATE CRM</small></span></div><h1>Operator sign in</h1><p>Customer data is not loaded before authentication succeeds.</p><label>Username<input name="username" autoComplete="username" required/></label><label>Password<input name="password" autoComplete="current-password" type="password" required/></label>{authError&&<div className="notice">{authError}</div>}<button type="submit" className="primary auth-submit" disabled={authBusy}>{authBusy?'Signing in…':'Sign in'}</button><small className="muted">8-hour inactivity timeout · 12-hour maximum session</small></form></div>;
 return <div className="app">
  <a className="skip-link" href="#main-content">Skip to main content</a>
  <aside className="sidebar">
   <div className="brand"><span className="brandmark">EF</span><span>EasyFind<small>LEADS WORKSPACE</small></span></div>
   <nav aria-label="Primary navigation">{MENU.map(([name,Icon])=><button type="button" aria-current={page===name?'page':undefined} className={page===name?'nav active':'nav'} key={name} onClick={()=>navigateRoute({page:name})}><Icon size={19}/>{name}</button>)}</nav>
   <div className="sidebottom"><CheckCircle2 size={16}/> Production CRM<br/><small>Live source: {SOURCE_NUMBER}</small></div>
  </aside>
  <main className="main" id="main-content" tabIndex={-1}>
   <header className="top">
    <div className="top-title">{selectedId&&<button className="header-back" onClick={backToInbox} type="button"><ChevronLeft size={17}/> Leads Inbox</button>}<div><strong>{selectedId?'Lead Workspace':page}</strong><small>EasyFind Property Solutions / CRM</small></div></div>
    <div className="topright"><span className={'chip '+(error?'red':'green')} role="status">{error?'CRM data unavailable':'Production data'}</span><span className={"chip "+(realtimeState==='live'?'green':'')}>Realtime: {realtimeState}</span><span className="chip source">{SOURCE_NUMBER}</span><button className="privacy-toggle" type="button" onClick={togglePrivacy}><ShieldCheck size={15}/> Privacy: {privacyMode?'Masked':'Revealed'}</button><span className={"chip "+(online?'green':'red')}>{online?'Online':'Offline'}</span><button className="icon-action" type="button" onClick={signOut} title="Sign out"><LogOut size={15}/></button><span className="avatar">{operator?operator.slice(0,2).toUpperCase():'ZH'}</span></div>
   </header>
   <div className="content">{actionError&&<div className="notice action-error" role="alert"><b>Action failed:</b> {actionError} <button type="button" onClick={()=>setActionError('')}>Dismiss</button></div>}{!online&&<div className="offline-banner"><WifiOff size={15}/> Offline. Reading the current UI is allowed; writes and exports are disabled until the connection returns.</div>}

    {page==='Contact Classification'&&<section><div className="heading"><div><h1>Contact Classification</h1><p>Classify new WhatsApp contacts once. Qualified contacts move to CRM; other classifications stay outside CRM.</p></div><button type="button" className="primary" onClick={refresh} disabled={!online}><RefreshCw size={14}/> Refresh</button></div><div className="panel standalone"><div className="classification-header"><div><h3>Simple qualification queue</h3><p>Use the three tabs below to separate pending, qualified, and unqualified contacts.</p></div><label>Lead source <select value={sourceFilter} onChange={e=>setSourceFilter(e.target.value)}>{SOURCE_NUMBERS.map(n=><option key={n} value={n}>{n}</option>)}</select></label></div><div className="classification-tabs"><button className={classificationFilter==='not_pushed'?'selected':''} type="button" onClick={()=>setClassificationFilter('not_pushed')}>Waiting for classification <b>{dashboardStats?.notPushedClassificationCount??(classificationFilter==='not_pushed'?classificationTotal:0)}</b></button><button className={classificationFilter==='promoted'?'selected':''} type="button" onClick={()=>setClassificationFilter('promoted')}>Qualified lead pushed to CRM <b>{dashboardStats?.qualifiedClassificationCount??0}</b></button><button className={classificationFilter==='unqualified'?'selected':''} type="button" onClick={()=>setClassificationFilter('unqualified')}>Unqualified leads <b>{dashboardStats?.unqualifiedClassificationCount??0}</b></button></div>{classificationFilter==='not_pushed'&&<div className="notice">This tab contains only contacts still awaiting classification. A <b>Qualified Lead</b> Update moves the contact to the CRM tab; any other classification moves it to <b>Unqualified leads</b> after the database confirms the write.</div>}{classificationFilter==='promoted'&&<div className="notice">These contacts have already been promoted to CRM. Their preserved WhatsApp messages are linked to the CRM lead.</div>}{classificationFilter==='unqualified'&&<div className="notice">These contacts were explicitly classified as something other than <b>Qualified Lead</b>. They remain outside CRM.</div>}{classificationState==='loading'&&<div className="empty">Loading classifications...</div>}{classificationState==='unavailable'&&<div className="notice">Classification records are unavailable. {classificationError||'No fallback data is shown.'}</div>}{classificationState==='ready'&&(classifications.length?classifications.map(c=>{const draft=classificationDrafts[c.id]??c.classification_code;const saving=Boolean(classificationSaving[c.id]);const changed=draft&&draft!=='pending'&&draft!==c.classification_code;const promoted=c.status==='promoted';return <article className="event classification-row" key={c.id}><div className="classification-contact"><b>{privacyMode?maskPhone(c.phone):c.phone}</b><small>{promoted?'Qualified Lead · CRM lead':'Pending / '+(c.classification_label||'classification')} · {c.source_number}</small>{privacyMode?<button className="secondary" type="button" onClick={togglePrivacy}><ShieldCheck size={14}/> Reveal phone</button>:<a className="whatsapp-link" href={'https://wa.me/'+String(c.phone||'').replace(/\D/g,'')} target="_blank" rel="noreferrer">Open WhatsApp</a>}{classificationErrors[c.id]&&<small className="error">Update failed: {classificationErrors[c.id]}</small>}</div>{!promoted?<div className="classification-actions"><select value={draft==='pending'?'pending':draft} disabled={saving||!online} onChange={e=>classifyContact(c.id,e.target.value)}><option value="pending" disabled>Choose classification</option><option value="qualified_lead">Qualified Lead</option><option value="promotion">Promotion / Marketing</option><option value="cold_inquiry">Cold Inquiry</option><option value="property_listing_sent">Property Listing Sent</option><option value="vendor_supplier">Vendor / Supplier</option><option value="agent_partner">Agent / Partner</option><option value="personal_family">Family / personal</option><option value="internal">Internal</option><option value="business">Business</option><option value="unknown">Unknown</option></select><button className="primary" type="button" disabled={!changed||saving} onClick={()=>saveClassification(c)}>{saving?'Saving...':'Update'}</button></div>:<span className="chip green">In Leads Inbox</span>}</article>}):<div className="empty">No contacts in this queue.</div>)}</div><div className="pagination"><button type="button" disabled={classificationOffset===0} onClick={()=>setClassificationOffset(Math.max(0,classificationOffset-100))}>Previous</button><span>{classificationTotal?classificationOffset+1:0}–{Math.min(classificationOffset+classifications.length,classificationTotal)} of {classificationTotal}</span><button type="button" disabled={classificationOffset+100>=classificationTotal} onClick={()=>setClassificationOffset(classificationOffset+100)}>Next</button></div></section>}
    {page==='Inventory'&&<InventoryPanel data={inventoryData} state={inventoryState} refresh={refresh} query={inventoryQuery} setQuery={updateInventoryQuery} sort={inventorySort} setSort={value=>{setInventorySort(normalizeInventorySort(value));setInventoryOffset(0)}} filters={inventoryFilters} setFilters={setInventoryFilters} offset={inventoryOffset} setOffset={setInventoryOffset}/>}
    {page==='Activity'&&<section><div className="heading"><div><h1>Audit Activity</h1><p>All CRM activity across leads, messages, classifications, AI, inventory, webhooks and operator actions. Lead Workspace history is scoped separately.</p></div><button type="button" className="primary" onClick={loadAudit} disabled={!online||auditState==='loading'}><RefreshCw size={14}/> {auditState==='loading'?'Refreshing…':'Refresh'}</button></div><div className="audit-toolbar"><label className="audit-filter-field"><span>Date range</span><select className="audit-select" value={auditRangePreset} onChange={e=>applyAuditPreset(e.target.value)} aria-label="Audit date range"><option value="all">All activity</option><option value="today">Today</option><option value="7d">Last 7 days</option><option value="30d">Last 30 days</option><option value="this_month">This month</option><option value="previous_month">Previous month</option><option value="custom">Custom range</option></select></label>{auditRangePreset==='custom'&&<><label className="audit-filter-field"><span>From</span><input className="audit-date-input" type="date" value={auditFrom} onChange={e=>setAuditRange(e.target.value,auditTo,'custom')}/></label><label className="audit-filter-field"><span>To</span><input className="audit-date-input" type="date" value={auditTo} onChange={e=>setAuditRange(auditFrom,e.target.value,'custom')}/></label></>}</div>{auditState==='loading'&&<div className="panel standalone"><div className="empty">Loading audit activity…</div></div>}{auditState==='unavailable'&&<div className="panel standalone"><div className="notice">Audit activity is unavailable. No fallback data is shown.</div></div>}{auditState==='ready'&&<><div className="panel standalone audit-list">{auditRows.length?auditRows.map(a=><article className="event audit-row" key={a.id}><ActivityIcon size={17}/><div><span className='audit-category'>{auditCategory(a.action)}</span><b>{a.action}</b><small>{a.occurred_at?new Date(a.occurred_at).toLocaleString():''} · {a.actor}{a.lead_id?' · Lead '+a.lead_id:''}</small><pre className="jsonview">{JSON.stringify(a.details||{},null,2)}</pre></div></article>):<div className="empty">No audit events match this period.</div>}</div><div className="pagination"><button type="button" disabled={auditOffset===0} onClick={()=>setAuditOffset(Math.max(0,auditOffset-100))}>Previous</button><span>Page {Math.floor(auditOffset/100)+1}</span><button type="button" disabled={!auditHasMore} onClick={()=>setAuditOffset(auditOffset+100)}>Next</button></div></>}</section>}
    {page==='Settings'&&<><div className="heading"><div><h1>Settings</h1><p>Production privacy, access and data controls</p></div></div><div className="settings-grid"><div className="panel standalone"><h3><ShieldCheck size={17}/> Operator session</h3><p>Signed-in operator: <b>{operator||'local operator'}</b></p><p>Session expires after 8 hours of inactivity or 12 hours maximum. The session cookie is HttpOnly and never exposed to browser scripts.</p><button type="button" className="secondary" onClick={signOut}><LogOut size={14}/> Sign out</button></div><div className="panel standalone"><h3>Privacy display</h3><p>Phone numbers and observed message bodies can be masked without changing stored data.</p><button type="button" className="secondary" onClick={togglePrivacy}><ShieldCheck size={14}/> {privacyMode?'Reveal sensitive data':'Mask sensitive data'}</button></div><div className="panel standalone"><h3>Data controls</h3><p>Export the current source as CSV only after explicit operator action. Exports are audit-recorded.</p><button type="button" className="secondary" disabled={!online} onClick={exportCurrentSource}><Download size={14}/> Export {sourceFilter}</button><p className="muted">Retention: automatic deletion is disabled. Archived records remain reversible; permanent deletion is not exposed in v1.</p></div><div className="panel standalone"><h3>WhatsApp sources</h3><p>Verified EFPS source numbers:</p><div className="source-list">{SOURCE_NUMBERS.map(n=><span className="chip source" key={n}>{n}</span>)}</div><p>New WhatsApp activity is held in Contact Classification until an operator promotes it. The browser does not send WhatsApp messages automatically.</p></div></div></>}
    {(page==='Dashboard'||page==='Leads Inbox')&&selectedId&&workspaceState==='ready'&&<section className="panel live-detail">
      <div className="detailhead">
       <button type="button" className="back" onClick={backToInbox}><ChevronLeft size={18}/> Leads Inbox</button>
       <div className="identity"><span className="initial">{leadTitle(workspace.lead).split(/\s+/).map(x=>x[0]).join('').slice(0,3)}</span><div><h2>{leadTitle(workspace.lead)}</h2><span>{privacyMode?maskPhone(workspace.lead.normalized_phone)||'No phone stored':workspace.lead.normalized_phone||'No phone stored'} · {SOURCE_NUMBER}</span></div></div>
       <div className="headcontrols"><label className="inline-field">Lead Status <select disabled={!online} value={leadStatus||workspace.lead.lead_type||'New'} onChange={e=>{setLeadStatus(e.target.value);updateLead(workspace.lead.id,{leadType:e.target.value}).catch(()=>{})}}>{LEAD_STATUSES.map(s=><option key={s} value={s}>{LEAD_STATUS_LABELS[s]||s}</option>)}</select></label><label className="inline-field">Tenant Type <select disabled={!online} value={tenantType||'Not specified'} onChange={e=>{setTenantType(e.target.value);updateLead(workspace.lead.id,{tenantType:e.target.value}).catch(()=>{})}}>{TENANT_TYPES.map(s=><option key={s} value={s}>{s}</option>)}</select></label><button className="secondary danger" type="button" disabled={!online} onClick={toggleArchive}>{workspace.lead.status==='Archived'?<><RotateCcw size={14}/> Restore lead</>:<><Archive size={14}/> Archive lead</>}</button></div>
      </div>
      <div className="tabs" role="tablist" aria-label="Lead workspace sections">{TABS.map((t,index)=><button type="button" role="tab" id={'lead-tab-'+index} aria-controls="lead-tabpanel" aria-selected={tab===t} tabIndex={tab===t?0:-1} className={tab===t?'active':''} key={t} onClick={()=>navigateRoute({page:'Leads Inbox',leadId:selectedId,tab:t})} onKeyDown={event=>{if(!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return;event.preventDefault();const current=TABS.indexOf(t);const next=event.key==='Home'?0:event.key==='End'?TABS.length-1:(current+(event.key==='ArrowRight'?1:-1)+TABS.length)%TABS.length;navigateRoute({page:'Leads Inbox',leadId:selectedId,tab:TABS[next]});window.requestAnimationFrame(()=>document.getElementById('lead-tab-'+next)?.focus())}}>{t}</button>)}</div>
      <div className="tabbody" id="lead-tabpanel" role="tabpanel" aria-labelledby={'lead-tab-'+Math.max(0,TABS.indexOf(tab))} tabIndex={0}>
       {tab==='Overview'&&<><div className="two"><div className="inner"><h3>Stored requirements</h3><div className="requirements-grid">{requirementEntries(requirementsDraft||workspace.lead.requirements).length?requirementEntries(requirementsDraft||workspace.lead.requirements).map(([k,v])=><div className="requirement-item" key={k}><small>{k.replaceAll('_',' ')}</small><b>{String(v)}</b></div>):<div className="empty">No structured requirements recorded.</div>}</div><details className="raw-details"><summary>Source record</summary><pre className="jsonview">{JSON.stringify(workspace.lead.requirements||{},null,2)}</pre></details></div><div className="inner"><h3>Operator action</h3><p>{workspace.lead.operator_notes||'No operator note stored.'}</p>{privacyMode?<button className="secondary" type="button" onClick={togglePrivacy}><ShieldCheck size={14}/> Reveal phone to open WhatsApp</button>:<a className="primary inlinebutton" href={'https://wa.me/'+String(workspace.lead.normalized_phone||'').replace(/\D/g,'')} target="_blank" rel="noopener noreferrer">Open WhatsApp</a>}</div></div><div className="inner"><h3>Imported data</h3><p>Messages: <b>{workspace.messages.length}</b> · Activity: <b>{workspace.activity.length}</b> · Follow-ups: <b>{workspace.followups.length}</b></p><div className="notice">{workspace.messages.length?'Historical messages are available.':'No historical messages are imported yet. The production UI does not fabricate conversation history.'}</div></div></>}
       {tab==='Conversation'&&(workspace.messages.length?(()=>{const grouped=propertyRefsForMessages(workspace.messages);const renderMessage=m=><div className={'bubble '+(m.direction==='Outgoing'?'out':'')} key={m.id}><small>{m.direction} · {new Date(m.message_at).toLocaleString()} · {m.sender_name||m.source_number}</small><p>{privacyMode?maskMessage():(m.body||'['+m.message_type+']')}</p>{(m.media_urls||m.media_filenames)?.length>0&&<small>Media attached</small>}</div>;return <div className="conversation-groups">{grouped.refs.map(ref=><section className="conversation-property" key={ref.key}><header><div><span className="chip blue">Property reference</span><h3>{propertyLabel(ref.urls[0])}</h3><a href={ref.urls[0]} target="_blank" rel="noreferrer">{ref.urls[0]}</a></div><small>{ref.messageIds.size} explicitly linked message{ref.messageIds.size===1?'':'s'}</small></header><div className="conversation">{workspace.messages.filter(m=>ref.messageIds.has(m.id)).map(renderMessage)}</div></section>)}<section className="conversation-general"><header><div><span className="chip">General conversation</span><h3>Messages without an explicit property reference</h3></div><small>Not assigned to a property without stored evidence</small></header><div className="conversation">{grouped.general.map(renderMessage)}</div></section></div>})():<div className="empty">No imported conversation for this lead. Historical message import is separate from the lead records.</div>)}
       {tab==='Requirements'&&<div className="requirements-section"><div className="notice">Editable normalized requirement profile. These fields are the authoritative CRM profile used for inventory matching; legacy JSON is retained only as a compatibility mirror.</div><div className="requirements-table-wrap"><table className="requirements-table"><thead><tr><th>Requirement</th><th>Current value</th><th>Purpose</th></tr></thead><tbody>{REQUIREMENT_FIELDS.map(([key,label,type])=>{const value=requirementsDraft?.[key]??'';const options=key==='tenant_type'?TENANT_TYPES:key==='pets'?['Yes','No','Unknown']:key==='veg_nonveg'?['Veg','Non-Veg','No Preference','Unknown']:key==='furnishing'?['Fully Furnished','Semi Furnished','Unfurnished','Any','Unknown']:key==='parking'?['Required','Not Required','Any','Unknown']:[];const inventoryBhk=[...new Set((inventoryData?.rows||[]).map(x=>x.bhk).filter(Boolean))].sort();const inventoryLocations=[...new Set((inventoryData?.rows||[]).map(x=>x.locality).filter(Boolean))].sort();return <tr key={key}><td><b>{label}</b></td><td>{type==='textarea'?<textarea value={value} onChange={e=>setRequirementsDraft({...requirementsDraft,[key]:e.target.value})}/>:type==='select'?<select value={value} onChange={e=>setRequirementsDraft({...requirementsDraft,[key]:e.target.value})}><option value="">Not specified</option>{options.map(o=><option key={o} value={o}>{o}</option>)}</select>:<><input type={type} list={key==='bhk'?'crm-bhk-options':key==='preferred_locations'?'crm-locality-options':undefined} value={value} onChange={e=>setRequirementsDraft({...requirementsDraft,[key]:e.target.value})}/>{key==='bhk'&&<datalist id="crm-bhk-options">{inventoryBhk.map(v=><option key={v} value={v}/>)}</datalist>}{key==='preferred_locations'&&<datalist id="crm-locality-options">{inventoryLocations.map(v=><option key={v} value={v}/>)}</datalist>}</>}</td><td className="muted">{['bhk','budget','preferred_locations','move_in_date','pets','furnishing','parking','property_type','tenant_type'].includes(key)?'Inventory / qualification signal':'Conversation context'}</td></tr>})}</tbody></table></div><div className="requirements-actions"><button type="button" className="primary" disabled={!online||requirementsState==='saving'} onClick={saveRequirements}>{requirementsState==='saving'?'Saving…':requirementsState==='saved'?'Saved':'Save requirements'}</button>{requirementsState==='error'&&<span className="error">Requirement update failed.</span>}</div><div className="inner"><h3>Requirement evidence</h3>{workspace.requirement_evidence?.length?workspace.requirement_evidence.map(e=><div className="event" key={e.id}><CheckCircle2 size={16}/><div><b>{e.field_name}: {JSON.stringify(e.value?.value??e.value)}</b><small>Message #{e.source_message_id||'operator'} · {e.actor} · {formatLeadDate(e.recorded_at)}</small></div></div>):<div className="empty">No field-level evidence has been accepted yet.</div>}</div></div>}
       {tab==='Property Matches'&&<>{matchState==='loading'&&<div className="empty">Matching against current Supabase inventory…</div>}{matchState==='insufficient'&&<div className="empty">No structured BHK, budget or locality is stored for this lead, so no inventory match is inferred.</div>}{matchState==='unavailable'&&<div className="empty">Live inventory matching is unavailable.</div>}{matchState==='ready'&&(filteredMatches.length?<div className="properties">{filteredMatches.map(p=><article className="property" key={p.listing_id}><PropertyMatchMedia property={p}/><div className="rowtop"><b>{p.bhk} · {p.locality}</b><span className="chip green">{p.listing_state}</span></div><p className="price">{money(p.monthly_rent)} <small>/ month</small></p><p>{p.furnishing||'Furnishing not recorded'} · Pets: {p.pet_friendly||'Not recorded'}</p><small>{p.listing_id} · {p.society_name||'Society not recorded'}</small></article>)}</div>:<div className="empty">No live inventory matches were returned.</div>)}</>}
       {tab==='AI & Drafts'&&<div className="ai-section">
        <div className="notice">Production AI reviews the complete chronological conversation, requirement profile, evidence, prior AI runs and timing. It can propose requirement changes and draft a WhatsApp reply; it never sends a message or applies a requirement change without operator acceptance.</div>
        <div className="ai-toolbar"><div><h3><BrainCircuit size={18}/> Lead AI workspace</h3><p className="muted">Conversation: {workspace.messages.length} messages · AI runs: {workspace.ai_runs?.length||0} · Draft versions: {workspace.drafts?.length||0}</p></div><button type="button" className="primary" disabled={aiState==='running'||!online} onClick={runAi}>{aiState==='running'?'Analyzing full history…':'Run AI analysis'}</button></div>
        {aiState==='unavailable'&&<div className="notice">AI analysis failed. {aiError||'No fallback or fabricated result is shown.'}</div>}
        {ai?.proposal&&<div className="ai-grid">
         <div className="inner"><h3>AI evidence & timeline</h3><p>{ai.proposal.summary}</p><pre className="jsonview">{JSON.stringify(ai.proposal.timeline,null,2)}</pre><h4>Requirement changes proposed</h4>{ai.proposal.requirement_updates?.length?ai.proposal.requirement_updates.map((u,i)=><div className="ai-evidence" key={i}><b>{u.field}: {String(u.value)}</b><small>{u.evidence||'Evidence linked to conversation.'} · messages: {(u.source_message_ids||[]).join(', ')}</small></div>):<div className="empty">No requirement changes proposed.</div>}{ai.run?.status==='proposed'&&ai.proposal.requirement_updates?.length>0&&<div className="requirements-actions"><button type="button" className="primary" onClick={()=>acceptAiRequirements(ai.run.id)}>Accept requirement changes</button><button type="button" className="secondary" onClick={()=>rejectAiRequirements(ai.run.id)}>Reject</button></div>}<h4>Suggested lead status</h4><div className="chip">{ai.proposal.lead_status_suggestion?.status||'No change suggested'}</div><p>{ai.proposal.lead_status_suggestion?.reason||''}</p></div>

        </div>}
        <div className="inner"><h3>Draft workspace</h3>{workspace.drafts?.length?<><div className="draft-list">{workspace.drafts.map(d=><button type="button" className={'draft-row '+(selectedDraftId===d.id?'selected':'')} key={d.id} aria-label={'Open draft version '+d.version} disabled={!d.body?.trim()} onClick={()=>{setSelectedDraftId(d.id);setDraftBody(String(d.body||''));}}><div><b>v{d.version} · {d.status}</b><small>{formatLeadDate(d.created_at)}</small><small>AI: {d.model_name||'unknown'} · {d.ai_provider||'unknown'}{d.fallback_from?` · fallback from ${d.fallback_from}`:''}</small>{d.stale&&<small className="error">Stale — new activity</small>}</div><span>Open / edit</span></button>)}</div><div className="draft-detail"><div className="draft-meta"><div><b>{selectedDraftId?'Selected draft':'Latest draft'}</b><small>{workspace.drafts.find(d=>d.id===selectedDraftId)?.model_name||workspace.drafts[0]?.model_name||'unknown'} · {workspace.drafts.find(d=>d.id===selectedDraftId)?.ai_provider||workspace.drafts[0]?.ai_provider||'unknown'}{workspace.drafts.find(d=>d.id===selectedDraftId)?.fallback_from?` · fallback from ${workspace.drafts.find(d=>d.id===selectedDraftId)?.fallback_from}`:''}</small><small>Evidence: {(workspace.drafts.find(d=>d.id===selectedDraftId)?.evidence_message_ids||[]).join(', ')||'none attached'}</small><small>Input tokens: {tokenCount(workspace.drafts.find(d=>d.id===selectedDraftId)?.input_tokens)}</small><small>Output tokens: {tokenCount(workspace.drafts.find(d=>d.id===selectedDraftId)?.output_tokens)}</small><small>Estimated cost: {estimatedCost(workspace.drafts.find(d=>d.id===selectedDraftId)?.estimated_cost_usd)}</small>{workspace.drafts.find(d=>d.id===selectedDraftId)?.stale&&<span className="chip red">Stale — new activity since generation</span>}</div></div><textarea className="draft-editor" value={draftBody} onChange={e=>{setDraftBody(e.target.value);setDraftCheck(null)}} placeholder="Select a saved draft to view or edit it."/><div className="requirements-actions"><button type="button" className="primary" disabled={!draftBody.trim()||draftState==='saving'} onClick={saveDraftVersion}>{draftState==='saving'?'Saving…':draftState==='saved'?'Saved':'Save draft edit'}</button>{selectedDraftId&&<><button type="button" className="secondary" onClick={openDraftInWhatsApp}>Pre-send check & open WhatsApp</button><button type="button" className="secondary" onClick={copyDraft}>Copy</button>{workspace.drafts.find(d=>d.id===selectedDraftId)?.status==='opened'&&<button type="button" className="secondary" onClick={()=>markDraft(selectedDraftId,'confirmed_sent')}>Mark sent</button>}</>}{draftState==='error'&&<span className="error">Draft save failed.</span>}</div>{draftCheck&&!draftCheck.loading&&<div className="draft-check"><b>{draftCheck.ready?'Pre-send check passed':'Pre-send check blocked'}</b>{draftCheck.blocking?.map(x=><div className="error" key={x.code}>{x.message}</div>)}{draftCheck.warnings?.map(x=><div className="muted" key={x.code}>{x.message}</div>)}</div>}</div></>:<div className="empty">No drafts saved.</div>}</div>
        <div className="inner"><h3>Saved AI run history</h3>{workspace.ai_runs?.length?workspace.ai_runs.map(r=><div className="event" key={r.id}><BrainCircuit size={16}/><div><b>{r.model_name} · {r.provider||'unknown'} · {r.status}</b><small>{formatLeadDate(r.created_at)}{r.fallback_from?' · fallback from '+r.fallback_from:''}{r.fallback_reason?' · '+r.fallback_reason:''}{r.decided_at?' · decided '+formatLeadDate(r.decided_at):''}</small><small>Input tokens: {tokenCount(r.input_tokens)} · Output tokens: {tokenCount(r.output_tokens)} · Total: {tokenCount(r.total_tokens)}</small></div></div>):<div className="empty">No AI runs yet.</div>}</div>
       </div>}       {tab==='Activity & History'&&<><div className="inner"><h3>Lead audit history</h3><p className="muted">Only events linked to this lead are shown here. The same underlying audit records power the global Audit Activity page.</p><div className="audit-toolbar"><label className="audit-filter-field"><span>Date range</span><select className="audit-select" value={auditRangePreset} onChange={e=>applyAuditPreset(e.target.value)} aria-label="Lead audit date range"><option value="all">All activity</option><option value="today">Today</option><option value="7d">Last 7 days</option><option value="30d">Last 30 days</option><option value="this_month">This month</option><option value="previous_month">Previous month</option><option value="custom">Custom range</option></select></label>{auditRangePreset==='custom'&&<><label className="audit-filter-field"><span>From</span><input className="audit-date-input" type="date" value={auditFrom} onChange={e=>setAuditRange(e.target.value,auditTo,'custom')}/></label><label className="audit-filter-field"><span>To</span><input className="audit-date-input" type="date" value={auditTo} onChange={e=>setAuditRange(auditFrom,e.target.value,'custom')}/></label></>}</div>{leadAuditState==='loading'&&<div className="empty">Loading lead audit history…</div>}{leadAuditState==='unavailable'&&<div className="notice">Lead audit history is unavailable. No fallback events are shown.</div>}{leadAuditState==='ready'&&(leadAuditRows.length?leadAuditRows.map(a=><div className="event" key={a.id}><CheckCircle2 size={17}/><div><span className='audit-category'>{auditCategory(a.action)}</span><b>{a.action}</b><small>{a.occurred_at?new Date(a.occurred_at).toLocaleString():''} · {a.actor}</small><pre className="jsonview">{JSON.stringify(a.details||{},null,2)}</pre></div></div>):<div className="empty">No audit events match this period for this lead.</div>)}{leadAuditState==='ready'&&<div className="pagination"><button type="button" disabled={leadAuditOffset===0} onClick={()=>setLeadAuditOffset(Math.max(0,leadAuditOffset-100))}>Previous</button><span>Page {Math.floor(leadAuditOffset/100)+1}</span><button type="button" disabled={!leadAuditHasMore} onClick={()=>setLeadAuditOffset(leadAuditOffset+100)}>Next</button></div>}</div><div className="inner"><h3>Schedule follow-up</h3><div className="requirements-actions"><label className="inline-field">Due <input type="datetime-local" value={followupDueAt} onChange={e=>setFollowupDueAt(e.target.value)} aria-label="Follow-up due"/></label><input value={followupNote} onChange={e=>setFollowupNote(e.target.value)} placeholder="Follow-up note (optional)" aria-label="Follow-up note"/><button type="button" className="primary" disabled={!online||followupState==='saving'||!followupDueAt} onClick={()=>{if(new Date(followupDueAt).getTime()<=Date.now()){setActionError('Follow-up due time must be in the future');return}createFollowup()}}>{followupState==='saving'?'Scheduling…':followupState==='saved'?'Scheduled':'Schedule follow-up'}</button></div></div>{workspace.followups?.length?<div className="inner"><h3>Follow-ups</h3>{workspace.followups.map(f=><div className="event" key={f.id}><CheckCircle2 size={17}/><div><b>{f.completed_at?'Completed':'Scheduled'}</b><small>{f.due_at?new Date(f.due_at).toLocaleString():''} · {f.note||'No note recorded'}</small>{!f.completed_at&&<button type="button" className="secondary" disabled={!online} onClick={()=>completeFollowup(f.id)}>Complete</button>}</div></div>)}</div>:<div className="notice">No follow-up records are stored for this lead.</div>}{workspace.activity.length?workspace.activity.map(a=><div className="event" key={a.id}><CheckCircle2 size={17}/><div><b>{a.action}</b><small>{a.occurred_at?new Date(a.occurred_at).toLocaleString():''} · {a.actor}</small></div></div>):<div className="empty">No activity recorded for this lead.</div>}</>}
      </div>
     </section>}
    {(page==='Dashboard'||page==='Leads Inbox')&&!selectedId&&<section>
      <div className="heading"><div><h1>{page==='Dashboard'?'CRM Dashboard':'Leads Inbox'}</h1><p>Live production records across the verified WhatsApp source numbers.</p></div><div className="headcontrols"><label className="inline-field">Lead source <select value={sourceFilter} onChange={e=>{setSourceFilter(e.target.value);setOffset(0)}}>{SOURCE_NUMBERS.map(n=><option key={n} value={n}>{n}</option>)}</select></label><button type="button" className="primary" onClick={refresh}><RefreshCw size={14}/> Refresh</button></div></div>
      {error&&<div className="notice">Live CRM unavailable. {error}</div>}
      {page==='Dashboard'&&realtimeState==='error'&&<div className="notice">Realtime connection error: {realtimeError||'channel subscription failed'}. Live webhook ingestion is independent and continues server-side.</div>}
      {page==='Dashboard'&&<><div className="stats"><button type="button" className="stat stat-link" onClick={()=>navigateRoute({page:'Leads Inbox'})}><small>CRM leads</small><b>{dashboardStats?.qualifiedClassificationCount??0}</b><span>Actually qualified · Open Leads Inbox</span></button><button type="button" className="stat stat-link" onClick={()=>{navigateRoute({page:'Contact Classification'});setClassificationFilter('not_pushed')}}><small>Waiting for classification</small><b>{dashboardStats?.notPushedClassificationCount??0}</b><span>Contacts waiting for an operator decision</span></button><button type="button" className="stat stat-link" onClick={()=>navigateRoute({page:'Inventory'})}><small>Total available inventory</small><b>{dashboardStats?.availableInventoryCount??0}</b><span>Available properties · Open Inventory</span></button><button type="button" className="stat stat-link" onClick={()=>document.getElementById('today-followups')?.scrollIntoView({behavior:'smooth',block:'start'})}><small>Follow-ups</small><b>{dashboardStats?.followupTodayCount??0}</b><span>Today · {dashboardStats?.overdueFollowupCount??0} overdue · View actions below</span></button></div><div className="panel daily-actions" id="today-followups"><div className="daily-actions-head"><div><h3>Today's follow-ups</h3><p>Only the next actions that need your attention.</p></div>{dashboardStats?.webhookErrorCount>0&&<span className="chip red">{dashboardStats.webhookErrorCount} webhook errors</span>}</div>{(dashboardStats?.nextFollowups||[]).length?dashboardStats.nextFollowups.map(f=><button type="button" className="followup-row" key={f.id} onClick={()=>openLead(f.lead_id)}><span className="followup-time">{new Date(f.due_at).toLocaleString([], {day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit'})}</span><span><b>{f.display_name||f.normalized_phone||'Lead'}</b><small>{f.note||'Follow-up due'}</small></span><span className="chip">Open</span></button>):<div className="empty">No open follow-ups are scheduled. New activity will appear here when a follow-up is created.</div>}</div></>}
      {page==='Leads Inbox'&&<div className="status-summary-grid" aria-label="Lead status counts">
       {LEAD_STATUSES.map(status=>{const count=Number(dashboardStats?.leadStatusCounts?.find(x=>x.status===status)?.count||0);const active=leadStatusFilter===status;return <button key={status} type="button" className={'status-summary-card '+(active?'active':'')} onClick={()=>{navigateRoute({page:'Leads Inbox'});setLeadStatusFilter(status);setOffset(0)}}><span>{LEAD_STATUS_LABELS[status]||status}</span><b>{count}</b><small>Open {LEAD_STATUS_LABELS[status]||status}</small></button>})}
      </div>}
      <div className="panel leadlist-production">
       <div className="production-toolbar"><label className="search"><Search size={16}/><input value={query} onChange={e=>{setQuery(e.target.value);setOffset(0)}} placeholder="Search name or phone" aria-label="Search live leads"/></label><label>Lead status <select value={leadStatusFilter} onChange={e=>{setLeadStatusFilter(e.target.value);setOffset(0)}}><option value="">All statuses</option>{LEAD_STATUSES.map(s=><option key={s} value={s}>{LEAD_STATUS_LABELS[s]||s}</option>)}</select></label><label>Lead source <select value={sourceFilter} onChange={e=>{setSourceFilter(e.target.value);setOffset(0)}}>{SOURCE_NUMBERS.map(n=><option key={n} value={n}>{n}</option>)}</select></label><label>Sort leads <select value={leadSort} onChange={e=>{setLeadSort(e.target.value);setOffset(0)}} aria-label="Sort leads">{LEAD_SORT_OPTIONS.map(([value,label])=><option key={value} value={value}>{label}</option>)}</select></label><span>{total} leads</span></div>
       {loading?<div className="empty">Loading live leads…</div>:visibleLeads.length?visibleLeads.map(l=><LeadCard key={l.id} lead={l} privacyMode={privacyMode} onClick={()=>openLead(l.id)}/>):<div className="empty">No live leads match this search.</div>}
      </div>
      <div className="pagination"><button type="button" disabled={offset===0} onClick={()=>setOffset(Math.max(0,offset-100))}>Previous</button><span>{total?offset+1:0}–{Math.min(offset+leads.length,total)} of {total}</span><button type="button" disabled={offset+100>=total} onClick={()=>setOffset(offset+100)}>Next</button></div>
    </section>}
    {(page==='Dashboard'||page==='Leads Inbox')&&selectedId&&workspaceState==='loading'&&<div className="panel standalone"><div className="backlink"><button type="button" className="back" onClick={backToInbox}><ChevronLeft size={18}/> Leads Inbox</button></div><div className="empty">Loading the live lead workspace…</div></div>}
    {(page==='Dashboard'||page==='Leads Inbox')&&selectedId&&workspaceState==='unavailable'&&<div className="panel standalone"><div className="backlink"><button type="button" className="back" onClick={backToInbox}><ChevronLeft size={18}/> Leads Inbox</button></div><div className="notice">The live lead workspace could not be loaded. No fallback data is used.</div><button type="button" className="primary" onClick={refresh}>Retry</button></div>}
   </div>
  </main>
 </div>
}

createRoot(document.getElementById('root')).render(<AppErrorBoundary><App/></AppErrorBoundary>);
