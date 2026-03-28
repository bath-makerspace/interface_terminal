import gspread
import pandas as pd
import os
from oauth2client.service_account import ServiceAccountCredentials

cwd = os.getcwd()

class sheet_API:
    def __init__(self):
        cred_filename = "cred.json"
        cred_path = os.path.join(cwd, cred_filename)
        self.scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive","https://www.googleapis.com/auth/spreadsheets"]
        self.creds = ServiceAccountCredentials.from_json_keyfile_name("cred.json", self.scopes)
        self.client = gspread.authorize(self.creds)


    def __get_table_column_val(self, spreadsheet_name, sheet_name, table_range):
        
        spreadsheet_name = spreadsheet_name.strip()
        sheet_name = sheet_name.strip()

        sheet = self.client.open(spreadsheet_name).worksheet(sheet_name)
        data = sheet.get_values(table_range)

        if not data:
            return None
        
        headers = data[0]
        rows = data[1:]
        all_rows = []
        for row in rows:
            row_dict = dict(zip(headers, row))
            all_rows.append(row_dict)
        return all_rows

    # def __set_table_column_val(self, spreadsheet_name, sheet_name, table_range, new_value):

    def get_possible_auth_code(self) -> list:   
        table_details = self.convert_LUT('Auth_Code')
        table_val = self.__get_table_column_val(table_details["spreadsheet_name"], table_details["sheet_name"], table_details["col"])
        auth_codes = []
        for row in table_val:
            auth_codes.append(row["Auth Key"])
        return auth_codes

    def convert_LUT(self,target_name) -> str:
        csv_filename = "Sheet_LUT.csv"
        csv_filepath = os.path.join(cwd, csv_filename)

        try:
            df = pd.read_csv(csv_filepath)
            df.columns = df.columns.str.strip()
            result = df[df['table'].str.strip() == target_name]
            if not result.empty:
                return result.iloc[0].to_dict()
        except FileNotFoundError:
            print(f"Error: File not found at {csv_filepath}")
        return None
    
    def get_f1_75(self):
       table_details = self.convert_LUT('F1_75')
       table_val = self.__get_table_column_val(table_details["spreadsheet_name"], table_details["sheet_name"], table_details["col"])
       return table_val

    def get_f2_85(self):
       table_details = self.convert_LUT('F2_85')
       table_val = self.__get_table_column_val(table_details["spreadsheet_name"], table_details["sheet_name"], table_details["col"])
       return table_val
    
    def get_markforged(self):
       table_details = self.convert_LUT('Markforged')
       table_val = self.__get_table_column_val(table_details["spreadsheet_name"], table_details["sheet_name"], table_details["col"])
       return table_val
    
    def getAllFilaments(self):
        all_filaments = []
        all_filaments.append(self.get_f1_75())
        all_filaments.append(self.get_f2_85())
        all_filaments.append(self.get_markforged())
        return all_filaments

if __name__ == "__main__":
    sheet = sheet_API()
    print(sheet.get_possible_auth_code())
    print(sheet.get_f1_75())