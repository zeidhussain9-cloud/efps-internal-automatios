import pytest
from src.inventory_v5_notion import V5NotionPort
class C:
    def update_page(self,page,p):self.last=(page,p);return {'ok':True}
def test_narrow_notional_patch_never_sends_missing_options_or_formula():
    c=C();n=V5NotionPort(c,{'SL number':{'type':'title'},'Availability':{'type':'select','select':{'options':[{'name':'Available'}]}},'Live On':{'type':'multi_select','multi_select':{'options':[{'name':'Meta Catalogue'}]}}})
    n.patch('page',{'SL number':1,'Live On':[]})
    assert c.last==('page',{'SL number':{'title':[{'type':'text','text':{'content':'1'}}]},'Live On':{'multi_select':[]}})
    with pytest.raises(ValueError):n.patch('page',{'Availability':'Maybe'})
    with pytest.raises(ValueError):n.patch('page',{'missing':'x'})
