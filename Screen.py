import tkinter as tk
from tkinter import ttk
import random
from PIL import Image, ImageDraw, ImageTk, ImageEnhance
import csv
import sv_ttk
import os
import subprocess
from tkinter import messagebox
from datetime import datetime
from Bath_Cost_Code import Calculate_Personal_Cost
from Bath_Cost_Code import calculate_markforged_cost
from Sheet_API import sheet_API

sheet = sheet_API()

class App(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Makerspace Information Terminal")
        self.geometry("1024x600")

        self.kb_process = None
        self.current_frame = None
        self.switch_frame(StartScreen)

        

    def switch_frame(self, frame_class):
        self.close_keyboard()
        if self.current_frame is not None:
            self.current_frame.destroy()
        self.current_frame = frame_class(self)
        self.current_frame.pack(fill="both", expand=True)

        # Bind clicking on the background of the NEW frame to close the keyboard
        self.current_frame.bind("<Button-1>", lambda e: self.close_keyboard())

    def open_keyboard(self, mode="full"):
        self.close_keyboard()
        env = os.environ.copy()

        if mode == "numeric":
            args = ["wvkbd-mobintl", "-L", "250", "-l", "dialer"]
        else:
            args = ["wvkbd-mobintl", "-L", "250"]

        try:
            self.kb_process = subprocess.Popen(args, env=env)
        except FileNotFoundError:
            print("Keyboard not found.")

    def close_keyboard(self, event=None):
        """Kills keyboard and removes focus from widgets."""
        subprocess.run(["pkill", "wvkbd-mobintl"], stderr=subprocess.DEVNULL)
        if self.kb_process:
            self.kb_process.terminate()
            self.kb_process = None

        # This removes the blinking cursor from any text box
        self.focus_set()

    def get_loaned_items(self):
        """Returns items currently 'LOANED' based on the 6-column format."""
        loaned_items = set()
        if os.path.exists("loans.csv"):
            with open("loans.csv", "r") as f:
                reader = csv.reader(f)
                for row in reader:
                    # Indexing: 0:Time, 1:User, 2:Cat, 3:Item, 4:Status, 5:Auth
                    if len(row) >= 5:
                        item = row[3]
                        status = row[4]
                        if status == "LOANED":
                            loaned_items.add(item)
                        elif status == "RETURNED":
                            loaned_items.discard(item)
        return loaned_items

    def get_unpaid_debts(self):
        """Returns rows from entries.csv where column 4 (Auth) is missing."""
        unpaid = sheet.get_pending_payments()
        
        return unpaid

class StartScreen(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master

        # 1. Create a Canvas that fills the whole frame
        # We set highlightthickness=0 so there is no border
        self.canvas = tk.Canvas(self, highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True)

        # 2. Add the Logo to the Canvas
        try:
            # We process the logo here once
            chance = random.randint(1,1000)
            if chance == 676:
                original_logo = Image.open("transparent_jpg_logo_final.jpg").convert("RGBA")
            else:
                original_logo = Image.open("transparent_png_logo_final.png").convert("RGBA")
            logo_resized = original_logo.resize((600, 600), Image.Resampling.LANCZOS)

            # Opacity logic (0.1 for 10% visibility)
            alpha = logo_resized.split()[3]
            alpha = ImageEnhance.Brightness(alpha).enhance(0.1)
            logo_resized.putalpha(alpha)

            self.bg_image = ImageTk.PhotoImage(logo_resized, master=self.master)

            # Place logo on canvas (relx=0.2, rely=0.5 as per your original)
            # 1024 * 0.2 = 205, 600 * 0.5 = 300
            self.canvas.create_image(205, 300, image=self.bg_image, anchor="center")
        except FileNotFoundError:
            print("Logo file not found.")

        # 3. Add the TRANSPARENT Title Text to the Canvas
        # Because it's drawn on the canvas, it has no background box!
        self.canvas.create_text(
            512, 80,  # Centered horizontally (1024/2), 80 pixels down
            text="Welcome To The Makerspace Information Terminal",
            font=("Arial", 28, "bold"),
            fill="black",  # Or "white" if you switch to dark mode
            justify="center"
        )

        # 4. Add the Buttons
        # Since buttons are complex, we "embed" them into the canvas
        btn1 = ttk.Button(self, text="3D Printing Service", style="Big.TButton",
                          command=lambda: master.switch_frame(PaymentChoiceScreen))
        btn2 = ttk.Button(self, text="Equipment Service", style="Big.TButton",
                          command=lambda: master.switch_frame(EquipChoiceScreen))

        # We create "windows" on the canvas to hold the buttons
        self.canvas.create_window(512, 230, window=btn1, width=400, height=120)
        self.canvas.create_window(512, 400, window=btn2, width=400, height=120)

class PaymentChoiceScreen(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)

        label = ttk.Label(self, text="", font=("Arial", 24))
        label.pack(pady=20)

        btn1 = ttk.Button(self, text="Add 3D Print Debt",
                         command=lambda: master.switch_frame(PaymentInputScreen))
        btn1.pack(ipadx=60, ipady=35, pady=15)

        btn2 = ttk.Button(self, text="Add Markforged Print Debt",
                         command=lambda: master.switch_frame(MarkforgedInputScreen))
        btn2.pack(ipadx=35, ipady=35, pady=15)

        btn3 = ttk.Button(self, text="Mark Debt As Paid",
                         command=lambda: master.switch_frame(PaymentUpdateScreen))
        btn3.pack(ipadx=60, ipady=35, pady=15)

        btn4 = ttk.Button(self, text="Back",
                         command=lambda: master.switch_frame(StartScreen))
        btn4.pack(ipadx=30, ipady=15, pady=10)

class PaymentInputScreen(ttk.Frame):
    canvaswidth = 400
    canvasheight = 250

    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.signed = False  # Track if the user has signed

        # Ensure the signatures folder exists so we don't crash on save
        if not os.path.exists("signatures"):
            os.makedirs("signatures")

        self.bind("<Button-1>", lambda e: self.master.close_keyboard())

        # 1. TOP TITLE
        ttk.Label(self, text="Add 3D Print Debt", font=("Arial", 24, "bold")).pack(pady=20)

        # 2. MAIN CONTENT AREA
        content_container = ttk.Frame(self)
        content_container.pack(fill="both", expand=True, padx=50)

        # --- LEFT COLUMN (Inputs) ---
        left_col = ttk.Frame(content_container)
        left_col.pack(side="left", fill="both", expand=True, padx=20)

        ttk.Label(left_col, text="Payee Username", font=("Arial", 12)).pack(anchor="w")
        self.username = ttk.Entry(left_col, font=("Arial", 14))
        self.username.pack(fill="x", pady=(0, 15))
        self.username.bind("<Button-1>", lambda e: self.master.open_keyboard(mode="full"))

        ttk.Label(left_col, text="Print Mass (nearest gram)", font=("Arial", 12)).pack(anchor="w")
        self.print_mass = ttk.Entry(left_col, font=("Arial", 14))
        self.print_mass.pack(fill="x", pady=(0, 15))
        self.print_mass.bind("<Button-1>", lambda e: self.master.open_keyboard(mode="numeric"))
        self.print_mass.bind("<Return>", self.handle_enter_key)

        ttk.Label(left_col, text="Authentication Key", font=("Arial", 12)).pack(anchor="w")
        ttk.Label(left_col, text="(Committee only - for if paying now)", font=("Arial", 10, "italic")).pack(anchor="w")
        self.auth_key = ttk.Entry(left_col, font=("Arial", 14))
        self.auth_key.pack(fill="x", pady=(0, 10))
        self.auth_key.bind("<Button-1>", lambda e: self.master.open_keyboard(mode="numeric"))

        self.cost_display = ttk.Label(left_col, text="Cost: £0.00", font=("Arial", 18, "bold"))
        self.cost_display.pack(pady=10)

        # --- RIGHT COLUMN (Signature) ---
        right_col = ttk.Frame(content_container)
        right_col.pack(side="left", fill="both", expand=True, padx=20)

        ttk.Label(right_col, text="Payee Signature", font=("Arial", 12)).pack()
        self.canvas = tk.Canvas(right_col, bg="white", width=self.canvaswidth, height=self.canvasheight,
                                relief="ridge", bd=2, highlightthickness=0)
        self.canvas.pack(pady=10)

        self.image = Image.new("RGB", (self.canvaswidth, self.canvasheight), "white")
        self.draw = ImageDraw.Draw(self.image)
        self.last_x, self.last_y = None, None

        self.canvas.bind("<B1-Motion>", self.paint)
        self.canvas.bind("<ButtonRelease-1>", self.reset_coords)
        ttk.Button(right_col, text="Clear Signature", command=self.clear).pack()

        # 3. BOTTOM BUTTON BAR
        btn_frame = ttk.Frame(self)
        btn_frame.pack(side="bottom", pady=40)

        ttk.Button(btn_frame, text="Confirm", style="Accent.TButton",
                   command=self.handle_save).pack(side="left", padx=20, ipadx=20, ipady=10)

        ttk.Button(btn_frame, text="Cancel",
                   command=lambda: self.master.switch_frame(StartScreen)).pack(side="left", padx=20, ipadx=20, ipady=10)

    def paint(self, event):
        if self.last_x and self.last_y:
            self.canvas.create_line(self.last_x, self.last_y, event.x, event.y,
                                    width=4, fill="black", capstyle=tk.ROUND, smooth=True)
            self.draw.line([self.last_x, self.last_y, event.x, event.y], fill="black", width=4)
            self.signed = True  # User has started drawing
        self.last_x, self.last_y = event.x, event.y

    def reset_coords(self, event):
        self.last_x, self.last_y = None, None

    def clear(self):
        self.canvas.delete("all")
        self.image = Image.new("RGB", (self.canvaswidth, self.canvasheight), "white")
        self.draw = ImageDraw.Draw(self.image)
        self.signed = False  # Reset signature status

    def handle_enter_key(self, event):
        self.update_price()
        self.master.close_keyboard()

    def update_price(self):
        raw_val = self.print_mass.get()
        if raw_val:
            try:
                price = Calculate_Personal_Cost(raw_val)
                self.cost_display.config(text=f"Cost: £{float(price):.2f}")
                return price
            except ValueError:
                self.cost_display.config(text="Invalid Mass!")
        return 0

    def handle_save(self):
        user = self.username.get().strip()
        price = self.update_price()
        auth = self.auth_key.get().strip()

        # Validation
        auth_valid = (auth == "" or (len(auth) == 4 and auth.isdigit()))
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        if auth_valid and auth != "":
            auth_code_list = sheet.get_possible_auth_code()
            if auth in auth_code_list:
                auth_valid = True
            else:
                auth_valid = False

        if not user:
            messagebox.showwarning("Input Error", "Please fill in your username.")
        elif price <= 0:
            messagebox.showwarning("Input Error", "Please fill in your print mass.")
        elif not self.signed:
            messagebox.showwarning("Input Error", "Please add your signature.")
        elif not auth_valid:
            messagebox.showwarning("Input error", "Invalid authentication code.")
        else:
            # Save signature with unique timestamp
            filename = f"signatures/debt_{user}_{timestamp}.png"
            self.image.save(filename)
            sheet.add_personal_print_credit(Bath_ID=user, Weight=self.print_mass.get(), AuthCode=auth, Signature_path=filename)
            messagebox.showinfo("Thank you, have a nice day!", "Record logged successfully.")
            self.master.switch_frame(StartScreen)

class MarkforgedInputScreen(ttk.Frame):
    canvaswidth = 400
    canvasheight = 200  # Slightly shorter to fit extra inputs

    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.signed = False
        self.selected_fiber = "None"  # Default state

        if not os.path.exists("signatures"):
            os.makedirs("signatures")

        self.bind("<Button-1>", lambda e: self.master.close_keyboard())

        # 1. TOP TITLE
        ttk.Label(self, text="Add Markforged Print Debt", font=("Arial", 24, "bold")).pack(pady=10)

        # 2. MAIN CONTENT AREA
        content_container = ttk.Frame(self)
        content_container.pack(fill="both", expand=True, padx=40)

        # --- LEFT COLUMN (Inputs) ---
        left_col = ttk.Frame(content_container)
        left_col.pack(side="left", fill="both", expand=True, padx=20)

        # Username
        ttk.Label(left_col, text="Payee Username", font=("Arial", 11)).pack(anchor="w")
        self.username = ttk.Entry(left_col, font=("Arial", 14))
        self.username.pack(fill="x", pady=(0, 10))
        self.username.bind("<Button-1>", lambda e: self.master.open_keyboard(mode="full"))

        # Base Onyx Volume
        ttk.Label(left_col, text="Onyx CCs", font=("Arial", 11)).pack(anchor="w")
        self.onyx_vol = ttk.Entry(left_col, font=("Arial", 14))
        self.onyx_vol.pack(fill="x", pady=(0, 10))
        self.onyx_vol.bind("<Button-1>", lambda e: self.master.open_keyboard(mode="numeric"))

        # Fiber Selection Buttons
        ttk.Label(left_col, text="Select Reinforcement Fibre", font=("Arial", 11)).pack(anchor="w")
        fiber_frame = ttk.Frame(left_col)
        fiber_frame.pack(fill="x", pady=(0, 10))

        self.fiber_btns = {}
        for f_type in ["Carbon Fibre", "Kevlar", "None"]:
            btn = ttk.Button(fiber_frame, text=f_type,
                             command=lambda t=f_type: self.select_fiber(t))
            btn.pack(side="left", expand=True, fill="x", padx=2)
            self.fiber_btns[f_type] = btn

        # Fibre Volume & Print Time (Side-by-side)
        extra_info_frame = ttk.Frame(left_col)
        extra_info_frame.pack(fill="x")

        # Fibre CCs
        f_cc_frame = ttk.Frame(extra_info_frame)
        f_cc_frame.pack(side="left", expand=True, fill="x", padx=(0, 5))
        ttk.Label(f_cc_frame, text="Fibre CCs", font=("Arial", 10)).pack(anchor="w")
        self.fiber_vol = ttk.Entry(f_cc_frame, font=("Arial", 14))
        self.fiber_vol.pack(fill="x")
        self.fiber_vol.bind("<Button-1>", lambda e: self.master.open_keyboard(mode="numeric"))

        # Hours
        hr_frame = ttk.Frame(extra_info_frame)
        hr_frame.pack(side="left", expand=True, fill="x", padx=(5, 0))
        ttk.Label(hr_frame, text="Print Time (Hrs)", font=("Arial", 10)).pack(anchor="w")
        self.print_hrs = ttk.Entry(hr_frame, font=("Arial", 14))
        self.print_hrs.pack(fill="x")
        self.print_hrs.bind("<Button-1>", lambda e: self.master.open_keyboard(mode="numeric"))

        # Auth Key
        ttk.Label(left_col, text="Auth Key", font=("Arial", 11)).pack(anchor="w", pady=(10, 0))
        ttk.Label(left_col, text="(Committee only - for if paying now)", font=("Arial", 10, "italic")).pack(anchor="w")
        self.auth_key = ttk.Entry(left_col, font=("Arial", 14))
        self.auth_key.pack(fill="x")
        self.auth_key.bind("<Button-1>", lambda e: self.master.open_keyboard(mode="numeric"))

        self.cost_display = ttk.Label(left_col, text="Cost: £0.00", font=("Arial", 18, "bold"))
        self.cost_display.pack(pady=5)

        # --- RIGHT COLUMN (Signature) ---
        right_col = ttk.Frame(content_container)
        right_col.pack(side="left", fill="both", expand=True, padx=20)

        ttk.Label(right_col, text="Payee Signature", font=("Arial", 12)).pack()
        self.canvas = tk.Canvas(right_col, bg="white", width=self.canvaswidth, height=self.canvasheight,
                                relief="ridge", bd=2, highlightthickness=0)
        self.canvas.pack(pady=10)

        self.image = Image.new("RGB", (self.canvaswidth, self.canvasheight), "white")
        self.draw = ImageDraw.Draw(self.image)
        self.last_x, self.last_y = None, None

        self.canvas.bind("<B1-Motion>", self.paint)
        self.canvas.bind("<ButtonRelease-1>", self.reset_coords)
        ttk.Button(right_col, text="Clear Signature", command=self.clear).pack()

        # 3. BOTTOM BUTTON BAR
        btn_frame = ttk.Frame(self)
        btn_frame.pack(side="bottom", pady=20)

        ttk.Button(btn_frame, text="Confirm", style="Accent.TButton",
                   command=self.handle_save).pack(side="left", padx=20, ipadx=20, ipady=10)

        ttk.Button(btn_frame, text="Cancel",
                   command=lambda: self.master.switch_frame(StartScreen)).pack(side="left", padx=20, ipadx=20, ipady=10)

    def select_fiber(self, fiber_type):
        """Updates the selection state and color of buttons."""
        self.selected_fiber = fiber_type
        # If you have an 'Accent.TButton' defined, you could toggle styles here.
        # For now, we'll just store the choice and update the cost.
        self.update_price()

    def paint(self, event):
        if self.last_x and self.last_y:
            self.canvas.create_line(self.last_x, self.last_y, event.x, event.y,
                                    width=4, fill="black", capstyle=tk.ROUND, smooth=True)
            self.draw.line([self.last_x, self.last_y, event.x, event.y], fill="black", width=4)
            self.signed = True
        self.last_x, self.last_y = event.x, event.y

    def reset_coords(self, event):
        self.last_x, self.last_y = None, None

    def clear(self):
        self.canvas.delete("all")
        self.image = Image.new("RGB", (self.canvaswidth, self.canvasheight), "white")
        self.draw = ImageDraw.Draw(self.image)
        self.signed = False

    def update_price(self):
        onyx = self.onyx_vol.get()
        fiber_vol = self.fiber_vol.get() or "0"
        hours = self.print_hrs.get() or "0"

        # Only attempt calculation if at least Onyx volume is entered
        if onyx:
            try:
                # Calling our new separate function
                price = calculate_markforged_cost(
                    onyx_cc=onyx,
                    fiber_type=self.selected_fiber,
                    fiber_cc=fiber_vol,
                    hours=hours
                )
                self.cost_display.config(text=f"Cost: £{price:.2f}")
                return price
            except ValueError:
                self.cost_display.config(text="Invalid Inputs!")
        return 0.0

    def handle_save(self):
        user = self.username.get().strip()
        onyx = self.onyx_vol.get()
        fiber_vol = self.fiber_vol.get() or "0"
        hrs = self.print_hrs.get()
        price = self.update_price()
        auth = self.auth_key.get().strip()

        # Validating Auth
        auth_valid = (auth == "" or (len(auth) == 4 and auth.isdigit()))
        if auth_valid and auth != "":
            auth_code_list = sheet.get_possible_auth_code()
            auth_valid = auth in auth_code_list

        if not user:
            messagebox.showwarning("Input Error", "Please fill in your username.")
        elif not onyx:
            messagebox.showwarning("Input Error", "Please fill in your onyx volume.")
        elif not hrs:
            messagebox.showwarning("Input Error", "Please fill in your print time.")
        elif not self.signed:
            messagebox.showwarning("Input Error", "Please add your signature.")
        elif not auth_valid:
            messagebox.showerror("Input Error", "Invalid authentication code.")
        else:
            # timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            # filename = f"signatures/markforged_{user}_{timestamp}.png"
            # self.image.save(filename)
            #
            # # Assuming your spreadsheet helper has a specific method for Markforged
            # sheet.add_markforged_print_credit(
            #     Bath_ID=user,
            #     Onyx_CC=onyx,
            #     Fiber_Type=self.selected_fiber,
            #     Fiber_CC=fiber_vol,
            #     Hours=hrs,
            #     AuthCode=auth,
            #     Signature_path=filename
            # )

            messagebox.showinfo("Thank you, have a nice day!", "Record logged successfully.")
            self.master.switch_frame(StartScreen)

class PaymentUpdateScreen(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.unpaid_list = self.master.get_unpaid_debts()

        self.bind("<Button-1>", lambda e: self.master.close_keyboard())

        ttk.Label(self, text="Mark Debt As Paid", font=("Arial", 20, "bold")).pack(pady=15)

        content_container = ttk.Frame(self)
        content_container.pack(fill="both", expand=True, padx=40)

        # --- LEFT COLUMN ---
        left_col = ttk.Frame(content_container)
        left_col.pack(side="left", fill="both", expand=True, padx=20)
        ttk.Label(left_col, text="Select Record", font=("Arial", 12)).pack(pady=5)

        list_container = ttk.Frame(left_col)
        list_container.pack(fill="both", expand=True, pady=10)

        self.debt_listbox = tk.Listbox(list_container, font=("Arial", 16), height=6, exportselection=False)
        self.debt_listbox.pack(side="left", fill="both", expand=True)

        if not self.unpaid_list:
            self.debt_listbox.insert(tk.END, "  No unpaid debts found")
            self.debt_listbox.config(state="disabled")
        else:
            for row in self.unpaid_list:
                # Show Date, User, and Cost in the list
                self.debt_listbox.insert(tk.END, f"{row["Bath ID"]} - £{float(row["Value"]):.2f}")

        scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=self.debt_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.debt_listbox.config(yscrollcommand=scrollbar.set)

        # --- RIGHT COLUMN ---
        right_col = ttk.Frame(content_container)
        right_col.pack(side="left", fill="both", expand=True, padx=20)

        ttk.Label(right_col, text="Authentication Key", font=("Arial", 12)).pack(anchor="w")
        ttk.Label(right_col, text="(Committee only)", font=("Arial", 10, "italic")).pack(anchor="w")

        self.auth_key = ttk.Entry(right_col, font=("Arial", 14))
        self.auth_key.pack(fill="x", pady=10)
        self.auth_key.bind("<Button-1>", lambda e: self.master.open_keyboard(mode="numeric"))
        self.auth_key.bind("<Return>", lambda e: self.master.close_keyboard())

        # 3. BOTTOM BUTTONS
        btn_frame = ttk.Frame(self)
        btn_frame.pack(side="bottom", pady=40)

        ttk.Button(btn_frame, text="Confirm", style="Accent.TButton",
                   command=self.handle_save).pack(side="left", padx=20, ipadx=20, ipady=10)
        ttk.Button(btn_frame, text="Cancel",
                   command=lambda: self.master.switch_frame(StartScreen)).pack(side="left", padx=20, ipadx=20, ipady=10)

    def handle_save(self):
        auth = self.auth_key.get().strip()
        selection = self.debt_listbox.curselection()

        auth_valid = (len(auth) == 4 and auth.isdigit())

        if auth_valid and auth != "":
            auth_code_list = sheet.get_possible_auth_code()
            if auth in auth_code_list:
                auth_valid = True
            else:
                auth_valid = False

        selected_row_data = self.unpaid_list[selection[0]]
        if auth_valid:
            sheet.complete_pending_payment(Bath_ID=selected_row_data["Bath ID"], AuthCode=auth)
            messagebox.showinfo("Thank you, have a nice day!", "Record cleared successfully.")
            self.master.switch_frame(StartScreen)
        else:
            messagebox.showwarning("Input Error", "Invalid authentication code.")

class EquipChoiceScreen(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)

        label = ttk.Label(self, text="", font=("Arial", 24))
        label.pack(pady=20)

        btn1 = ttk.Button(self, text="Loan Equipment",
                         command=lambda: master.switch_frame(EquipLoanScreen))
        btn1.pack(ipadx=60, ipady=45, pady=15)

        btn2 = ttk.Button(self, text="Return Equipment",
                         command=lambda: master.switch_frame(EquipReturnScreen))
        btn2.pack(ipadx=60, ipady=45, pady=15)

        btn3 = ttk.Button(self, text="Back",
                         command=lambda: master.switch_frame(StartScreen))
        btn3.pack(ipadx=30, ipady=15, pady=10)

class EquipLoanScreen(ttk.Frame):
    canvaswidth = 350
    canvasheight = 180  # Slightly shorter to accommodate the extra entry box

    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.signed = False
        self.current_category = None

        self.equipment_data = [
            "IT_Inventory",
            "Mechanical_tools",
            "Electronics_Equipment",
            "Laser_Printer_Equip",
        ]

        self.bind("<Button-1>", lambda e: self.master.close_keyboard())

        # 1. TOP TITLE
        ttk.Label(self, text="Loan Equipment", font=("Arial", 20, "bold")).pack(pady=10)

        # 2. MAIN CONTENT AREA
        content_container = ttk.Frame(self)
        content_container.pack(fill="both", expand=True, padx=40)

        # --- LEFT COLUMN (Selection Area) ---
        left_col = ttk.Frame(content_container)
        left_col.pack(side="left", fill="both", expand=True, padx=20)

        ttk.Label(left_col, text="Select Category", font=("Arial", 12)).pack(pady=5)

        grid_frame = ttk.Frame(left_col)
        grid_frame.pack()
        for i,category in enumerate(self.equipment_data):
            btn = ttk.Button(grid_frame, text=category, width=20,
                             command=lambda c=category: self.update_category(c))
            btn.grid(row=i // 2, column=i % 2, padx=5, pady=5, ipady=5)

        ttk.Label(left_col, text="Tap to Select Item", font=("Arial", 12)).pack(pady=(15, 5))

        list_container = ttk.Frame(left_col)
        list_container.pack(fill="both", expand=True)

        self.item_listbox = tk.Listbox(
            list_container,
            font=("Arial", 16),
            height=4,
            exportselection=False,
            selectbackground="#007fff"
        )
        self.item_listbox.pack(side="left", fill="both", expand=True)

        self.scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=self.item_listbox.yview)
        self.scrollbar.pack(side="right", fill="y")
        self.item_listbox.config(yscrollcommand=self.scrollbar.set)

        # --- RIGHT COLUMN (Identity & Auth) ---
        right_col = ttk.Frame(content_container)
        right_col.pack(side="left", fill="both", expand=True, padx=20)

        # Username
        ttk.Label(right_col, text="Username", font=("Arial", 12)).pack(anchor="w")
        self.username = ttk.Entry(right_col, font=("Arial", 14))
        self.username.pack(fill="x", pady=(0, 10))
        self.username.bind("<Button-1>", lambda e: self.master.open_keyboard(mode="full"))
        self.username.bind("<Return>", lambda e: self.master.close_keyboard())

        # Auth Key
        ttk.Label(right_col, text="Authentication Key", font=("Arial", 12)).pack(anchor="w")
        ttk.Label(right_col, text="(Committee only)", font=("Arial", 10, "italic")).pack(anchor="w")
        self.auth_key = ttk.Entry(right_col, font=("Arial", 14))
        self.auth_key.pack(fill="x", pady=(0, 10))
        self.auth_key.bind("<Button-1>", lambda e: self.master.open_keyboard(mode="numeric"))
        self.auth_key.bind("<Return>", lambda e: self.master.close_keyboard())

        # 3. BOTTOM BUTTON BAR
        btn_frame = ttk.Frame(self)
        btn_frame.pack(side="bottom", pady=20)

        ttk.Button(btn_frame, text="Confirm", style="Accent.TButton",
                   command=self.handle_save).pack(side="left", padx=20, ipadx=20, ipady=10)

        ttk.Button(btn_frame, text="Cancel",
                   command=lambda: self.master.switch_frame(StartScreen)).pack(side="left", padx=20, ipadx=20, ipady=10)

    def update_category(self, category):
        self.current_category = category
        self.item_listbox.delete(0, tk.END)
        for item in sheet.get_available_equipment_inventory(category):
            self.item_listbox.insert(tk.END, f"  {item["Item Name"]}")
        
        if self.item_listbox.size() == 0:
            self.item_listbox.insert(tk.END, "  No items available")
        self.master.close_keyboard()

    def paint(self, event):
        if self.last_x and self.last_y:
            self.canvas.create_line(self.last_x, self.last_y, event.x, event.y,
                                    width=4, fill="black", capstyle=tk.ROUND, smooth=True)
            self.draw.line([self.last_x, self.last_y, event.x, event.y], fill="black", width=4)
            self.signed = True
        self.last_x, self.last_y = event.x, event.y

    def reset_coords(self, event):
        self.last_x, self.last_y = None, None

    def clear(self):
        self.canvas.delete("all")
        self.image = Image.new("RGB", (self.canvaswidth, self.canvasheight), "white")
        self.draw = ImageDraw.Draw(self.image)
        self.signed = False

    def handle_save(self):
        user = self.username.get().strip()
        auth = self.auth_key.get().strip()
        selection = self.item_listbox.curselection()
        item = self.item_listbox.get(selection[0]).strip() if selection else None

        auth_valid = (len(auth) == 4 and auth.isdigit())
        
        if auth_valid and auth != "":
            auth_code_list = sheet.get_possible_auth_code()
            if auth in auth_code_list:
                auth_valid = True
            else:
                auth_valid = False

        if not user or not item or not auth_valid:
            messagebox.showwarning("Input Error", "Please fill in your username.")
        elif not item:
            messagebox.showwarning("Input Error", "Please select an item.")
        elif not auth_valid:
            messagebox.showwarning("Input Error", "Invalid authentication code.")
        else:
            sheet.add_loan_out_entry(Bath_ID=user, Item_Category=self.current_category, Item=item, AuthCode=auth)
            messagebox.showinfo("Thank you, have a nice day!", f"{item} successfully loaned to {user}.")
            self.master.switch_frame(StartScreen)

class EquipReturnScreen(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master

        # Pull the fresh list of loaned items from the CSV
        self.loaned_items = self.master.get_loaned_items()

        # Background tap closes keyboard
        self.bind("<Button-1>", lambda e: self.master.close_keyboard())

        # 1. TOP TITLE
        ttk.Label(self, text="Return Equipment", font=("Arial", 20, "bold")).pack(pady=15)

        # 2. MAIN CONTENT AREA
        content_container = ttk.Frame(self)
        content_container.pack(fill="both", expand=True, padx=40)

        # --- LEFT COLUMN (Item Selection) ---
        left_col = ttk.Frame(content_container)
        left_col.pack(side="left", fill="both", expand=True, padx=20)

        ttk.Label(left_col, text="Select Item to Return", font=("Arial", 12)).pack(pady=5)

        list_container = ttk.Frame(left_col)
        list_container.pack(fill="both", expand=True, pady=10)

        # Large Listbox for fingers
        self.item_listbox = tk.Listbox(
            list_container,
            font=("Arial", 16),
            height=6,
            exportselection=False,
            selectbackground="#007fff"
        )
        self.item_listbox.pack(side="left", fill="both", expand=True)

        # Populate with ONLY items currently out
        if not self.loaned_items:
            self.item_listbox.insert(tk.END, "  No items currently loaned out")
            self.item_listbox.config(state="disabled")
        else:
            for item in sorted(self.loaned_items):
                self.item_listbox.insert(tk.END, f"  {item}")

        # Thick scrollbar for touchscreen
        scrollbar_style = ttk.Style()
        scrollbar_style.configure("Return.Vertical.TScrollbar", arrowsize=25)

        self.scrollbar = ttk.Scrollbar(list_container, orient="vertical",
                                       command=self.item_listbox.yview,
                                       style="Return.Vertical.TScrollbar")
        self.scrollbar.pack(side="right", fill="y")
        self.item_listbox.config(yscrollcommand=self.scrollbar.set)

        # --- RIGHT COLUMN (Verification) ---
        right_col = ttk.Frame(content_container)
        right_col.pack(side="left", fill="both", expand=True, padx=20)

        ttk.Label(right_col, text="Username", font=("Arial", 12)).pack(anchor="w")
        self.username = ttk.Entry(right_col, font=("Arial", 14))
        self.username.pack(fill="x", pady=(0, 20))
        self.username.bind("<Button-1>", lambda e: self.master.open_keyboard(mode="full"))
        self.username.bind("<Return>", lambda e: self.master.close_keyboard())

        ttk.Label(right_col, text="Auth Key", font=("Arial", 12)).pack(anchor="w")
        ttk.Label(right_col, text="(Committee only)", font=("Arial", 10, "italic")).pack(anchor="w")
        self.auth_key = ttk.Entry(right_col, font=("Arial", 14))
        self.auth_key.pack(fill="x", pady=(0, 10))
        self.auth_key.bind("<Button-1>", lambda e: self.master.open_keyboard(mode="numeric"))
        self.auth_key.bind("<Return>", lambda e: self.master.close_keyboard())

        # 3. BOTTOM BUTTON BAR
        btn_frame = ttk.Frame(self)
        btn_frame.pack(side="bottom", pady=40)

        ttk.Button(btn_frame, text="Confirm", style="Accent.TButton",
                   command=self.handle_save).pack(side="left", padx=20, ipadx=20, ipady=10)

        ttk.Button(btn_frame, text="Cancel",
                   command=lambda: self.master.switch_frame(StartScreen)).pack(side="left", padx=20, ipadx=20, ipady=10)

    def handle_save(self):
        user = self.username.get().strip()
        auth = self.auth_key.get().strip()
        selection = self.item_listbox.curselection()
        item = self.item_listbox.get(selection[0]).strip() if selection else None

        auth_valid = (len(auth) == 4 and auth.isdigit())
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        if not user:
            messagebox.showwarning("Input error", "Please fill in your username.")
        elif not item:
            messagebox.showwarning("Input error", "Please select an item.")
        elif not auth_valid:
            messagebox.showwarning("Input error", "Invalid authentication code.")
        else:
            with open("loans.csv", "a", newline="") as f:
                # Logging the return timestamp
                csv.writer(f).writerow([timestamp, user, "N/A", item, "RETURNED", auth])

            messagebox.showinfo("Thank you, have a nice day!", f"Item '{item}' returned successfully.")
            self.master.switch_frame(StartScreen)

if __name__ == "__main__":
    app = App()
    # Apply the theme to the specific app instance
    sv_ttk.set_theme("light")
    app.mainloop()