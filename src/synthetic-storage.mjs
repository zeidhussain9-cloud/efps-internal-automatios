// Synthetic-only browser storage. Never enable this adapter for real customer data.
export const STORAGE_KEY='easyfind-crm-synthetic-v1';
export function readSynthetic(storage){try{const raw=storage.getItem(STORAGE_KEY);if(!raw)return null;const data=JSON.parse(raw);if(data?.version!==1||!Array.isArray(data.leads)||!Array.isArray(data.history)||!Array.isArray(data.followups))return null;return data;}catch{return null;}}
export function writeSynthetic(storage,data){if(!data||!Array.isArray(data.leads)||!Array.isArray(data.history)||!Array.isArray(data.followups))throw Error('Invalid synthetic CRM state');storage.setItem(STORAGE_KEY,JSON.stringify({version:1,...data}));}
export function clearSynthetic(storage){storage.removeItem(STORAGE_KEY);}
