import test from 'node:test';
import assert from 'node:assert/strict';
import {
  projectLegacyRequirementProfile,
  compareRequirementProfiles,
  buildPropertyMatchingInputs,
  matchPropertyRows,
  auditRequirementAndMatching
} from '../src/crm-requirement-match-audit.mjs';

test('legacy requirement projection is deterministic and complete',()=>{
  const lead={tenant_type:'Family',requirements:{bhk:'2 BHK',budget:'45000',locality:'Sarjapur',furnishing:'Semi Furnished',pets:'No',parking:'Required',property_type:'Apartment',bathrooms:'2'}};
  assert.deepEqual(projectLegacyRequirementProfile(lead),{
    bhk:'2 BHK',budget:45000,preferred_locations:['Sarjapur'],tenant_type:'Family',move_in_date:null,pets:'No',
    veg_nonveg:'Unknown',furnishing:'Semi Furnished',parking:'Required',property_type:'Apartment',bathrooms:'2',
    occupancy_count:null,lease_term_months:null,preferred_floor:'',preferred_amenities:[],notes:''
  });
});

test('field correctness rejects a changed canonical field',()=>{
  const actual=projectLegacyRequirementProfile({tenant_type:'Family',requirements:{bhk:'2 BHK',budget:'45000'}});
  const changed={...actual,budget:50000};
  assert.equal(compareRequirementProfiles(changed,actual).ok,false);
});

test('matching inputs and results use the same deterministic predicates',()=>{
  const input=buildPropertyMatchingInputs({bhk:'2 BHK',budget:50000,preferred_locations:['Sarjapur'],furnishing:'Semi Furnished',pets:'No'});
  const rows=[
    {listing_id:'A',listing_state:'Available',bhk:'2 BHK',monthly_rent:45000,locality:'Sarjapur Road',furnishing:'Semi Furnished',pet_friendly:'No'},
    {listing_id:'B',listing_state:'Available',bhk:'3 BHK',monthly_rent:40000,locality:'Sarjapur',furnishing:'Semi Furnished',pet_friendly:'No'}
  ];
  assert.deepEqual(matchPropertyRows(rows,input).map(r=>r.listing_id),['A']);
});

test('combined audit fails closed on missing profile or mismatched field',()=>{
  const result=auditRequirementAndMatching({
    qualifiedLeads:[
      {lead_id:'L1',tenant_type:'Family',requirements:{bhk:'2 BHK',budget:'45000'},profile:null},
      {lead_id:'L2',tenant_type:'Family',requirements:{bhk:'2 BHK',budget:'45000'},profile:{...projectLegacyRequirementProfile({tenant_type:'Family',requirements:{bhk:'2 BHK',budget:'45000'}}),budget:50000}}
    ],
    inventoryRows:[]
  });
  assert.equal(result.population.profilesMissing,1);
  assert.equal(result.fieldCorrectness.mismatchedLeads,1);
  assert.equal(result.complete,false);
});
