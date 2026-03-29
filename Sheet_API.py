import gspread
import pandas as pd
import os
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

from Testing.Bath_Cost_Code import Calculate_Personal_Cost

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

    def add_personal_print_credit(self, Bath_ID, Weight, AuthCode):
        table_details = self.convert_LUT('Credit_Tracker')
        
        sheet = self.client.open(table_details["spreadsheet_name"]).worksheet(table_details["sheet_name"])
        col = table_details["col"].split(":")
        
        start_col = col[0]
        end_col = col[1]

        row_values = len(sheet.col_values(1))
        date = datetime.now().strftime("%d/%m/%Y")
        date = "'"+str(date) # Ensure date is treated as text in Google Sheets

        Value = Calculate_Personal_Cost(Weight)

        AuthCode = "'"+AuthCode # Ensure AuthCode is treated as text in Google Sheets
        AUTHORISER_FORMULA = f"=VLOOKUP(F{row_values + 1},'Committee/Volunteer'!D:F,2,FALSE)"

        new_row_data = [date, Bath_ID, Weight, Value, AUTHORISER_FORMULA, AuthCode]
        target_range = f"{start_col}{row_values + 1}:{end_col}{row_values + 1}"

        sheet.update(range_name=target_range, values=[new_row_data],value_input_option='USER_ENTERED')
        print(f"Successfully added row to {table_details['sheet_name']} at {target_range}")

    def add_loan_out_entry(self, Bath_ID, Item, AuthCode):
        

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
    sheet.add_personal_print_credit("IL356", 100, "9408")
    # print(sheet.get_f1_75())