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
