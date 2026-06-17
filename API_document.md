# Documentation of API
Created by: Ian-Lim-Collab
<br>
<br>
Documentation code for backend API on the Makerspace Interface Terminal.

## Table of Contents
- [Common Errors](#common-errors)
- [Sheet_LUT.csv Reference](#sheet_lutcsv-reference)
- [API Functions](#api-functions)
  - [Printing Credit](#printing-credit-functions)
  - [Equipment Loans](#equipment-loan-functions)
  - [Filament & Inventory](#filament--inventory-functions)
  - [Lookup & Authorisation](#lookup--authorisation-functions)
  - [Cost Calculation (Bath_Cost_Code.py)](#cost-calculation-functions)
- [Internal Helper Functions](#internal-helper-functions)

## Common Errors
| Error | Where it occurs | Cause |
|:---|:---|:---|
| `TypeError: 'NoneType' object is not subscriptable` | Any function calling `convert_LUT` | `convert_LUT` returns `None` if the requested key isn't found in `Sheet_LUT.csv`, or if the CSV file itself can't be found. The calling function then tries to index the `None` result. |
| `NameError` | `add_personal_print_credit` | Raised deliberately when a committee/volunteer member supplies an `AuthCode` that matches their own index in the committee list (i.e. attempting to self-authorise their own print). |
| `RuntimeError: No active exception to re-raise` | `add_personal_markforged_credit` | The self-authorisation check here uses a bare `raise` outside of an `except` block instead of raising `NameError` like its counterpart above. This is a known inconsistency — see the function entry below. |
| `ValueError: '<code>' is not in list` | `add_personal_print_credit`, `add_personal_markforged_credit` | Raised if `Bath_ID` is in the committee list but the `AuthCode` provided doesn't exist in `get_possible_auth_code()`. |
| `ValueError` (returns `0.0` instead) | `Calculate_Personal_Cost` | Caught internally — returns `0.0` if `Weight_String` cannot be converted to an integer. |
| `ValueError` / `TypeError` (returns `0.0` instead) | `calculate_markforged_cost` | Caught internally — returns `0.0` if `onyx_cc`, `fiber_cc`, or `hours` cannot be converted to a float. |
| `ValueError: Invalid column string` | `__col_to_num` | Raised if a column letter outside `A`–`Z` is passed in. |
| `FileNotFoundError` (printed, not raised) | `convert_LUT` | Printed to console if `Sheet_LUT.csv` isn't found at the expected path relative to the current working directory; function then returns `None`. |

## Sheet_LUT.csv Reference
`Sheet_LUT.csv` is the local lookup table that maps a logical key (used throughout the codebase) to the physical Google Sheet, worksheet tab, and column range it lives in. Every function that reads from or writes to a Google Sheet resolves its target through this file via `convert_LUT`.

| table (key) | spreadsheet_name | sheet_name | col |
|:---|:---|:---|:---|
| F1_75 | Inventory | Filament | A:F |
| F2_85 | Inventory | Filament | H:M |
| Markforged | Inventory | Filament | O:Q |
| IT_Inventory | Inventory | Equipment Inventory | A:E |
| Mechanical_tools | Inventory | Equipment Inventory | G:L |
| Electronics_Equipment | Inventory | Equipment Inventory | N:T |
| Laser_Printer_Equip | Inventory | Equipment Inventory | V:AA |
| Auth_Code | Committee Info | Committee/Volunteer | D:D |
| Username | Committee Info | Committee/Volunteer | B:B |
| Credit_Tracker | GUI_Credit Tracker | Printing Credit | A:G |
| Credit_AuthCode | GUI_Credit Tracker | Printing Credit | G:G |
| Loan_Out | GUI_Credit Tracker | On Loan | A:F |
| Loan_In | GUI_Credit Tracker | On Loan | G:H |
| Pending_Loan | GUI_Credit Tracker | Pending | A:E |
| Pending_Payment | GUI_Credit Tracker | Pending | G:J |

> Note: adding a new equipment category, filament type, or sheet tab only requires a new row here — no code changes are needed elsewhere, since every function looks up its target by key.

## API Functions

### Printing Credit Functions

#### add_personal_print_credit
```Python
def add_personal_print_credit(self, Bath_ID:str, Weight:int, AuthCode:str="", Signature_path:str="")
```
Records a manual filament print transaction. Calculates the cost via `Calculate_Personal_Cost`, applies the committee/volunteer discount where applicable, uploads the user's signature image to Google Drive and embeds it in the sheet, and — if no `AuthCode` is supplied — queues the print in the Pending Payment sheet for later sign-off (merging with any existing pending row for that user).

| Item | Format | Details |
|:---|:---- | :---|
| Bath_ID | String | The university username (i.e. IL356) |
| Weight | Integer | The weight of the 3d print |
| AuthCode | String | This is an <i><b>optional</b></i> value used to indicated that the transaction has been approved by a trusted member |
| Signature_Path| String | The path(technically the filename) where signature of the user printing|

##### Dependencies
| Files | File location | Relationship |
|:---|:---|:---|
| GUI_Credit Tracker | Google Drive (Sheet) | The Google Sheet that tracks the value |
| Committee Info | Google Drive (Sheet) | The Google Sheet that tracks committee/volunteer information |
| Sheet_LUT.csv | Codebase | The local csv file used for storing values relating to the google sheet(i.e. Sheet Name, Column to file, etc) |

| Function | Function Filename | Relationship |
| :---| :---| :---|
| convert_LUT | Sheet_API.py | function to Look up data from <b><i>"Sheet_LUT.csv"</i></b> using a key |
| Calculate_Personal_Cost | Bath_Cost_Code.py | This function centralise function used to calculate the monetary cost of the 3D print |
| get_possible_committee_users | Sheet_API.py | used to determine if a committee discount is required and ensure the rule of 2 |
| get_possible_auth_code | Sheet_API.py | used to determine if Auth Code provided is valid |
| \_\_apply_volunteer_committee_discount | Sheet_API.py | applies the fixed committee/volunteer discount to the calculated cost |
| \_\_upload_image_to_drive | Sheet_API.py | uploads the signature image and returns a public link for embedding |

---

#### add_personal_markforged_credit
```Python
def add_personal_markforged_credit(self, Bath_ID: str, Price: str, AuthCode: str = "", Signature_path: str = "")
```
Records a Markforged (composite/fibre-reinforced) print transaction. Unlike `add_personal_print_credit`, the cost is supplied directly via `Price` rather than derived from a weight — it's expected to be the output of `calculate_markforged_cost`. The Weight column for these rows is hardcoded to `777`, used as a flag value to mark the row as a Markforged entry rather than a standard FDM print. Applies the same committee discount and pending-payment queuing logic as `add_personal_print_credit`.

| Item | Format | Details |
|:---|:---- | :---|
| Bath_ID | String | The university username (i.e. IL356) |
| Price | String/Float | The pre-calculated cost of the print, typically the return value of `calculate_markforged_cost` |
| AuthCode | String | This is an <i><b>optional</b></i> value used to indicate that the transaction has been approved by a trusted member |
| Signature_Path | String | The path (technically the filename) where the signature of the user printing is stored |

> **Known issue:** the self-authorisation check (when a committee member's own `AuthCode` matches their own index) ends in a bare `raise` with no active exception to re-raise, which produces a `RuntimeError` rather than the `NameError` used in `add_personal_print_credit`. The line directly after it is unreachable and should be removed for consistency.

##### Dependencies
| Files | File location | Relationship |
|:---|:---|:---|
| GUI_Credit Tracker | Google Drive (Sheet) | The Google Sheet that tracks the value |
| Committee Info | Google Drive (Sheet) | The Google Sheet that tracks committee/volunteer information |
| Sheet_LUT.csv | Codebase | The local csv file used for storing values relating to the google sheet |

| Function | Function Filename | Relationship |
| :---| :---| :---|
| convert_LUT | Sheet_API.py | function to Look up data from "Sheet_LUT.csv" using a key |
| calculate_markforged_cost | Bath_Cost_Code.py | Intended source of the `Price` argument (not called directly by this function) |
| get_possible_committee_users | Sheet_API.py | used to determine if a committee discount is required |
| get_possible_auth_code | Sheet_API.py | used to determine if Auth Code provided is valid |
| \_\_upload_image_to_drive | Sheet_API.py | uploads the signature image and returns a public link for embedding |

---

#### get_pending_payments
```Python
def get_pending_payments(self)
```
Returns every row currently in the Pending Payment sheet, i.e. all print transactions awaiting committee sign-off.

| Item | Format | Details |
|:---|:----|:---|
| *(no parameters)* | — | — |

**Returns:** `list[dict]` — one dictionary per pending row, keyed by column header.

##### Dependencies
| Files | File location | Relationship |
|:---|:---|:---|
| GUI_Credit Tracker | Google Drive (Sheet) | Source of the Pending sheet data |
| Sheet_LUT.csv | Codebase | Resolves the Pending_Payment key to its sheet/range |

| Function | Function Filename | Relationship |
| :---| :---| :---|
| convert_LUT | Sheet_API.py | Resolves the `Pending_Payment` key |
| \_\_get_table_column_val | Sheet_API.py | Reads the resolved range and returns it as row dictionaries |

---

#### complete_pending_payment
```Python
def complete_pending_payment(self, Bath_ID:str, AuthCode:str)
```
Finalises a pending print payment for a given user. Clears that user's row from the Pending Payment sheet, then writes the supplied `AuthCode` into every individual row referenced in that pending entry's `Row_in_Printing_Credit` field, retroactively marking each of those print transactions as authorised.

| Item | Format | Details |
|:---|:----|:---|
| Bath_ID | String | The university username whose pending payment is being completed |
| AuthCode | String | The authorisation code applied retroactively to the relevant print rows |

##### Dependencies
| Files | File location | Relationship |
|:---|:---|:---|
| GUI_Credit Tracker | Google Drive (Sheet) | Holds both the Pending and Printing Credit sheets being updated |
| Sheet_LUT.csv | Codebase | Resolves the Pending_Payment and Credit_AuthCode keys |

| Function | Function Filename | Relationship |
| :---| :---| :---|
| convert_LUT | Sheet_API.py | Resolves the relevant sheet/range keys |
| \_\_get_table_column_val | Sheet_API.py | Reads the Pending Payment table to find the matching row |
| \_\_col_to_num | Sheet_API.py | Converts column letters to numeric indices where needed |

### Equipment Loan Functions

#### add_loan_out_entry
```Python
def add_loan_out_entry(self, Bath_ID:str, Item_Category:str, Item:str, AuthCode:str)
```
Logs an equipment loan-out. Adds a new record to the On Loan sheet and a matching record to the Pending sheet (so the loan can later be checked back in), then updates the relevant inventory row's Location to `"On Loan"`.

| Item | Format | Details |
|:---|:----|:---|
| Bath_ID | String | The university username borrowing the item |
| Item_Category | String | The `Sheet_LUT.csv` key for the inventory category (e.g. `IT_Inventory`, `Mechanical_tools`) |
| Item | String | The exact `Item Name` of the equipment being loaned, as it appears in the inventory sheet |
| AuthCode | String | The approval code from the committee/volunteer authorising the loan |

##### Dependencies
| Files | File location | Relationship |
|:---|:---|:---|
| GUI_Credit Tracker | Google Drive (Sheet) | Holds the On Loan and Pending sheets being written to |
| Inventory | Google Drive (Sheet) | Holds the Equipment Inventory sheet being updated |
| Sheet_LUT.csv | Codebase | Resolves Loan_Out, Pending_Loan, and the relevant inventory category key |

| Function | Function Filename | Relationship |
| :---| :---| :---|
| convert_LUT | Sheet_API.py | Resolves the relevant sheet/range keys |
| \_\_get_table_column_val | Sheet_API.py | Reads the inventory table to find the matching item row |
| \_\_col_to_num | Sheet_API.py | Converts column letters to numeric indices for row counting |

---

#### add_loan_in_entry
```Python
def add_loan_in_entry(self, Bath_ID:str, Item_Category:str, Item:str, AuthCode:str)
```
Logs the return of previously loaned equipment. Clears the matching row from the Pending sheet, writes the authoriser/`AuthCode` into the corresponding On Loan sheet row, and updates the inventory row's Location back to `"Makerspace (Lab)"`.

| Item | Format | Details |
|:---|:----|:---|
| Bath_ID | String | The university username returning the item |
| Item_Category | String | The `Sheet_LUT.csv` key for the inventory category |
| Item | String | The exact `Item Name` of the equipment being returned |
| AuthCode | String | The approval code from the committee/volunteer confirming the return |

##### Dependencies
| Files | File location | Relationship |
|:---|:---|:---|
| GUI_Credit Tracker | Google Drive (Sheet) | Holds the On Loan and Pending sheets being updated |
| Inventory | Google Drive (Sheet) | Holds the Equipment Inventory sheet being updated |
| Sheet_LUT.csv | Codebase | Resolves Loan_In, Pending_Loan, and the relevant inventory category key |

| Function | Function Filename | Relationship |
| :---| :---| :---|
| convert_LUT | Sheet_API.py | Resolves the relevant sheet/range keys |
| \_\_get_table_column_val | Sheet_API.py | Reads the Pending and Inventory tables to find matching rows |

---

#### get_pending_loans
```Python
def get_pending_loans(self)
```
Returns every row currently in the Pending sheet's loan section, i.e. all equipment currently on loan and awaiting return.

| Item | Format | Details |
|:---|:----|:---|
| *(no parameters)* | — | — |

**Returns:** `list[dict]` — one dictionary per pending loan row.

##### Dependencies
| Files | File location | Relationship |
|:---|:---|:---|
| GUI_Credit Tracker | Google Drive (Sheet) | Source of the Pending sheet data |
| Sheet_LUT.csv | Codebase | Resolves the Pending_Loan key |

| Function | Function Filename | Relationship |
| :---| :---| :---|
| convert_LUT | Sheet_API.py | Resolves the `Pending_Loan` key |
| \_\_get_table_column_val | Sheet_API.py | Reads the resolved range and returns it as row dictionaries |

### Filament & Inventory Functions

#### get_f1_75 / get_f2_85 / get_markforged
```Python
def get_f1_75(self)
def get_f2_85(self)
def get_markforged(self)
```
Each returns every row of its corresponding material table from the Inventory sheet's Filament tab: `get_f1_75` for 1.75mm FDM filament, `get_f2_85` for 2.85mm FDM filament, and `get_markforged` for Markforged composite material reels.

| Item | Format | Details |
|:---|:----|:---|
| *(no parameters)* | — | — |

**Returns:** `list[dict]` — one dictionary per material row.

##### Dependencies
| Files | File location | Relationship |
|:---|:---|:---|
| Inventory | Google Drive (Sheet) | Source of the Filament tab data |
| Sheet_LUT.csv | Codebase | Resolves the F1_75 / F2_85 / Markforged keys |

| Function | Function Filename | Relationship |
| :---| :---| :---|
| convert_LUT | Sheet_API.py | Resolves the relevant material key |
| \_\_get_table_column_val | Sheet_API.py | Reads the resolved range and returns it as row dictionaries |

---

#### getAllFilaments
```Python
def getAllFilaments(self)
```
Convenience wrapper that calls `get_f1_75`, `get_f2_85`, and `get_markforged` in order, returning their combined results.

| Item | Format | Details |
|:---|:----|:---|
| *(no parameters)* | — | — |

**Returns:** `list[list[dict]]` — a 3-element list: `[F1.75 rows, F2.85 rows, Markforged rows]`.

##### Dependencies
| Function | Function Filename | Relationship |
| :---| :---| :---|
| get_f1_75 | Sheet_API.py | Provides the 1.75mm filament rows |
| get_f2_85 | Sheet_API.py | Provides the 2.85mm filament rows |
| get_markforged | Sheet_API.py | Provides the Markforged material rows |

---

#### get_equipment_inventory
```Python
def get_equipment_inventory(self, category)
```
Returns every row for the given equipment category from the Inventory sheet's Equipment Inventory tab.

| Item | Format | Details |
|:---|:----|:---|
| category | String | The `Sheet_LUT.csv` key for the equipment category (e.g. `IT_Inventory`, `Mechanical_tools`, `Electronics_Equipment`, `Laser_Printer_Equip`) |

**Returns:** `list[dict]` — one dictionary per equipment row.

##### Dependencies
| Files | File location | Relationship |
|:---|:---|:---|
| Inventory | Google Drive (Sheet) | Source of the Equipment Inventory tab data |
| Sheet_LUT.csv | Codebase | Resolves the requested category key |

| Function | Function Filename | Relationship |
| :---| :---| :---|
| convert_LUT | Sheet_API.py | Resolves the category key |
| \_\_get_table_column_val | Sheet_API.py | Reads the resolved range and returns it as row dictionaries |

---

#### get_available_equipment_inventory
```Python
def get_available_equipment_inventory(self, catergory)
```
Filters `get_equipment_inventory` results down to items whose `Location` is not `"On Loan"` — i.e. items currently available to borrow.

| Item | Format | Details |
|:---|:----|:---|
| catergory | String | The `Sheet_LUT.csv` key for the equipment category *(parameter name as written in code)* |

**Returns:** `list[dict]` — filtered list of available equipment rows.

##### Dependencies
| Function | Function Filename | Relationship |
| :---| :---| :---|
| get_equipment_inventory | Sheet_API.py | Provides the unfiltered category rows to filter |

### Lookup & Authorisation Functions

#### convert_LUT
```Python
def convert_LUT(self, target_name:str) -> str
```
Looks up a single row in `Sheet_LUT.csv` whose `table` column matches `target_name`, returning the spreadsheet name, sheet/tab name, and column range as a dictionary. This is the central resolver used by almost every other method to find which physical Google Sheet and range to read or write.

| Item | Format | Details |
|:---|:----|:---|
| target_name | String | The logical table key, matching a value in the `table` column of `Sheet_LUT.csv` (e.g. `"Credit_Tracker"`, `"Auth_Code"`, `"F1_75"`) |

**Returns:** `dict` with keys `table`, `spreadsheet_name`, `sheet_name`, `col` — or `None` if the key isn't found, or if `Sheet_LUT.csv` can't be located.

##### Dependencies
| Files | File location | Relationship |
|:---|:---|:---|
| Sheet_LUT.csv | Codebase | The data source being queried |

---

#### get_possible_auth_code
```Python
def get_possible_auth_code(self) -> list
```
Returns the cached list of valid committee/volunteer auth codes, loaded once when the `sheet_API` object is constructed.

| Item | Format | Details |
|:---|:----|:---|
| *(no parameters)* | — | — |

**Returns:** `list[str]` — valid Auth Keys.

> Note: this list is cached at `__init__` time via `__get_possible_online_auth_code`. Changes made to the Committee Info sheet after the `sheet_API` object is created won't be reflected until a new instance is created.

##### Dependencies
| Function | Function Filename | Relationship |
| :---| :---| :---|
| \_\_get_possible_online_auth_code | Sheet_API.py | Populates the cached list at construction time |

---

#### get_possible_committee_users
```Python
def get_possible_committee_users(self) -> list
```
Returns the cached list of committee/volunteer usernames, loaded once when the `sheet_API` object is constructed.

| Item | Format | Details |
|:---|:----|:---|
| *(no parameters)* | — | — |

**Returns:** `list[str]` — committee/volunteer usernames.

> Note: same caching behaviour as `get_possible_auth_code` — the list reflects the Committee Info sheet's state at the time the object was created.

##### Dependencies
| Function | Function Filename | Relationship |
| :---| :---| :---|
| \_\_get_possible_online_committee_users | Sheet_API.py | Populates the cached list at construction time |

### Cost Calculation Functions
*(Bath_Cost_Code.py)*

#### Calculate_Personal_Cost
```Python
def Calculate_Personal_Cost(Weight_String: str) -> float
```
Converts a 3D print's weight in grams into a monetary cost, using a two-tier pricing model: £0.06/gram for the first 70g, then £0.04/gram for any weight above that threshold.

| Item | Format | Details |
|:---|:----|:---|
| Weight_String | String | The print weight in grams, typically passed as text straight from a GUI Entry box |

**Returns:** `float` — cost rounded to 2 decimal places, or `0.0` if `Weight_String` isn't a valid integer.

##### Pricing constants
| Constant | Value |
|:---|:---|
| tier_1_threshold | 70 g |
| tier_1_cost_per_gram | £0.06 |
| tier_2_cost_per_gram | £0.04 |

---

#### calculate_markforged_cost
```Python
def calculate_markforged_cost(onyx_cc, fiber_type, fiber_cc, hours)
```
Calculates the total cost of a Markforged print from volumetric material usage and print time, with a 40% markup applied to the combined total. Intended to feed the `Price` argument of `add_personal_markforged_credit`.

| Item | Format | Details |
|:---|:----|:---|
| onyx_cc | Float/Int | Volume (cc) of base Onyx material used |
| fiber_type | String | One of `"Carbon Fibre"`, `"Kevlar"`, or `"None"` |
| fiber_cc | Float/Int | Volume (cc) of reinforcement fibre used |
| hours | Float/Int | Total print time in hours |

**Returns:** `float` — total cost rounded to 2 decimal places, or `0.0` if any input can't be converted to a number.

##### Pricing constants
| Constant | Value |
|:---|:---|
| ONYX_PRICE_PER_CC | £0.24 |
| CARBON_FIBER_PRICE_PER_CC | £2.22 |
| KEVLAR_PRICE_PER_CC | £1.48 |
| TIME_PRICE_PER_HOUR | £0.90 |
| Markup | ×1.4 applied to (materials + time) |

## Internal Helper Functions
The following are private methods (name-mangled with a leading double underscore) on the `sheet_API` class. They aren't called directly from the GUI layer, but are documented here since several public functions above depend on them.

| Function | Purpose |
|:---|:---|
| \_\_get_service(self, cred_file) | Authenticates with Google via OAuth (`token.json` / `credentials.json`) and returns a Google Drive v3 API service object, used for signature uploads. |
| \_\_get_table_column_val(self, spreadsheet_name, sheet_name, table_range) | Generic reader — fetches a column range from a worksheet and returns it as a list of `{header: value}` dictionaries, one per row. |
| \_\_col_to_num(self, col_str) | Converts a spreadsheet column letter (e.g. `"AA"`) into its 1-indexed numeric column position. |
| \_\_upload_image_to_drive(self, image_path) | Uploads a local signature image to the shared Google Drive signature folder (`FOLDER_ID`), sets it to publicly readable, and returns a direct download link. |
| \_\_apply_volunteer_committee_discount(self, value) | Applies the fixed 10% committee/volunteer discount to a given cost value. |
| \_\_get_possible_online_auth_code(self) | Fetches the current list of valid Auth Keys from the Committee Info sheet. Called once at `__init__`. |
| \_\_get_possible_online_committee_users(self) | Fetches the current list of committee/volunteer usernames from the Committee Info sheet. Called once at `__init__`. |
