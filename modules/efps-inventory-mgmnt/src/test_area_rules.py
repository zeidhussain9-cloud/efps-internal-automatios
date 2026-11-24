from __future__ import annotations
import pipeline

def _row(area_text):
    raw="*Semi Furnished 2 BHK with 2 Bathrooms*\n\nRent: 25K\nDeposit: 3 Months\n"+area_text+"\nFloor: 3/4\nGated Community\nLocation: *Haralur*"
    return pipeline.deterministic(raw,pipeline.initial_row("EF-TEST-AREA"))

def test_plain_sqft_is_carpet_and_built_up_adds_90():
    for t in ("Sqft: 1200","Sq.ft: 1200","1200 sqft","Sqft : 1200"):
        r=_row(t);assert (r["carpet_area"],r["built_up_area"])==("1200","1290"),t

def test_labelled_carpet_only():
    for t in ("Carpet area: 1000","Carpet: 1000","Carpet Area 1000 sqft"):
        r=_row(t);assert (r["carpet_area"],r["built_up_area"])==("1000","1090"),t

def test_labelled_built_up_only_derives_carpet():
    for t in ("Built-up area: 1100","Built up: 1100","Builtup area 1100 sqft"):
        r=_row(t);assert (r["built_up_area"],r["carpet_area"])==("1100","1010"),t

def test_both_labelled_are_kept_as_given():
    r=_row("Carpet area: 1000\nBuilt-up area: 1250");assert (r["carpet_area"],r["built_up_area"])==("1000","1250")

def test_labelled_built_up_not_overwritten_by_generic_sqft():
    r=_row("Built-up area: 1100\nSqft: 1100");assert (r["built_up_area"],r["carpet_area"])==("1100","1010")

def test_super_built_up_is_not_treated_as_built_up():
    r=_row("Super built-up area: 1500 sqft");assert r.get("built_up_area","")=="" and r.get("carpet_area","")==""

def test_no_area_stays_blank():
    r=_row("");assert r.get("built_up_area","")=="" and r.get("carpet_area","")==""
