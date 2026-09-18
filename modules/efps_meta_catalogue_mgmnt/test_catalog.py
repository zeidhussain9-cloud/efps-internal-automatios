"""
Manual test entrypoint for publishing a meta catalog item.
"""
import sys
import json

sys.path.insert(0, ".")

from shared.google_sheets.client import GoogleSheetsClient
from shared.google_sheets import schema
from modules.efps_meta_catalogue_mgmnt.src.generator import publish_catalog

def run_publish(listing_id: str):
    print(f"--- Attempting to publish catalog for listing_id: {listing_id} ---")
    
    client = GoogleSheetsClient()
    try:
        rows = client.read_range(schema.SHEET_ID, schema.WORKSHEET_NAME, "A2:AV50") # Read all columns
        target_row_data = None
        target_row_number = -1
        
        for i, row in enumerate(rows, start=2):
            if row and row[0] == listing_id:
                target_row_number = i
                padded_row = list(row) + [""] * (schema.GRID_WIDTH - len(row))
                target_row_data = schema.row_to_mapping(padded_row)
                break
        
        if not target_row_data:
            print(f"ERROR: Listing ID '{listing_id}' not found.")
            return

    except Exception as e:
        print(f"ERROR reading from sheet: {e}")
        return

    # Publish the catalog
    result = publish_catalog(target_row_number, target_row_data)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_publish(sys.argv[1])
    else:
        print("Usage: python modules/efps_meta_catalogue_mgmnt/test_catalog.py <listing_id>")
