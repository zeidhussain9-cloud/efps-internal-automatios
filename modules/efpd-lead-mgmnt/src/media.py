"""Lead media adapter backed by shared Cloudinary transport."""
from __future__ import annotations
import hashlib
from dataclasses import dataclass
from shared.cloudinary.client import CloudinaryClient
@dataclass
class Upload:url:str;public_id:str;index:int
def lead_public_id(phone,message_id,index):
 safe="".join(c for c in str(message_id) if c.isalnum() or c in "-_") or "nomsg";return f"leads/{str(phone).strip()}/{safe}_{index}"
def upload_lead_images(phone,message_id,blobs,*,_uploader=None):
 if not blobs:return []
 client=CloudinaryClient(uploader=_uploader);out=[]
 for i,blob in enumerate(blobs,1):
  pid=lead_public_id(phone,message_id,i);r=client.upload_bytes(blob,public_id=pid,resource_type="image",overwrite=False);out.append(Upload(str(r["secure_url"]),pid,i))
 return out
def image_fingerprint(blob):return hashlib.sha256(blob).hexdigest()[:16]
