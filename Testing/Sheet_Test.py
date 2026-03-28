import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Authorize the API
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("cred.json", scope)
client = gspread.authorize(creds)


def get_filament_table(spreadsheet_name, table_range):
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("cred.json", scope)
    client = gspread.authorize(creds)
    
    # Open the 'Filament' tab specifically
    sheet = client.open(spreadsheet_name).worksheet("Filament")
    
    # Fetch only the range for that table
    # This returns a list of lists (rows)
    data = sheet.get_values(table_range)
    
    if not data:
        print("No data found.")
        return

    # Extract headers (the first row of the range)
    headers = data[0]
    rows = data[1:]

    print(f"--- Printing Table: {table_range} ---")
    print(rows[0])
#     for row in rows:
#         # Zip creates a dictionary style view: {'Brand': 'Bambu', 'Colour': 'Natural', ...}
#         row_dict = dict(zip(headers, row))
#         print(row_dict)

# # --- Usage Examples based on your image ---

# 1. To get the F1.75 Table (Columns A to F)
get_filament_table("Inventory", "H:M")