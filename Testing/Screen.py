import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageDraw, ImageTk, ImageEnhance
import csv
import sv_ttk
import os
import subprocess
from Bath_Cost_Code import Calculate_Personal_Cost
from tkinter import messagebox
from datetime import datetime

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
        unpaid = []
        if os.path.exists("entries.csv"):
            with open("entries.csv", "r") as f:
                reader = csv.reader(f)
                for row in reader:
                    # Indexing: 0:Time, 1:User, 2:Cost, 3:Auth
                    if len(row) >= 3:
                        auth = row[3] if len(row) > 3 else ""
                        if not auth.strip():
                            unpaid.append(row)
        return unpaid

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
        ttk.Label(self, text="Log 3D Print Debt", font=("Arial", 24, "bold")).pack(pady=20)

        # 2. MAIN CONTENT AREA
        content_container = ttk.Frame(self)
        content_container.pack(fill="both", expand=True, padx=50)

        # --- LEFT COLUMN (Inputs) ---
        left_col = ttk.Frame(content_container)
        left_col.pack(side="left", fill="both", expand=True, padx=20)

        ttk.Label(left_col, text="Username", font=("Arial", 12)).pack(anchor="w")
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

        ttk.Label(right_col, text="Please Sign Below", font=("Arial", 12)).pack()
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

        if not user or price <= 0 or not self.signed:
            messagebox.showwarning("Incomplete", "Please fill in Username, Mass, and Signature.")
        elif not auth_valid:
            messagebox.showwarning("Invalid Auth", "Auth Key must be 4 digits (or leave blank).")
        else:
            # Save signature with unique timestamp
            filename = f"signatures/debt_{user}_{timestamp}.png"
            self.image.save(filename)

            with open("entries.csv", "a", newline="") as f:
                # Adding timestamp as the first column
                csv.writer(f).writerow([timestamp, user, price, auth])

            messagebox.showinfo("Success", "Debt logged successfully!")
            self.master.switch_frame(StartScreen)


class StartScreen(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master

        # --- BACKGROUND LOGO LOGIC ---
        try:
            # 1. Load the original image
            original_logo = Image.open("transparent_png_logo_final.png").convert("RGBA")

            # 2. Resize it (e.g., to 400x400 or whatever fits your 1024x600 screen)
            logo_resized = original_logo.resize((800, 800), Image.Resampling.LANCZOS)

            # 3. Adjust Opacity (0.1 is 10% opacity, 0.2 is 20%, etc.)
            alpha = logo_resized.split()[3]
            alpha = ImageEnhance.Brightness(alpha).enhance(0.2)
            logo_resized.putalpha(alpha)

            # 4. Convert to a format Tkinter understands
            self.bg_image = ImageTk.PhotoImage(logo_resized)

            # 5. Create a label to hold the image and place it in the center
            # We use a standard tk.Label here so we can set a transparent background
            self.bg_label = tk.Label(self, image=self.bg_image)
            self.bg_label.place(relx=0.3, rely=0.5, anchor="center")

        except FileNotFoundError:
            print("Logo file not found, skipping background image.")

        # --- EXISTING BUTTONS ---
        # The buttons will naturally sit on top of the placed image
        label = ttk.Label(self, text="Welcome To The Makerspace Information Terminal",
                          font=("Arial", 32, "bold"))
        label.pack(pady=(80, 40))  # More top padding to move text off the logo center

        btn1 = ttk.Button(self, text="3D Printing Service", font=("Arial", 24),
                          command=lambda: master.switch_frame(PaymentChoiceScreen))
        btn1.pack(ipadx=40, ipady=30, pady=10)

        btn2 = ttk.Button(self, text="Equipment Service", font=("Arial", 24),
                          command=lambda: master.switch_frame(EquipChoiceScreen))
        btn2.pack(ipadx=40, ipady=30, pady=10)

class EquipChoiceScreen(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)

        label = ttk.Label(self, text="", font=("Arial", 24))
        label.pack(pady=75)

        btn1 = ttk.Button(self, text="Loaning Equipment",
                         command=lambda: master.switch_frame(EquipLoanScreen))
        btn1.pack(ipadx=20, ipady=10, pady=10)

        btn2 = ttk.Button(self, text="Returning Equipment",
                         command=lambda: master.switch_frame(EquipReturnScreen))
        btn2.pack(ipadx=20, ipady=10, pady=10)

        btn3 = ttk.Button(self, text="Cancel",
                         command=lambda: master.switch_frame(StartScreen))
        btn3.pack(ipadx=20, ipady=10, pady=10)

class PaymentChoiceScreen(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)

        label = ttk.Label(self, text="", font=("Arial", 24))
        label.pack(pady=75)

        btn1 = ttk.Button(self, text="Log New Print Debt",
                         command=lambda: master.switch_frame(PaymentInputScreen))
        btn1.pack(ipadx=20, ipady=10, pady=10)

        btn2 = ttk.Button(self, text="Mark Debt As Paid",
                         command=lambda: master.switch_frame(PaymentUpdateScreen))
        btn2.pack(ipadx=20, ipady=10, pady=10)

        btn3 = ttk.Button(self, text="Cancel",
                         command=lambda: master.switch_frame(StartScreen))
        btn3.pack(ipadx=20, ipady=10, pady=10)


class EquipLoanScreen(ttk.Frame):
    canvaswidth = 350
    canvasheight = 180  # Slightly shorter to accommodate the extra entry box

    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.signed = False
        self.current_category = None

        self.equipment_data = {
            "Power Tools": ["Cordless Drill", "Jigsaw", "Orbital Sander", "Heat Gun", "Router"],
            "Hand Tools": ["Screwdriver Set", "Socket Wrench", "Chisel Set", "Hand Saw"],
            "Electronics": ["Multimeter", "Soldering Iron", "Oscilloscope", "Power Supply"],
            "Miscellaneous": ["Safety Goggles", "Measuring Tape", "Spirit Level", "Clamps"]
        }

        self.bind("<Button-1>", lambda e: self.master.close_keyboard())

        # 1. TOP TITLE
        ttk.Label(self, text="Equipment Loan Portal", font=("Arial", 20, "bold")).pack(pady=10)

        # 2. MAIN CONTENT AREA
        content_container = ttk.Frame(self)
        content_container.pack(fill="both", expand=True, padx=40)

        # --- LEFT COLUMN (Selection Area) ---
        left_col = ttk.Frame(content_container)
        left_col.pack(side="left", fill="both", expand=True, padx=20)

        ttk.Label(left_col, text="1. Select Category", font=("Arial", 12, "bold")).pack(pady=5)

        grid_frame = ttk.Frame(left_col)
        grid_frame.pack()
        for i, cat in enumerate(self.equipment_data.keys()):
            btn = ttk.Button(grid_frame, text=cat, width=15,
                             command=lambda c=cat: self.update_category(c))
            btn.grid(row=i // 2, column=i % 2, padx=5, pady=5, ipady=5)

        ttk.Label(left_col, text="2. Tap to Select Item", font=("Arial", 12, "bold")).pack(pady=(15, 5))

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
        ttk.Label(right_col, text="Username", font=("Arial", 11)).pack(anchor="w")
        self.username = ttk.Entry(right_col, font=("Arial", 14))
        self.username.pack(fill="x", pady=(0, 10))
        self.username.bind("<Button-1>", lambda e: self.master.open_keyboard(mode="full"))
        self.username.bind("<Return>", lambda e: self.master.close_keyboard())

        # Auth Key
        ttk.Label(right_col, text="Auth Key (Committee Only)", font=("Arial", 11)).pack(anchor="w")
        self.auth_key = ttk.Entry(right_col, font=("Arial", 14))
        self.auth_key.pack(fill="x", pady=(0, 10))
        self.auth_key.bind("<Button-1>", lambda e: self.master.open_keyboard(mode="numeric"))
        self.auth_key.bind("<Return>", lambda e: self.master.close_keyboard())

        # Signature
        ttk.Label(right_col, text="Signature", font=("Arial", 11)).pack(anchor="w")
        self.canvas = tk.Canvas(right_col, bg="white", width=self.canvaswidth, height=self.canvasheight,
                                relief="ridge", bd=2, highlightthickness=0)
        self.canvas.pack(pady=5)

        self.image = Image.new("RGB", (self.canvaswidth, self.canvasheight), "white")
        self.draw = ImageDraw.Draw(self.image)
        self.last_x, self.last_y = None, None
        self.canvas.bind("<B1-Motion>", self.paint)
        self.canvas.bind("<ButtonRelease-1>", self.reset_coords)

        ttk.Button(right_col, text="Clear Signature", command=self.clear).pack(pady=2)

        # 3. BOTTOM BUTTON BAR
        btn_frame = ttk.Frame(self)
        btn_frame.pack(side="bottom", pady=20)

        ttk.Button(btn_frame, text="Confirm Loan", style="Accent.TButton",
                   command=self.handle_save).pack(side="left", padx=20, ipadx=20, ipady=10)

        ttk.Button(btn_frame, text="Cancel",
                   command=lambda: self.master.switch_frame(StartScreen)).pack(side="left", padx=20, ipadx=20, ipady=10)

    def update_category(self, category):
        self.current_category = category
        self.item_listbox.delete(0, tk.END)
        currently_loaned = self.master.get_loaned_items()

        for item in self.equipment_data[category]:
            if item not in currently_loaned:
                self.item_listbox.insert(tk.END, f"  {item}")

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
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        if not user or not item or not self.signed or not auth_valid:
            messagebox.showwarning("Incomplete", "Username, Item, Signature, and 4-Digit Auth are REQUIRED.")
        else:
            # Save signature with unique timestamp
            filename = f"signatures/loan_{user}_{timestamp}.png"
            self.image.save(filename)

            with open("loans.csv", "a", newline="") as f:
                # Logging: Time, User, Category, Item, Status, Auth
                csv.writer(f).writerow([timestamp, user, self.current_category, item, "LOANED", auth])

            messagebox.showinfo("Success", f"{item} loaned to {user}!")
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

        ttk.Label(left_col, text="1. Select Item to Return", font=("Arial", 12, "bold")).pack(pady=5)

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

        ttk.Label(right_col, text="2. Your Details", font=("Arial", 12, "bold")).pack(pady=10)

        ttk.Label(right_col, text="Username", font=("Arial", 11)).pack(anchor="w")
        self.username = ttk.Entry(right_col, font=("Arial", 14))
        self.username.pack(fill="x", pady=(0, 20))
        self.username.bind("<Button-1>", lambda e: self.master.open_keyboard(mode="full"))
        self.username.bind("<Return>", lambda e: self.master.close_keyboard())

        ttk.Label(right_col, text="Auth Key (Committee Only)", font=("Arial", 11)).pack(anchor="w")
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

        if not user or not item or not auth_valid:
            messagebox.showwarning("Incomplete", "Username, Selection, and 4-Digit Auth are REQUIRED.")
        else:
            with open("loans.csv", "a", newline="") as f:
                # Logging the return timestamp
                csv.writer(f).writerow([timestamp, user, "N/A", item, "RETURNED", auth])

            messagebox.showinfo("Success", f"Item '{item}' returned successfully!")
            self.master.switch_frame(StartScreen)


class PaymentUpdateScreen(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.unpaid_list = self.master.get_unpaid_debts()

        self.bind("<Button-1>", lambda e: self.master.close_keyboard())

        ttk.Label(self, text="Clear Outstanding Debt", font=("Arial", 20, "bold")).pack(pady=15)

        content_container = ttk.Frame(self)
        content_container.pack(fill="both", expand=True, padx=40)

        # --- LEFT COLUMN ---
        left_col = ttk.Frame(content_container)
        left_col.pack(side="left", fill="both", expand=True, padx=20)

        ttk.Label(left_col, text="Select Record", font=("Arial", 12, "bold")).pack(pady=5)

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
                date_short = row[0][:10]  # Just the YYYY-MM-DD part
                self.debt_listbox.insert(tk.END, f"  {date_short} | {row[1]} - £{float(row[2]):.2f}")

        scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=self.debt_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.debt_listbox.config(yscrollcommand=scrollbar.set)

        # --- RIGHT COLUMN ---
        right_col = ttk.Frame(content_container)
        right_col.pack(side="left", fill="both", expand=True, padx=20)

        ttk.Label(right_col, text="Verification", font=("Arial", 12, "bold")).pack(pady=10)
        ttk.Label(right_col, text="4-Digit Auth Key", font=("Arial", 11)).pack(anchor="w")

        self.auth_key = ttk.Entry(right_col, font=("Arial", 14))
        self.auth_key.pack(fill="x", pady=10)
        self.auth_key.bind("<Button-1>", lambda e: self.master.open_keyboard(mode="numeric"))
        self.auth_key.bind("<Return>", lambda e: self.master.close_keyboard())

        # 3. BOTTOM BUTTONS
        btn_frame = ttk.Frame(self)
        btn_frame.pack(side="bottom", pady=40)

        ttk.Button(btn_frame, text="Mark as PAID", style="Accent.TButton",
                   command=self.handle_save).pack(side="left", padx=20, ipadx=20, ipady=10)
        ttk.Button(btn_frame, text="Cancel",
                   command=lambda: self.master.switch_frame(StartScreen)).pack(side="left", padx=20, ipadx=20, ipady=10)

    def handle_save(self):
        auth = self.auth_key.get().strip()
        selection = self.debt_listbox.curselection()

        if not selection or not (len(auth) == 4 and auth.isdigit()):
            messagebox.showwarning("Error", "Select a record and enter a 4-digit Auth Key.")
            return

        selected_row_data = self.unpaid_list[selection[0]]
        all_rows = []
        updated = False

        # Read and find the matching row using the unique timestamp + user + cost
        with open("entries.csv", "r") as f:
            reader = csv.reader(f)
            for row in reader:
                if not updated and row == selected_row_data:
                    # Column 0: Time, 1: User, 2: Cost, 3: Auth
                    if len(row) < 4:
                        row.append(auth)
                    else:
                        row[3] = auth
                    updated = True
                all_rows.append(row)

        with open("entries.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(all_rows)

        messagebox.showinfo("Success", "Record updated.")
        self.master.switch_frame(StartScreen)

if __name__ == "__main__":
    app = App()
    # Apply the theme to the specific app instance
    sv_ttk.set_theme("light")
    app.mainloop()