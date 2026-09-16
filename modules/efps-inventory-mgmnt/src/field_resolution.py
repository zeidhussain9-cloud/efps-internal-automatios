"""Canonical deterministic candidate resolution for Inventory Stage 2."""
from __future__ import annotations
import re
from dataclasses import dataclass
try:
    from .source_segments import split_source_messages
except ImportError:
    from source_segments import split_source_messages

AUTHORIZED_PROPERTY_SUBTYPES=("Apartment","Villa","Independent House","Duplex","Studio","Independent Floor")
@dataclass(frozen=True)
class Candidate:
    field:str; value:str; segment_index:int; method:str; explicit:bool; position:int
def _clean(value:str)->str:return re.sub(r"\s+"," ",re.sub(r"[*_`~]","",str(value or ""))).strip(" -–—")
def _segments(text:str)->list[str]:return split_source_messages(text)
def _label_candidates(text:str,label:str,field:str)->list[Candidate]:
    out=[];pattern=re.compile(rf"\b(?:{label})\b\s*(?::|[-–—|=])\s*([^|\n<]+)",re.I)
    for i,segment in enumerate(_segments(text)):
        for match in pattern.finditer(segment):
            value=_clean(match.group(1))
            if value:out.append(Candidate(field,value,i,"label",True,match.start()))
    return out
def _community_name_candidates(text:str)->list[Candidate]:
    out=[];marker=re.compile(r"📍\s*([^:\n|]+?)\s*:\s*",re.I)
    for match in marker.finditer(text or ""):
        name=_clean(match.group(1))
        if name and not re.fullmatch(r"(?:landmark|location)\s*",name,re.I):out.append(Candidate("society_name",name,0,"marker",True,match.start()))
    out.extend(_label_candidates(text,r"society\s*name|society|apartment\s*name|community\s*name|building\s*name","society_name"));return sorted(out,key=lambda c:c.position)
def resolve_bhk(text:str)->str:
    candidates=[]
    for i,segment in enumerate(_segments(text)):
        for m in re.finditer(r"\b(\d+(?:\.\d+)?)\s*[- ]?\s*bhk\b",segment,re.I):candidates.append(Candidate("BHK",f"{m.group(1)} BHK",i,"direct",True,m.start()))
        for m in re.finditer(r"\bbed\s*rooms?\s*[:\-]\s*(\d+(?:\.\d+)?)\b",segment,re.I):candidates.append(Candidate("BHK",f"{m.group(1)} BHK",i,"label",True,m.start()))
        for m in re.finditer(r"\b(\d+(?:\.\d+)?)\s*[- ]?\s*bed\s*rooms?\b",segment,re.I):candidates.append(Candidate("BHK",f"{m.group(1)} BHK",i,"direct",True,m.start()))
    if candidates:return sorted(candidates,key=lambda c:(c.segment_index,c.position))[-1].value
    return "1 RK" if re.search(r"\bstudio\b",text,re.I) or re.search(r"\b1\s*[- ]?\s*rk\b",text,re.I) else ""
def _scale_number(value:str,unit:str="")->str:
    n=float(value.replace(",",""));u=(unit or "").lower()
    if u=="k":n*=1000
    elif u in {"l","lakh","lakhs"}:n*=100000
    return str(int(n))
def resolve_maintenance(text:str)->tuple[str,str]:
    candidates=[]
    for i,segment in enumerate(_segments(text)):
        for m in re.finditer(r"\bmaintenance\b\s*(?::|[-–—|=])\s*([^|\n<]+)",segment,re.I):
            value=_clean(m.group(1))
            if value:candidates.append(Candidate("maintenance",value,i,"label",True,m.start()))
        for m in re.finditer(r"(?:₹|rs\.?\s*)?\s*\d[\d,.]*\s*(?:k|lakh|l)?\s*\+\s*(\d[\d,.]*)\s*(k|lakh|l)?\s*maintenance\b",segment,re.I):candidates.append(Candidate("maintenance",_scale_number(m.group(1),m.group(2)),i,"rent_suffix",True,m.start()))
    if not candidates:return "",""
    raw=sorted(candidates,key=lambda c:(c.segment_index,c.position))[-1].value.strip();low=raw.lower()
    if re.fullmatch(r"included(?:\s*\+\s*(?:water|water\s*charges?|utilities?|utility))?",low):
        qualifier=re.search(r"\+\s*(.+)$",raw,re.I);return ("0" if not qualifier else f"0 + {qualifier.group(1).strip()}"),"Yes"
    m=re.fullmatch(r"([\d.,]+)\s*(k|lakh|l)?\s*(?:\+\s*(.+))?",raw,re.I)
    if not m:return re.sub(r"(?<=\d),(?=\d)","",raw),"No"
    result=_scale_number(m.group(1),m.group(2));suffix=_clean(m.group(3) or "");return (f"{result} + {suffix}" if suffix else result),"No"
def _property_type_from_value(value:str)->str:
    low=re.sub(r"\s+"," ",str(value or "").strip().lower()).replace("–","-").replace("—","-");low=re.sub(r"\s*[-/]\s*"," ",low)
    if low in {"gated","gated community","gatedcommunity"}:return "Gated Community"
    if low in {"semi gated","semi-gated","semi gated community","semi-gated community","semigated","semigated community"}:return "Semi Gated"
    if low in {"standalone","stand alone","stand-alone","stand alone property","standalone property"}:return "Standalone"
    return ""
def resolve_internal_property_type(text:str)->str:
    explicit=[];labels=(r"internal\s*property\s*type",r"property\s*(?:type|classification)",r"gating\s*type",r"community")
    for label in labels:
        method="community_label" if label==r"community" else "property_type_label"
        for candidate in _label_candidates(text,label,"internal_property_type"):
            canonical=_property_type_from_value(candidate.value)
            if canonical:explicit.append(Candidate(candidate.field,canonical,candidate.segment_index,method,True,candidate.position))
    if explicit:return sorted(explicit,key=lambda c:(c.segment_index,c.position))[-1].value
    boolean=[];pattern=re.compile(r"\b(?P<label>semi[-\s]*gated(?:\s+community)?|gated(?:\s+community)?)\s*(?::|=|\||-)\s*(?P<value>[^|\n<]+)",re.I);yes={"yes","y","true","1","allowed","community","society","property"};no={"no","n","false","0","not allowed","not permitted","none"}
    for i,segment in enumerate(_segments(text)):
        for m in pattern.finditer(segment):
            value=_clean(m.group("value")).lower()
            if value in yes:boolean.append(Candidate("internal_property_type","Semi Gated" if "semi" in m.group("label").lower() else "Gated Community",i,"boolean",True,m.start()))
            elif value in no:boolean.append(Candidate("internal_property_type","Standalone",i,"boolean_negative",True,m.start()))
    if boolean:return sorted(boolean,key=lambda c:(c.segment_index,c.position))[-1].value
    generic=[]
    for i,segment in enumerate(_segments(text)):
        if re.search(r"\bsemi[-\s]*gated\b",segment,re.I):generic.append(Candidate("internal_property_type","Semi Gated",i,"generic",False,0))
        elif re.search(r"\bgated\s*(?:community|society|property)\b",segment,re.I):generic.append(Candidate("internal_property_type","Gated Community",i,"generic",False,0))
        elif re.search(r"\b(?:independent\s+(?:house|floor)|farm\s*house|stand[-\s]*alone)\b",segment,re.I):generic.append(Candidate("internal_property_type","Standalone",i,"generic",False,0))
    if generic:return sorted(generic,key=lambda c:(c.segment_index,c.position))[-1].value
    return ""
def _property_subtype_candidates(text:str)->tuple[set[str],bool]:
    labels=_label_candidates(text,r"property\s*subtype|subtype","property_subtype");source=" ".join(c.value for c in labels);scopes=(source,text or "");patterns=((r"\b1\s*[- ]?\s*rk\b|\bstudio\b","Studio"),(r"\bindependent\s+house\b","Independent House"),(r"\bindependent\s+floor\b","Independent Floor"),(r"\bduplex\b","Duplex"),(r"\bvilla\b","Villa"),(r"\b(?:apartment|flat|unit)\b","Apartment"));found=set();unsupported=False
    for scope in scopes:
        if re.search(r"\bpenthouse\b|\bfarm\s*house\b",scope,re.I):unsupported=True
        for pattern,canonical in patterns:
            if re.search(pattern,scope,re.I):found.add(canonical)
    if re.search(r"\bduplex\s+villa\b",text or "",re.I):found.discard("Villa")
    if len(found)>1 and "Apartment" in found:found.discard("Apartment")
    return found,unsupported
def has_property_subtype_evidence(text:str)->bool:
    found,unsupported=_property_subtype_candidates(text);return bool(found) or unsupported
def resolve_property_subtype(text:str)->str:
    found,unsupported=_property_subtype_candidates(text or "")
    if unsupported or len(found)!=1:return ""
    return next(iter(found))
def trace(text:str)->dict:
    bhk=resolve_bhk(text);maintenance,maintenance_included=resolve_maintenance(text);property_type=resolve_internal_property_type(text);subtype=resolve_property_subtype(text)
    return {"BHK":{"selected":bhk},"maintenance":{"selected":maintenance,"maintenance_included":maintenance_included},"internal_property_type":{"selected":property_type},"property_subtype":{"selected":subtype},"source_segments":_segments(text)}
