"""
Manual test entrypoint for the meta catalog generator.
"""
import sys
import json

# Ensure other project modules can be imported
sys.path.insert(0, ".")

from shared.google_sheets.client import GoogleSheetsClient
from shared.google_sheets import schema
from modules.efps_meta_catalogue_mgmnt.src.generator import generate_catalog_text, get_image_urls

def run_test(listing_id: str):
    """
    Fetches a single row from the sheet by listing_id and prints its generated catalog.
    """
    print(f"--- Running test for listing_id: {listing_id} ---")
    
    # 1. Fetch data from sheet
    client = GoogleSheetsClient()
    try:
        # Read the safe range first to find the row number
        rows = client.read_range(schema.SHEET_ID, schema.WORKSHEET_NAME, "A2:AT")
        target_row_data = None
        target_row_number = -1
        
        for i, row in enumerate(rows, start=2):
            if row and row[0] == listing_id:
                target_row_number = i
                # Now fetch the full row to get all data, including image URLs
                full_row_list = client.read_range(schema.SHEET_ID, schema.WORKSHEET_NAME, f"A{i}:AV{i}")[0]
                padded_row = list(full_row_list) + [""] * (schema.GRID_WIDTH - len(full_row_list))
                target_row_data = schema.row_to_mapping(padded_row)
                break
        
        if not target_row_data:
            print(f"ERROR: Listing ID '{listing_id}' not found.")
            return

    except Exception as e:
        print(f"ERROR reading from sheet: {e}")
        return

    # 2. Generate catalog text
    catalog_text = generate_catalog_text(target_row_data)
    
    # 3. Get image URLs
    image_urls = get_image_urls(target_row_data)
    
    # 4. Print results
    print("\\n--- Proposed Format ---\\n")
    print(catalog_text)
    print("\\n--- Image Attachments (up to 10) ---")
    if image_urls:
        for url in image_urls:
            print(f"• {url}")
    else:
        print("No images found for this property.")
    print("\\n" + "="*40 + "\\n")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Test with specified listing ID
        run_test(sys.argv[1])
    else:
        # Run with default examples if no ID is provided
        print("No listing_id provided. Running default tests.")
        run_test("EF-2609-YWY8") # Example with society name
        run_test("EF-2609-R94M") # Assumed example without society for demo
