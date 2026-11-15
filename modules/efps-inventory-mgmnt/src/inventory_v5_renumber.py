"""Resumable single-writer SL title updater, independent of listing identity.

The persisted membership snapshot fixes rank for the complete pass. Membership
changes coalesce into the next job. Notion cannot atomically change104titles;
the view may show intermediate numbers while a migration is paused.
"""
from __future__ import annotations

def run_renumber(*, repository, notion, max_rows=20):
    job=repository.claim()
    if job.get('busy') or job.get('idle'):return job
    ids=job['ordered_page_ids'];offset=job['next_offset']
    token=job['lease_token'];job_id=job['job_id'];changed=[]
    for index in range(offset,min(len(ids),offset+max_rows)):
        repository.renew(job_id,token)
        page=notion.snapshot(ids[index])
        if page.get('_archived'):
            repository.fail(job_id,token,'Membership changed; fresh reference job required')
            return {'status':'membership_changed','changed':changed}
        desired=str(index+1)
        if page.get('SL number')!=desired:
            # Re-read protects detected races, but the Notion operation itself
            # remains non-atomic against a simultaneous human title edit.
            check=notion.snapshot(ids[index])
            if check.get('SL number')!=page.get('SL number'):
                repository.fail(job_id,token,'Concurrent title edit')
                return {'status':'needs_review','changed':changed}
            repository.prepare_title(ids[index],desired)
            repository.effect(job_id,token,{'page_id':ids[index],'patch':{'SL number':desired}},
                              lambda:notion.patch(ids[index],{'SL number':desired}))
            final=notion.snapshot(ids[index])
            if final.get('SL number')!=desired:
                repository.fail(job_id,token,'Title readback mismatch')
                return {'status':'needs_review','changed':changed}
            repository.ack_title(ids[index],desired)
            changed.append(ids[index])
        repository.checkpoint(job_id,token,index+1)
    completed=min(len(ids),offset+max_rows)==len(ids)
    if completed:repository.finish(job_id,token)
    else:repository.yield_lease(job_id,token)
    return {'status':'completed' if completed else 'paused','changed':changed}
