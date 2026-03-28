import gspread
from oauth2client.service_account import ServiceAccountCredentials

class sheet_API:
    def __init__(self):
        self.scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        self.creds = ServiceAccountCredentials.from_json_keyfile_name("cred.json", self.scopes)
        self.client = gspread.authorize(self.creds)

    def __get_table_column_val(self, spreadsheet_name, sheet_name, table_range):
        sheet = self.client.open(spreadsheet_name).worksheet(sheet_name)
        data = sheet.get_values(table_range)

        if not data:
            return None
        
        headers = data[0]
        rows = data[1:]
        row_dict = {}
        for row in rows:
            row_dict = dict(zip(headers, row))

        return row_dict
    
    def convert_LUT(table_name) -> str:
        

        return 