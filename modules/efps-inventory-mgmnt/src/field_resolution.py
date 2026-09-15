"""Canonical deterministic candidate resolution for Inventory Stage 2.

Extraction discovers source candidates; this module chooses the authoritative
candidate. It contains no AI and never uses existing Sheet values as source
truth. Resolution traces are diagnostic artifacts and are not written to the
48-column production Sheet.
"""
from __future__ import annotations
import re
from dataclasses import dataclass, asdict
from .source_segments import split_source_messages

@dataclass(frozen=True)
class Candidate:
    field: str
    value: str
    segment_index: int
    method: str
    explicit: bool
    position: int

def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[*_`~]", "", str(value or ""))).strip(" -–—")

def _segments(text: str) -> list[str]: return split_source_messages(text)

def _label_candidates(text: str, label: str, field: str) -> list[Candidate]:
    out=[]; pattern=re.compile(rf"\b{label}\b\s*(?::|[-–—|=])\s*([^|\n<]+)",re.I)
    for i,segment in enumerate(_segments(text)):
        for match in pattern.finditer(segment):
            value=_clean(match.group(1))
            if value: out.append(Candidate(field,value,i,"label",True,match.start()))
    return out

def resolve_bhk(text: str) -> str:
    candidates=[]
    for i,segment in enumerate(_segments(text)):
        for m in re.finditer(r"\b(\d+(?:\.\d+)?)\s*[- ]?\s*bhk\b",segment,re.I): candidates.append(Candidate("BHK",f"{m.group(1)} BHK",i,"direct",True,m.start()))
        for m in re.finditer(r"\bbed\s*rooms?\s*[:\-]\s*(\d+(?:\.\d+)?)\b",segment,re.I): candidates.append(Candidate("BHK",f"{m.group(1)} BHK",i,"label",True,m.start()))
        for m in re.finditer(r"\b(\d+(?:\.\d+)?)\s*[- ]?\s*bed\s*rooms?\b",segment,re.I): candidates.append(Candidate("BHK",f"{m.group(1)} BHK",i,"direct",True,m.start()))
    if candidates: return sorted(candidates,key=lambda c:(c.segment_index,c.position))[-1].value
    return "1 RK" if re.search(r"\bstudio\b",text,re.I) else ""

def _scale_number(value:str,unit:str="") -> str:
    n=float(value.replace(",","")); u=(unit or "").lower()
    if u=="k": n*=1000
    elif u in {"l","lakh","lakhs"}: n*=100000
    return str(int(n))

def resolve_maintenance(text: str) -> tuple[str,str]:
    candidates=[]
    for i,segment in enumerate(_segments(text)):
        pattern=re.compile(r"\bmaintenance\b\s*(?::|[-–—|=])\s*([^|\n<]+)",re.I)
        for m in pattern.finditer(segment):
            value=_clean(m.group(1))
            if value: candidates.append(Candidate("maintenance",value,i,"label",True,m.start()))
        pattern=re.compile(r"(?:₹|rs\.?\s*)?\s*\d[\d,.]*\s*(?:k|lakh|l)?\s*\+\s*(\d[\d,.]*)\s*(k|lakh|l)?\s*maintenance\b",re.I)
        for m in pattern.finditer(segment): candidates.append(Candidate("maintenance",_scale_number(m.group(1),m.group(2)),i,"rent_suffix",True,m.start()))
    if not candidates:return "",""
    chosen=sorted(candidates,key=lambda c:(c.segment_index,c.position))[-1]; raw=chosen.value.strip()
    if raw.lower()=="included":return "0","Yes"
    m=re.fullmatch(r"([\d.,]+)\s*(k|lakh|l)?\s*(?:\+\s*(.+))?",raw,re.I)
    if not m:return re.sub(r"(?<=\d),(?=\d)","",raw),"No"
    result=_scale_number(m.group(1),m.group(2)); suffix=_clean(m.group(3) or "")
    return (f"{result} + {suffix}" if suffix else result),"No"

def resolve_internal_property_type(text: str) -> str:
    explicit=[]
    for label,method in ((r"internal\s*property\s*type","internal"),(r"property\s*(?:type|classification)","property_label"),(r"gating\s*type","gating_label")):
        for candidate in _label_candidates(text,label,"internal_property_type"):
            value=candidate.value.lower()
            if "semi" in value and "gated" in value:explicit.append(Candidate(candidate.field,"Semi Gated",candidate.segment_index,method,True,candidate.position))
            elif "gated" in value:explicit.append(Candidate(candidate.field,"Gated Community",candidate.segment_index,method,True,candidate.position))
            elif "stand" in value:explicit.append(Candidate(candidate.field,"Standalone",candidate.segment_index,method,True,candidate.position))
    boolean=[]; pattern=re.compile(r"\b(?P<label>semi[-\s]*gated|gated\s*(?:community|society|property)?)\b\s*(?:[:=|\-])\s*(?P<value>[^|\n<]+)",re.I)
    yes={"yes","y","true","1","allowed"}; no={"no","n","false","0","not allowed","not permitted","none"}
    for i,segment in enumerate(_segments(text)):
        for m in pattern.finditer(segment):
            value=_clean(m.group("value")).lower()
            if value in yes:boolean.append(Candidate("internal_property_type","Semi Gated" if "semi" in m.group("label").lower() else "Gated Community",i,"boolean",True,m.start()))
            elif value in no:boolean.append(Candidate("internal_property_type","Standalone",i,"boolean_negative",True,m.start()))
    if boolean:return sorted(boolean,key=lambda c:(c.segment_index,c.position))[-1].value
    if explicit:return sorted(explicit,key=lambda c:(c.segment_index,c.position))[-1].value
    generic=[]
    for i,segment in enumerate(_segments(text)):
        if re.search(r"\bsemi[-\s]*gated\b",segment,re.I):generic.append(Candidate("internal_property_type","Semi Gated",i,"generic",False,0))
        elif re.search(r"\bgated\s*(?:community|society|property)\b",segment,re.I):generic.append(Candidate("internal_property_type","Gated Community",i,"generic",False,0))
        elif re.search(r"\b(?:independent\s+(?:house|floor)|farm\s*house|stand[-\s]*alone)\b",segment,re.I):generic.append(Candidate("internal_property_type","Standalone",i,"generic",False,0))
    return sorted(generic,key=lambda c:(c.segment_index,c.position))[-1].value if generic else "Standalone"

def trace(text: str) -> dict:
    """Return diagnostic source candidates and selected values without side effects."""
    bhk=resolve_bhk(text); maintenance,maintenance_included=resolve_maintenance(text); property_type=resolve_internal_property_type(text)
    return {
        "BHK":{"selected":bhk},
        "maintenance":{"selected":maintenance,"maintenance_included":maintenance_included},
        "internal_property_type":{"selected":property_type},
        "source_segments":_segments(text),
    }
