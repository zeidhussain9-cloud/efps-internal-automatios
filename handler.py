"""Scheduled Inventory worker; uses only the canonical new Inventory package."""
from __future__ import annotations
import json,sys
sys.path.insert(0, str(__file__).rsplit("/",1)[0] + "/modules/efps-inventory-mgmnt/src")
from pipeline import process_closed_session, write_phase1_update
from shared.google_sheets import schema
from shared.google_sheets.client import GoogleSheetsClient

def lambda_handler(event,context):
 client=GoogleSheetsClient();raw=client.read_range(schema.SHEET_ID,schema.WORKSHEET_NAME,"A2:AT");processed=0;review=0;errors=[]
 for idx,values in enumerate(raw,start=2):
  if not values:continue
  padded=list(values)+[""]*(schema.GRID_WIDTH-len(values)) if len(values)<schema.GRID_WIDTH else list(values)
  row=schema.row_to_mapping(padded)
  if str(row.get("intake_status") or "").strip()!="Raw":continue
  try:
   out,issues=process_closed_session(str(row.get("raw_message_text") or ""),row=row);write_phase1_update(client,idx,out);processed+=1;review+=out.get("status")=="Needs Review"
  except Exception as exc:errors.append(f"row {idx}: {exc}")
 result={"processed":processed,"needs_review":review,"errors":errors[:20]};print(json.dumps(result));return result
