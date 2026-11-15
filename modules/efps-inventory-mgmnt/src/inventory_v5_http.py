"""Staged HTTP client preserving structured Notion terminal-write evidence.

No retries for PATCH. A timeout is unknown, not proof of commit or cancellation.
The exact documented saved-response path may read back, never resend the write.
"""
import time
try:
    from .inventory_v5 import content_hash
except ImportError:
    from inventory_v5 import content_hash

class V5NotionWriteError(RuntimeError):
    def __init__(self,*,status,body,request_id=None,dispatch=None):
        super().__init__('Notion write failed with HTTP '+str(status))
        self.dispatch=dispatch
        self.status=status;self.body=body if isinstance(body,dict)else {};self.request_id=request_id or self.body.get('request_id')

    def receipt(self):
        return {'status':self.status,'code':self.body.get('code'),'request_id':self.request_id,
                'additional_data':self.body.get('additional_data',{}),'message':self.body.get('message',''),'dispatch':self.dispatch,'body':self.body}

    def explicitly_saved(self):
        # Only the documented terminal saved-write response, not generic503,
        # deadline text, English message alone,504oratransportexception.
        extra=self.body.get('additional_data',{})
        guidance=extra.get('retry_guidance',[])if isinstance(extra,dict)else[]
        return self.status==503 and self.body.get('code')=='service_unavailable' and           isinstance(guidance,list) and guidance==['Read the object again to confirm the saved change.','Do not repeat the write.'] and           bool(self.request_id) and isinstance(self.dispatch,dict) and self.dispatch.get('method')=='PATCH'



class V5HttpNotionClient:
    def __init__(self,*,token,version,session):
        self.token=token;self.version=version;self.session=session

    def _request(self,method,page,properties=None):
        started=time.monotonic()
        dispatch={'method':method,'page_id':page,'body_hash':content_hash({'properties':properties})if properties is not None else None,'started_monotonic':started}
        response=self.session.request(method,'https://api.notion.com/v1/pages/'+page,
          headers={'Authorization':'Bearer '+self.token,'Notion-Version':self.version,'Content-Type':'application/json'},
          json={'properties':properties}if properties is not None else None,timeout=25)
        dispatch['finished_monotonic']=time.monotonic()
        try:body=response.json()
        except ValueError:body={}
        if not response.ok:
            raise V5NotionWriteError(status=response.status_code,body=body,request_id=response.headers.get('x-request-id'),dispatch=dispatch)
        return body

    def get_page(self,page):return self._request('GET',page)
    def update_page(self,page,properties):return self._request('PATCH',page,properties)
