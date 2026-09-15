"""Crash-to-bug reporting for public EFPS handlers."""
from __future__ import annotations
import functools,logging,traceback
from typing import Any,Callable
log=logging.getLogger(__name__)
SEVERITY={"webhook":"critical","leads_worker":"critical","batch":"major","events":"major","interactive":"major","commands":"minor"}
SLACK_OK={"statusCode":200,"body":""}
def _describe(exc):return f"{type(exc).__name__}: {str(exc).strip().splitlines()[0] if str(exc).strip() else ''}"[:200]
def report(where:str,exc:BaseException,*,reference:str="")->None:
    try:
        from . import bugs
        bugs.log_error(_describe(exc),where=where,reference=reference,detail=traceback.format_exc()[-3000:],severity=SEVERITY.get(where,"major"))
    except Exception:log.exception("could not file crash in %s",where)
def guarded(where:str,*,returns:Any=None)->Callable:
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(event,context):
            try:return fn(event,context)
            except Exception as exc:
                log.exception("unhandled failure in %s",where);report(where,exc)
                if returns is not None:return returns
                raise
        return wrapper
    return deco
