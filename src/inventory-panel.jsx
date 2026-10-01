import React,{useState} from 'react';
import {Search,MapPin,Images,RefreshCw,ChevronLeft,ChevronRight,SlidersHorizontal,Clock3,Database,ExternalLink,CheckCircle2,ImageOff} from 'lucide-react';
import {imageUrls} from './crm-logic.mjs';
import {INVENTORY_PAGE_SIZE,INVENTORY_SORT_OPTIONS,normalizeInventorySort,inventorySortLabel} from './inventory-logic.mjs';

const money=n=>n===null||n===undefined||n===''?'Price on request':'₹'+Number(n).toLocaleString('en-IN');
const text=(v,fallback='Not specified')=>v!==null&&v!==undefined&&String(v).trim()?String(v).trim():fallback;

function PropertyMedia({property}){
 const urls=imageUrls(property);
 const [index,setIndex]=useState(0);
 const [broken,setBroken]=useState([]);
 const usable=urls.filter(url=>!broken.includes(url));
 const current=usable.length?usable[index%usable.length]:null;
 const displayNumber=usable.length?Math.min((index%usable.length)+1,usable.length):0;
 const markBroken=()=>{if(current)setBroken(items=>items.includes(current)?items:[...items,current]);};
 const retry=()=>{if(current)setBroken(items=>items.filter(url=>url!==current));else setBroken([])};
 return <div className="inventory-media">
  {current?<img
    key={current}
    loading="lazy"
    decoding="async"
    referrerPolicy="no-referrer"
    src={current}
    alt={`${property.bhk||'Property'} in ${property.locality||'Bengaluru'} — photo ${displayNumber}`}
    onLoad={event=>{event.currentTarget.dataset.loaded='true'}}
    onError={markBroken}
  />:<div className="inventory-no-photo">
    {urls.length?<><ImageOff size={32}/><strong>Photo preview unavailable</strong><small>Source media URL is stored, but the image could not be loaded.</small><button type="button" className="inventory-media-retry" onClick={retry}>Retry image</button></>:<><Images size={32}/><strong>Photos not available</strong><small>No source photo URL is stored for this property.</small></>}
  </div>}
  <span className="inventory-media-count">{urls.length?(usable.length?(`${displayNumber} / ${usable.length} photos`):`${urls.length} source URLs`):'No photos'}</span>
  {usable.length>1&&<div className="inventory-media-nav">
    <button type="button" aria-label="Previous property photo" onClick={()=>setIndex(i=>(i+usable.length-1)%usable.length)}><ChevronLeft size={19}/></button>
    <button type="button" aria-label="Next property photo" onClick={()=>setIndex(i=>(i+1)%usable.length)}><ChevronRight size={19}/></button>
  </div>}
 </div>
}

export default function InventoryPanel({data,state,refresh,query,setQuery,sort,setSort,filters,setFilters,offset,setOffset}){
 const [selected,setSelected]=useState(null);
 const rows=data?.rows||[];
 const {status='All',bhk='All',locality='All',withPhotos=null}=filters||{};
 const live=state==='live';
 const facets=data?.facets||{statuses:[],bhks:[],localities:[]};
 const summary=data?.summary;
 const statuses=facets.statuses||[];
 const localities=facets.localities||[];
 const bhks=facets.bhks||[];
 const total=Number(data?.total)||0;
 const pageLimit=Number(data?.limit)||INVENTORY_PAGE_SIZE;
 const available=Number(summary?.available)||0;
 const rented=Number(summary?.rented)||0;
 const withImages=Number(summary?.withPhotos)||0;
 const chosen=rows.find(r=>r.listing_id===selected);
 const resetFilters=()=>{setFilters({status:'All',bhk:'All',locality:'All',withPhotos:null});setQuery('',true);setOffset(0)};
 const applyKpi=kind=>{setFilters({status:kind==='available'?'Available':kind==='rented'?'Rented Out':'All',bhk:'All',locality:'All',withPhotos:kind==='photos'?true:null});setQuery('',true);setOffset(0)};
 const setFilter=(key,value)=>{setFilters(current=>({...current,[key]:value}));setOffset(0)};
 const activeFilters=status!=='All'||bhk!=='All'||locality!=='All'||withPhotos!==null||Boolean(query);
 const start=total?offset+1:0;
 const end=Math.min(offset+rows.length,total);
 return <section className="inventory-screen">
  <div className="inventory-heading">
   <div><span className="inventory-eyebrow"><Database size={14}/> HOUSING_LISTINGS · SUPABASE MIRROR</span><h1>Property inventory</h1><p>Every property, its availability and its source media in one workspace.</p></div>
   <button type="button" className="inventory-refresh" onClick={refresh} disabled={state==='loading'} aria-busy={state==='loading'}><RefreshCw size={16}/> {state==='loading'?'Refreshing…':'Refresh'}</button>
  </div>
  {!live&&<div className="inventory-alert" role="status">{state==='loading'?'Loading the inventory from Supabase…':'Live inventory unavailable. No synthetic properties are presented as company inventory.'}</div>}
  {live&&<>
   <div className="inventory-kpis" aria-label="Inventory summary">
     <button type="button" className={'inventory-kpi '+(!activeFilters?'is-active':'')} aria-pressed={!activeFilters} onClick={()=>applyKpi('total')}><small>Total properties</small><strong>{Number(summary?.total)||0}</strong><span>View all inventory</span></button>
    <button type="button" className={'inventory-kpi '+(status==='Available'?'is-active':'')} aria-pressed={status==='Available'} onClick={()=>applyKpi('available')}><small>Available</small><strong>{available}</strong><span>Ready for enquiry matching</span></button>
    <button type="button" className={'inventory-kpi '+(status==='Rented Out'?'is-active':'')} aria-pressed={status==='Rented Out'} onClick={()=>applyKpi('rented')}><small>Rented out</small><strong>{rented}</strong><span>Not offered for matching</span></button>
     <button type="button" className={'inventory-kpi '+(withPhotos===true?'is-active':'')} aria-pressed={withPhotos===true} onClick={()=>applyKpi('photos')}><small>With photos</small><strong>{withImages}<em> / {Number(summary?.total)||0}</em></strong><span>{summary?.total?Math.round(withImages/summary.total*100):0}% source media coverage</span></button>
   </div>
   <div className="inventory-reconcile">
     <div><strong>Inventory reconciliation</strong><span>{Number(summary?.total)||0} total = {statuses.map(s=>`${summary?.statusCounts?.[s]??0} ${s.toLowerCase()}`).join(' + ')}</span></div>
    <div><strong>Latest completed Sheet sync</strong><span>{data.latestSync?new Date(data.latestSync.created_at).toLocaleString('en-IN',{dateStyle:'medium',timeStyle:'short'}):'Not yet recorded — this is a point-in-time mirror'}</span></div>
     <div><strong>Geographic coverage</strong><span>{localities.length} localities · Bengaluru. No location is inferred where the Sheet is blank.</span></div>
   </div>
   <div className="inventory-controls">
    <label className="inventory-search"><Search size={18}/><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search ID, locality, society or title…" aria-label="Search inventory"/></label>
     <label><SlidersHorizontal size={15}/> Status<select value={status} onChange={e=>setFilter('status',e.target.value)}><option>All</option>{statuses.map(s=><option key={s}>{s}</option>)}</select></label>
     <label>BHK<select value={bhk} onChange={e=>setFilter('bhk',e.target.value)}><option>All</option>{bhks.map(v=><option key={v}>{v}</option>)}</select></label>
     <label>Locality<select value={locality} onChange={e=>setFilter('locality',e.target.value)}><option>All</option>{localities.map(v=><option key={v}>{v}</option>)}</select></label>
    <label>Sort inventory<select value={normalizeInventorySort(sort)} onChange={e=>setSort(normalizeInventorySort(e.target.value))}>{INVENTORY_SORT_OPTIONS.map(([value,label])=><option key={value} value={value}>{label}</option>)}</select></label>
   </div>
    {activeFilters&&<div className="inventory-filter-summary"><span>Filtered view · {total} properties</span><button type="button" onClick={resetFilters}>Clear filters</button></div>}
    <div className="inventory-results"><strong>{total} properties</strong><span>Sorted by {inventorySortLabel(sort)}</span></div>
    <div className="inventory-card-grid">{rows.map(p=><article className="inventory-card" key={p.listing_id}><PropertyMedia property={p}/><div className="inventory-card-body">
    <div className="inventory-card-top"><span className={'inventory-status '+(p.listing_state==='Available'?'is-available':'is-rented')}>{text(p.listing_state)}</span><small>{p.listing_id}</small></div>
    <h2>{text(p.bhk,'Property')} · {text(p.locality,'Location unspecified')}</h2>
    <p className="inventory-society"><MapPin size={15}/>{text(p.society_name,p.locality||'Location not provided')}</p>
    <div className="inventory-card-price">{money(p.monthly_rent)}<small> / month</small></div>
    <div className="inventory-card-tags"><span>{text(p.furnishing,'Furnishing unknown')}</span><span>{text(p.source_record?.internal_property_type||p.source_record?.property_subtype,'Property')}</span></div>
    <div className="inventory-card-bottom"><span><Clock3 size={13}/> {p.onboarded_on||p.source_record?.onboarded_on||'Import snapshot'}</span><button type="button" onClick={()=>setSelected(p.listing_id)}>View property <ExternalLink size={14}/></button></div>
   </div></article>)}</div>
    {!rows.length&&<div className="inventory-empty"><CheckCircle2 size={18}/> No properties match the selected filters.</div>}
    <nav className="pagination inventory-pagination" aria-label="Inventory pagination"><button type="button" aria-label="Previous inventory page" disabled={offset===0} onClick={()=>setOffset(Math.max(0,offset-pageLimit))}>Previous</button><span aria-live="polite">Page {Math.floor(offset/pageLimit)+1} · {start}–{end} of {total}</span><button type="button" aria-label="Next inventory page" disabled={!data?.hasMore} onClick={()=>setOffset(offset+pageLimit)}>Next</button></nav>
   {chosen&&<div className="inventory-modal-backdrop" onClick={()=>setSelected(null)}><div className="inventory-modal" role="dialog" aria-modal="true" aria-label="Property details" onClick={e=>e.stopPropagation()}>
    <button type="button" className="inventory-close" onClick={()=>setSelected(null)}>Close ×</button><PropertyMedia property={chosen}/>
    <div className="inventory-modal-body"><span className="inventory-eyebrow">{chosen.listing_id} · {chosen.listing_state}</span><h2>{text(chosen.bhk)} · {text(chosen.locality)}</h2><h3>{money(chosen.monthly_rent)} / month</h3>
     <div className="inventory-detail-grid">{[['Society',chosen.society_name],['Furnishing',chosen.furnishing],['City / state',chosen.source_record?.city||chosen.source_record?.state],['Maintenance',chosen.source_record?.maintenance],['Deposit',chosen.source_record?.security_deposit],['Bathrooms',chosen.source_record?.bathrooms],['Pet friendly',chosen.pet_friendly],['Parking',chosen.source_record?.covered_parking],['Onboarded',chosen.onboarded_on||chosen.source_record?.onboarded_on],['Source updated',chosen.last_synced_at?new Date(chosen.last_synced_at).toLocaleString('en-IN'):null]].map(([k,v])=><div key={k}><small>{k}</small><strong>{text(v)}</strong></div>)}</div>
     {chosen.source_record?.property_highlights&&<p>{chosen.source_record.property_highlights}</p>}{chosen.source_record?.google_maps_url?.startsWith('https://')&&<a href={chosen.source_record.google_maps_url} target="_blank" rel="noreferrer">View source map ↗</a>}
    </div>
   </div></div>}
  </>}
 </section>
}
