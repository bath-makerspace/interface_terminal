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

    def add_personal_print_credit(self, Bath_ID, Weight, AuthCode=""):
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

        if AuthCode == "'" or AuthCode is None:
            pending_table_details = self.convert_LUT('Pending_Payment')
            pending_sheet = self.client.open(pending_table_details["spreadsheet_name"]).worksheet(pending_table_details["sheet_name"])
            pending_pay_table = self.__get_table_column_val(pending_table_details["spreadsheet_name"], pending_table_details["sheet_name"], pending_table_details["col"])
            for index,item in enumerate(pending_pay_table):
                if item["Bath ID"] == Bath_ID:
                    pending_row = index + 2 # +1, for header, +1 because index starts at 0
                    pending_target_range = f"{pending_table_details['col'].split(':')[0]}{pending_row}:{pending_table_details['col'].split(':')[1]}{pending_row}"
                    weight = int(item["Weight"]) + Weight
                    Value = float(item["Value"]) + Value
                    Row_in_Print_Credit = item["Row_in_Printing_Credit"] + "," + str(row_values + 1)
                    new_pending_data = [Bath_ID, weight, Value, Row_in_Print_Credit]
                    pending_sheet.update(range_name=pending_target_range, values=[new_pending_data],value_input_option='USER_ENTERED')
                    print(f"Successfully added row to {pending_table_details['sheet_name']} at {pending_target_range}")
                    return
            pending_target_range = f"{pending_table_details['col'].split(':')[0]}{len(pending_sheet.col_values(1))+1}:{pending_table_details['col'].split(':')[1]}{len(pending_sheet.col_values(1))+1}"
            pending_sheet.update(range_name=pending_target_range, values=[[Bath_ID, Weight, Value,str(row_values + 1)]],value_input_option='USER_ENTERED')

    def add_loan_out_entry(self, Bath_ID, Item_Category, Item, AuthCode):
        on_loan_table_details = self.convert_LUT('Loan_Out')
        pending_table_details = self.convert_LUT('Pending')
        inventory_table_details = self.convert_LUT(Item_Category)

        on_loan_sheet = self.client.open(on_loan_table_details["spreadsheet_name"]).worksheet(on_loan_table_details["sheet_name"])
        pending_sheet = self.client.open(pending_table_details["spreadsheet_name"]).worksheet(pending_table_details["sheet_name"])
        inventory_sheet = self.client.open(inventory_table_details["spreadsheet_name"]).worksheet(inventory_table_details["sheet_name"])

        on_loan_col = on_loan_table_details["col"].split(":")
        on_loan_start_col = on_loan_col[0]
        on_loan_end_col = on_loan_col[1]
        on_loan_row_values = len(on_loan_sheet.col_values(1))
        Row_In_OnLoan = on_loan_row_values + 1

        pending_col = pending_table_details["col"].split(":")
        pending_start_col = pending_col[0]
        pending_end_col = pending_col[1]
        pending_row_values = len(pending_sheet.col_values(1))

        inventory_col = inventory_table_details["col"].split(":")
        inventory_start_col = inventory_col[0]
        inventory_end_col = inventory_col[1]

        date = datetime.now().strftime("%d/%m/%Y")
        date = "'"+str(date) # Ensure date is treated as text in Google Sheets

        AuthCode = "'"+AuthCode # Ensure AuthCode is treated as text in Google Sheets
        Loan_AUTHORISER_FORMULA     = f"=VLOOKUP({on_loan_end_col}{on_loan_row_values + 1},'Committee/Volunteer'!D:F,2,FALSE)"

        # Creating Payload for On Loan Sheet and sending it to Google Sheets
        new_on_loan_data = [date, Bath_ID, Item_Category, Item, Loan_AUTHORISER_FORMULA, AuthCode]
        on_loan_target_range = f"{on_loan_start_col}{on_loan_row_values + 1}:{on_loan_end_col}{on_loan_row_values + 1}"
        on_loan_sheet.update(range_name=on_loan_target_range, values=[new_on_loan_data],value_input_option='USER_ENTERED')
        print(f"Successfully added row to {on_loan_table_details['sheet_name']} at {on_loan_target_range}")

        # Creating Payload for Pending Sheet and sending it to Google Sheets
        new_pending_data = [date, Bath_ID, Item_Category, Item, Row_In_OnLoan]
        pending_target_range = f"{pending_start_col}{pending_row_values + 1}:{pending_end_col}{pending_row_values + 1}"
        pending_sheet.update(range_name=pending_target_range, values=[new_pending_data],value_input_option='USER_ENTERED')
        print(f"Successfully added row to {pending_table_details['sheet_name']} at {pending_target_range}")

        # Update Inventory Sheet to be on Loan
        inventory_table = self.__get_table_column_val(inventory_table_details["spreadsheet_name"], inventory_table_details["sheet_name"], inventory_table_details["col"])
        for index, item in enumerate(inventory_table):
            if item["Item Name"] == Item:
                inventory_row = index + 2 # +1, for header, +1 because index starts at 0
                Inventory_AUTHORISER_FORMULA = f"=VLOOKUP({inventory_end_col}{inventory_row},'Committee/Volunteer'!D:F,2,FALSE)"
                inventory_target_range = f"{inventory_start_col}{inventory_row}:{inventory_end_col}{inventory_row}"
                new_inventory_data = [Item, item["Item Type"], "On Loan", Inventory_AUTHORISER_FORMULA, AuthCode]
                inventory_sheet.update(range_name=inventory_target_range, values=[new_inventory_data],value_input_option='USER_ENTERED')
                print(f"Successfully updated {Item} status to On Loan in {inventory_table_details['sheet_name']} at {inventory_target_range}")
                break

    def get_pending_loans(self):
        table_details = self.convert_LUT('Pending_Loan')
        table_val = self.__get_table_column_val(table_details["spreadsheet_name"], table_details["sheet_name"], table_details["col"])
        return table_val
    
    def get_pending_payments(self):
        table_details = self.convert_LUT('Pending_Payment')
        table_val = self.__get_table_column_val(table_details["spreadsheet_name"], table_details["sheet_name"], table_details["col"])
        return table_val
    
    def complete_pending_payment(self, Bath_ID, AuthCode):
        pending_payment_details = self.convert_LUT('Pending_Payment')
        pending_payment_sheet = self.client.open(pending_payment_details["spreadsheet_name"]).worksheet(pending_payment_details["sheet_name"])
        pending_payment_table = self.__get_table_column_val(pending_payment_details["spreadsheet_name"], pending_payment_details["sheet_name"], pending_payment_details["col"])
        pending_payment_sheet.delete_rows(2)
        # for index, item in enumerate(pending_payment_table):
        #     if item["Bath ID"] == Bath_ID:
        #         pending_row = index + 2 # +1, for header, +1 because index starts at 0
        #         pending_target_range = f"{pending_payment_details['col'].split(':')[0]}{pending_row}:{pending_payment_details['col'].split(':')[1]}{pending_row}"
        #         pending_payment_sheet.update(range_name=pending_target_range, values=[[item["Bath ID"], item["Weight"], item["Value"], item["Row_in_Printing_Credit"], AuthCode]],value_input_option='USER_ENTERED')
        #         print(f"Successfully completed pending payment for {Bath_ID} in {pending_payment_details['sheet_name']} at {pending_target_range}")
        #         return

    def add_loan_in_entry(self, Bath_ID, Item, AuthCode):
        pass


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

    def get_equipment_inventory(self, category):
        table_details = self.convert_LUT(category)
        table_val = self.__get_table_column_val(table_details["spreadsheet_name"], table_details["sheet_name"], table_details["col"])
        return table_val

if __name__ == "__main__":
    sheet = sheet_API()
    sheet.add_personal_print_credit("IL356", 11)
    sheet.add_personal_print_credit("IL356", 40, "9408")
    sheet.add_loan_out_entry("IL356", "IT_Inventory", "Raspberry Pi Zero 2W #1", "9408")
    print(sheet.get_pending_payments())
    sheet.complete_pending_payment("IL356", "9408")
    # sheet.add_loan_out_entry("IL356", "IT_Inventory", "Raspberry Pi Zero 2W #1", "9408")
    