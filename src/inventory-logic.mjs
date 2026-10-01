export const INVENTORY_SORT_OPTIONS = [
  ['latest','Latest'],
  ['oldest','Oldest'],
  ['rent_asc','Rent: low to high'],
  ['rent_desc','Rent: high to low'],
  ['bhk_asc','BHK: low to high'],
  ['bhk_desc','BHK: high to low'],
  ['locality_asc','Locality: A–Z'],
];

const INVENTORY_SORT_VALUES = new Set(INVENTORY_SORT_OPTIONS.map(([value]) => value));

export function normalizeInventorySort(value='latest'){
  const sort=String(value||'latest');
  return INVENTORY_SORT_VALUES.has(sort)?sort:'latest';
}

export function inventorySortLabel(value='latest'){
  return INVENTORY_SORT_OPTIONS.find(([option])=>option===normalizeInventorySort(value))?.[1] || 'Latest';
}

export function sortInventoryRows(rows,sort='latest'){
  const requested=normalizeInventorySort(sort);
  const parseDate=value=>{if(!value)return null;const t=Date.parse(String(value));return Number.isFinite(t)?t:null};
  const bhkNumber=value=>{const match=String(value||'').match(/\d+(?:\.\d+)?/);return match?Number(match[0]):Number.POSITIVE_INFINITY};
  return [...(Array.isArray(rows)?rows:[])].sort((a,b)=>{
   if(requested==='rent_asc'||requested==='rent_desc'){
    const av=Number(a.monthly_rent),bv=Number(b.monthly_rent);
    if(Number.isFinite(av)&&Number.isFinite(bv)&&av!==bv)return requested==='rent_asc'?av-bv:bv-av;
    if(Number.isFinite(av)!==Number.isFinite(bv))return Number.isFinite(av)?-1:1;
   }
   if(requested==='bhk_asc'||requested==='bhk_desc'){
    const av=bhkNumber(a.bhk),bv=bhkNumber(b.bhk);
    if(av!==bv)return requested==='bhk_asc'?av-bv:bv-av;
   }
   if(requested==='locality_asc'){
    const cmp=String(a.locality||'').localeCompare(String(b.locality||''));
    if(cmp!==0)return cmp;
   }
   const ad=parseDate(a.onboarded_on||a.source_record?.onboarded_on||a.last_synced_at);
   const bd=parseDate(b.onboarded_on||b.source_record?.onboarded_on||b.last_synced_at);
   if(requested==='latest'||requested==='oldest'){
    if(ad===null&&bd!==null)return 1;
    if(ad!==null&&bd===null)return -1;
    if(ad!==null&&bd!==null&&ad!==bd)return requested==='latest'?bd-ad:ad-bd;
   }
   return String(a.listing_id||'').localeCompare(String(b.listing_id||''));
  });
}

export const INVENTORY_PAGE_SIZE=24;

function inventoryText(value,fallback=''){
 return value!==null&&value!==undefined&&String(value).trim()?String(value).trim():fallback;
}

export function filterInventoryRows(rows,{status='All',bhk='All',locality='All',withPhotos=null,search=''}={},hasPhotos=row=>{
 const raw=row?.photos??row?.cloudinary_image_urls??[];
 return Array.isArray(raw)?raw.length>0:Boolean(String(raw||'').trim());
}){
 const query=String(search||'').trim().toLocaleLowerCase();
 return (Array.isArray(rows)?rows:[]).filter(row=>
  (status==='All'||inventoryText(row.listing_state,'Unknown')===status)&&
  (bhk==='All'||String(row.bhk??'')===String(bhk))&&
  (locality==='All'||inventoryText(row.locality,'Unspecified')===locality)&&
  (withPhotos===null||Boolean(hasPhotos(row))===withPhotos)&&
  (!query||[row.listing_id,row.locality,row.society_name,row.bhk,row.source_record?.catalog_title].join(' ').toLocaleLowerCase().includes(query))
 );
}

export function inventoryFacets(rows){
 const values=Array.isArray(rows)?rows:[];
 const bhkNumber=value=>{const match=String(value||'').match(/\d+(?:\.\d+)?/);return match?Number(match[0]):Number.POSITIVE_INFINITY};
 return{
  statuses:[...new Set(values.map(row=>inventoryText(row.listing_state,'Unknown')))].sort(),
  bhks:[...new Set(values.map(row=>row.bhk).filter(Boolean).map(String))].sort((a,b)=>bhkNumber(a)-bhkNumber(b)||a.localeCompare(b)),
  localities:[...new Set(values.map(row=>inventoryText(row.locality,'Unspecified')))].sort((a,b)=>a.localeCompare(b))
 };
}

export function summarizeInventoryRows(rows,hasPhotos=row=>{
 const raw=row?.photos??row?.cloudinary_image_urls??[];
 return Array.isArray(raw)?raw.length>0:Boolean(String(raw||'').trim());
}){
 const values=Array.isArray(rows)?rows:[];
 const statuses=[...new Set(values.map(row=>inventoryText(row.listing_state,'Unknown')))];
 return{
  total:values.length,
  available:values.filter(row=>row.listing_state==='Available').length,
  rented:values.filter(row=>row.listing_state==='Rented Out').length,
  withPhotos:values.filter(hasPhotos).length,
  statusCounts:Object.fromEntries(statuses.map(status=>[status,values.filter(row=>inventoryText(row.listing_state,'Unknown')===status).length]))
 };
}

export function buildInventoryPage(rows,{limit=INVENTORY_PAGE_SIZE,offset=0,sort='latest',status='All',bhk='All',locality='All',withPhotos=null,search=''}={},hasPhotos){
 if(!Number.isInteger(limit)||limit<1||limit>100||!Number.isInteger(offset)||offset<0)throw Error('Invalid inventory pagination');
 const values=Array.isArray(rows)?rows:[];
 const photoCheck=hasPhotos||((row)=>{
  const raw=row?.photos??row?.cloudinary_image_urls??[];
  return Array.isArray(raw)?raw.length>0:Boolean(String(raw||'').trim());
 });
 const filtered=sortInventoryRows(filterInventoryRows(values,{status,bhk,locality,withPhotos,search},photoCheck),sort);
 const pageRows=filtered.slice(offset,offset+limit);
 return{
  rows:pageRows,
  total:filtered.length,
  offset,
  limit,
  hasMore:offset+pageRows.length<filtered.length,
  summary:summarizeInventoryRows(values,photoCheck),
  facets:inventoryFacets(values)
 };
}
