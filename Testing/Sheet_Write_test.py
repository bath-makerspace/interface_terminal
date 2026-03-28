import os
from oauth2client.service_account import ServiceAccountCredentials
import gspread


scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive","https://www.googleapis.com/auth/spreadsheets"]
creds = ServiceAccountCredentials.from_json_keyfile_name("cred.json", scopes)
client = gspread.authorize(creds)

table_title = "Pending"
new_row_data = ["Test", "Data", "For", "Pending"]

sheet = client.open("GUI_Credit Tracker").worksheet("Pending")

first_row = sheet.row_values(1)
start_col_idx = 1

col_values = sheet.col_values(start_col_idx)
first_empty_row = len(col_values) + 1

# 3. Define the Range to update
# Example: If table is F1.75 (Col A) and row is 21, range is A21:F21
num_cols = len(new_row_data)

def col_to_letter(n):
    string = ""
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        string = chr(65 + remainder) + string
    return string

start_let = col_to_letter(start_col_idx)
end_let = col_to_letter(start_col_idx + num_cols - 1)

target_range = f"{start_let}{first_empty_row}:{end_let}{first_empty_row}"

# 4. Write the data
sheet.update(range_name=target_range, values=[new_row_data])
print(f"Successfully added row to {table_title} at {target_range}")
    