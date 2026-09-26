// Entirely fictional fixture. The EFPS source numbers below are verified operator numbers,
// not customer identities. The conversation examples are newly written, not copied from raw messages.
// This is a seed for the synthetic pilot, NOT the final statistically representative dataset.
export const efpsSources=['+919148338801','+917975102130','+919902024973'];
export const customers=[
 {id:'TEST-001',name:'Synthetic Customer A',phone:'+919000000001',source:efpsSources[0],requirements:{bhk:2,locations:['Harlur'],budgetMax:52000,pets:'Allowed'},messages:[{id:'T1',direction:'in',body:'I need a 2 BHK in Harlur, around 52k. We have a dog.'},{id:'T2',direction:'out',body:'Would you prefer furnished or semi-furnished?'},{id:'T3',direction:'in',body:'Semi-furnished is fine. Covered parking would help.'}],expected:{bhk:2,locations:['Harlur'],budgetMax:52000,pets:'Allowed',parking:'Preferred'}},
 {id:'TEST-002',name:'Synthetic Customer B',phone:'+919000000002',source:efpsSources[1],requirements:{bhk:1,locations:['Bellandur'],budgetMax:35000},messages:[{id:'T4',direction:'in',body:'Any 1 BHK near Bellandur under 35k?'},{id:'T5',direction:'in',body:'Actually, my maximum budget is now 32k.'}],expected:{bhk:1,locations:['Bellandur'],budgetMax:32000}},
 {id:'TEST-003',name:'Synthetic Customer C',phone:'+919000000003',source:efpsSources[2],requirements:{bhk:3,locations:['Whitefield'],budgetMax:null},messages:[{id:'T6',direction:'in',body:'Checking whether you have 3 BHK homes in Whitefield.'}],expected:{bhk:3,locations:['Whitefield'],budgetMax:null}}
];
export const inventory=[
 {listing_id:'TEST-P001',locality:'Harlur',BHK:2,monthly_rent:49000,listing_state:'Available',furnish_type:'Semi Furnished',pet_friendly:'Yes',cloudinary_image_urls:[],maintenance:null,maintenance_included:null},
 {listing_id:'TEST-P002',locality:'Bellandur',BHK:1,monthly_rent:31000,listing_state:'Available',furnish_type:'Semi Furnished',pet_friendly:null,cloudinary_image_urls:[],maintenance:null,maintenance_included:null},
 {listing_id:'TEST-P003',locality:'Whitefield',BHK:3,monthly_rent:75000,listing_state:'Rented Out',furnish_type:'Fully Furnished',pet_friendly:'No',cloudinary_image_urls:[],maintenance:null,maintenance_included:null}
];
export function assertSyntheticFixture(){const ids=[...customers.map(c=>c.id),...inventory.map(p=>p.listing_id)];if(new Set(ids).size!==ids.length)throw Error('Duplicate fixture IDs');if(customers.some(c=>efpsSources.includes(c.phone)))throw Error('Customer number must differ from EFPS source');if(customers.some(c=>!efpsSources.includes(c.source)))throw Error('Unknown EFPS source');if(inventory.some(p=>!Array.isArray(p.cloudinary_image_urls)))throw Error('Inventory image URLs must be arrays');return true;}
