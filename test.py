import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Authorize the API
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("cred.json", scope)
client = gspread.authorize(creds)

# Open the sheet
spreadsheet = client.open("Inventory")

# READ data
sheet = spreadsheet.worksheet("Volunteers/Commitee")
records = sheet.get_all_records()

for row in records:
    print(row)

# WRITE data
# sheet.update_acell('B2', "Hello from Python!")  # Update one cell
# sheet.append_row(["Data 1", "Data 2", "Data 3"])  # Add a new row at the bottom