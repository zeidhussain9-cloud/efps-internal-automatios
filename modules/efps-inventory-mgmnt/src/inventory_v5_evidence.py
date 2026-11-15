"""Evidence-preserving extraction overlays for the staged v5 path.

These helpers do not reinterpret old derived measurements as raw source facts.
Unsupported source conflicts produce review issues rather than exact guesses.
"""
from __future__ import annotations
from decimal import Decimal
import re
try:
    from .inventory_v5 import balcony_evidence, decimal_value, derive_areas, derive_deposit, number_text, pet_evidence
except ImportError:
    from inventory_v5 import balcony_evidence, decimal_value, derive_areas, derive_deposit, number_text, pet_evidence


def _one(matches, label, issues):
    values = set(matches)
    if len(values) > 1:
        issues.append(f'Conflicting explicit {label} values')
        return ''
    return next(iter(values)) if values else ''


def evidence_overlay(raw):
    values, provenance, issues = {}, {}, []
    balcony, error = balcony_evidence(raw)
    if error:issues.append(error)
    values['balconies'] = '' if balcony is None else balcony
    if balcony not in (None, ''):provenance['balconies'] = {'origin':'source_explicit','evidence':'balcony wording'}
    for field, label in [('carpet_area',r'carpet[ \t]*area'),('built_up_area',r'built[ -]*up[ \t]*area')]:
        hits=re.findall(r'\b'+label+r'[ \t]*(?:[:=-][ \t]*)?(\d+(?:\.\d+)?)[ \t]*(?:sq\.?[ \t]*ft\.?|sqft|sft)?\b',raw,re.I)
        v=_one(hits,field,issues)
        values[field]=v
        if v:provenance[field]={'origin':'source_explicit','evidence':field+' labelled source'}
    # Generic sqft is built-up only when its line is not an explicit carpet line.
    if not values['built_up_area']:
        hits=[]
        for line in raw.splitlines():
            if re.search(r'\bcarpet\b',line,re.I):continue
            if re.search(r'\bbuilt[ -]*up\b',line,re.I):continue
            hits.extend(re.findall(r'\bsq\.?[ \t]*ft\.?[ \t]*[:=-][ \t]*(\d+(?:\.\d+)?)\b',line,re.I))
            hits.extend(re.findall(r'\b(\d+(?:\.\d+)?)[ \t]*(?:sq\.?[ \t]*ft\.?|sqft|sft)\b',line,re.I))
        v=_one(hits,'generic sqft',issues)
        values['built_up_area']=v
        if v:provenance['built_up_area']={'origin':'source_explicit','evidence':'generic sqft source'}
    explicit=set(provenance)&{'carpet_area','built_up_area'}
    derived,area_errors=derive_areas(values['built_up_area'],values['carpet_area'],explicit)
    values.update(derived);issues.extend(area_errors)
    for field,value in derived.items():provenance[field]={'origin':'derived','last_generated_value':value,'derivation_version':5,'rule':'90sqft missing-side buffer'}
    # Only labelled rent is usable for a deposit conversion; a lone currency
    # amount could be a deposit, maintenance or another property's price.
    rents=[]
    for match in re.finditer(r'\b(?:rent|rental)[ \t]*[:=-][ \t]*(?:₹|rs\.?|inr)?[ \t]*([\d,]+(?:\.\d+)?)[ \t]*(k|lakh|lakhs|l)?\b',raw,re.I):
        n=decimal_value(match.group(1).replace(',',''))
        if n is not None:rents.append(number_text(n*(1000 if (match.group(2)or'').lower()=='k' else 100000 if match.group(2) else 1)))
    rent=_one(rents,'rent',issues)
    values['monthly_rent']=rent
    if rent:provenance['monthly_rent']={'origin':'source_explicit','evidence':'labelled rent'}
    deposits=[];months=[]
    for match in re.finditer(r'\b(?:deposit|dep|advance)[ \t]*[:=-][ \t]*(?:₹|rs\.?|inr)?[ \t]*([\d,]+(?:\.\d+)?)[ \t]*(months?|mnths?|mos?|k|lakhs?|l)?\b',raw,re.I):
        unit=(match.group(2)or'').lower();n=decimal_value(match.group(1).replace(',',''))
        if n is None:continue
        if unit.startswith(('month','mnth','mo')):months.append(number_text(n))
        else:deposits.append(number_text(n*(1000 if unit=='k' else 100000 if unit in('l','lakh','lakhs')else 1)))
    month=_one(months,'deposit-month',issues);amount=_one(deposits,'deposit-amount',issues)
    values['security_deposit']=''
    if month and amount:
        issues.append('Both deposit amount and months supplied; review before conversion')
    elif amount:
        values['security_deposit']=amount;provenance['security_deposit']={'origin':'source_explicit','evidence':'explicit deposit amount'}
    elif month:
        amount,errors=derive_deposit(month,rent);issues.extend(errors);values['security_deposit']=amount
        provenance['security_deposit']={'origin':'derived','deposit_months':month,'last_generated_value':amount,'derivation_version':5}
    values['pet_friendly']=pet_evidence(raw)
    provenance['pet_friendly']={'origin':'source_explicit' if re.search(r'\bpets?\b',raw,re.I)else'derived','last_generated_value':values['pet_friendly']}
    return values,provenance,issues
