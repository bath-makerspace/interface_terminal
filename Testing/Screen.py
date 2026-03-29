import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageDraw
import csv
import sv_ttk
import os
import subprocess
from Bath_Cost_Code import Calculate_Personal_Cost
from tkinter import messagebox


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Makerspace Portal")
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
        """Returns a set of items that are currently marked as 'LOANED'."""
        loaned_items = set()
        if os.path.exists("loans.csv"):
            with open("loans.csv", "r") as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 4:
                        user, cat, item, status = row[0], row[1], row[2], row[3]
                        if status == "LOANED":
                            loaned_items.add(item)
                        elif status == "RETURNED":
                            loaned_items.discard(item)
        return loaned_items

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

        # Validation Logic
        auth_valid = (auth == "" or (len(auth) == 4 and auth.isdigit()))

        if not user:
            messagebox.showwarning("Incomplete", "Please enter a Username.")
        elif price <= 0:
            messagebox.showwarning("Incomplete", "Please enter a valid Print Mass.")
        elif not self.signed:
            messagebox.showwarning("Incomplete", "Please provide a signature.")
        elif not auth_valid:
            messagebox.showwarning("Invalid Auth", "Auth Key must be empty or a 4-digit number.")
        else:
            # All checks pass - Save data
            self.image.save(f"signatures/{user}_sig.png")
            with open("entries.csv", "a", newline="") as f:
                csv.writer(f).writerow([user, price, auth])

            messagebox.showinfo("Success", "Debt logged successfully!")
            self.master.switch_frame(StartScreen)

class StartScreen(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)

        label = ttk.Label(self, text="Welcome to the Makerspace Portal", font=("Arial", 24))
        label.pack(pady=100)

        # Using style="Accent.TButton" (provided by sv_ttk) for the primary action
        # btn1 = ttk.Button(self, text="Test Signature Pad",
        #                  style="Accent.TButton",
        #                  command=lambda: master.switch_frame(SignatureScreen))
        # btn1.pack(ipadx=20, ipady=10, pady=10)

        btn2 = ttk.Button(self, text="3D Printing services",
                         command=lambda: master.switch_frame(PaymentChoiceScreen))
        btn2.pack(ipadx=20, ipady=10, pady=10)

        btn2 = ttk.Button(self, text="Equipment services",
                         command=lambda: master.switch_frame(EquipChoiceScreen))
        btn2.pack(ipadx=20, ipady=10, pady=10)

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
    canvasheight = 200

    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.signed = False
        self.current_category = None

        self.equipment_data = {
            "Power Tools": ["Cordless Drill", "Jigsaw", "Orbital Sander", "Heat Gun", "Router", "Circular Saw"],
            "Hand Tools": ["Screwdriver Set", "Socket Wrench", "Chisel Set", "Hand Saw", "Rubber Mallet"],
            "Electronics": ["Multimeter", "Soldering Iron", "Oscilloscope", "Power Supply"],
            "Miscellaneous": ["Safety Goggles", "Measuring Tape", "Spirit Level", "Clamps"]
        }

        self.bind("<Button-1>", lambda e: self.master.close_keyboard())

        # 1. TOP TITLE - Reduced padding from 20 to 10
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

        # REDUCED HEIGHT: Changed from 6 to 4 to save vertical space
        self.item_listbox = tk.Listbox(
            list_container,
            font=("Arial", 16),
            height=4,
            activestyle='none',
            exportselection=False,
            selectbackground="#007fff"
        )
        self.item_listbox.pack(side="left", fill="both", expand=True)

        scrollbar_style = ttk.Style()
        scrollbar_style.configure("Vertical.TScrollbar", arrowsize=25)

        self.scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=self.item_listbox.yview,
                                       style="Vertical.TScrollbar")
        self.scrollbar.pack(side="right", fill="y")
        self.item_listbox.config(yscrollcommand=self.scrollbar.set)

        # --- RIGHT COLUMN (Identity Area) ---
        right_col = ttk.Frame(content_container)
        right_col.pack(side="left", fill="both", expand=True, padx=20)

        ttk.Label(right_col, text="Username", font=("Arial", 11)).pack(anchor="w")
        self.username = ttk.Entry(right_col, font=("Arial", 14))
        self.username.pack(fill="x", pady=(0, 10))
        self.username.bind("<Button-1>", lambda e: self.master.open_keyboard(mode="full"))
        self.username.bind("<Return>", lambda e: self.master.close_keyboard())

        ttk.Label(right_col, text="Signature", font=("Arial", 11)).pack(anchor="w")
        self.canvas = tk.Canvas(right_col, bg="white", width=self.canvaswidth, height=self.canvasheight,
                                relief="ridge", bd=2, highlightthickness=0)
        self.canvas.pack(pady=5)

        self.image = Image.new("RGB", (self.canvaswidth, self.canvasheight), "white")
        self.draw = ImageDraw.Draw(self.image)
        self.last_x, self.last_y = None, None
        self.canvas.bind("<B1-Motion>", self.paint)
        self.canvas.bind("<ButtonRelease-1>", self.reset_coords)

        ttk.Button(right_col, text="Clear Signature", command=self.clear).pack(pady=5)

        # 3. BOTTOM BUTTON BAR - Adjusted padding for breathing room
        btn_frame = ttk.Frame(self)
        btn_frame.pack(side="bottom", pady=20)

        ttk.Button(btn_frame, text="Confirm", style="Accent.TButton",
                   command=self.handle_save).pack(side="left", padx=20, ipadx=20, ipady=10)

        ttk.Button(btn_frame, text="Cancel",
                   command=lambda: self.master.switch_frame(StartScreen)).pack(side="left", padx=20, ipadx=20, ipady=10)

    # (Methods: update_category, paint, reset_coords, clear, and handle_save stay the same)

    def update_category(self, category):
        self.current_category = category
        self.item_listbox.delete(0, tk.END)

        # Get the current list of what is ALREADY out
        currently_loaned = self.master.get_loaned_items()

        for item in self.equipment_data[category]:
            # ONLY add to the list if it is NOT currently loaned out
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
        selection = self.item_listbox.curselection()
        item = self.item_listbox.get(selection[0]).strip() if selection else None

        if not user or not item or not self.signed:
            messagebox.showwarning("Incomplete", "Please ensure Username, Item, and Signature are provided.")
        else:
            if not os.path.exists("signatures"): os.makedirs("signatures")
            self.image.save(f"signatures/loan_{user}.png")
            with open("loans.csv", "a", newline="") as f:
                csv.writer(f).writerow([user, self.current_category, item, "LOANED"])
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

        # Get item selection
        selection = self.item_listbox.curselection()
        item = self.item_listbox.get(selection[0]).strip() if selection else None

        # Logic: Auth must be empty OR exactly 4 digits
        auth_valid = (auth == "" or (len(auth) == 4 and auth.isdigit()))

        if not user:
            messagebox.showwarning("Incomplete", "Please enter your Username.")
        elif not item or "No items" in item:
            messagebox.showwarning("Incomplete", "Please select an item to return.")
        elif not auth_valid:
            messagebox.showwarning("Invalid Auth", "Auth Key must be empty or 4 digits.")
        else:
            # Append to loans.csv with RETURNED status
            with open("loans.csv", "a", newline="") as f:
                csv.writer(f).writerow([user, "N/A", item, "RETURNED", auth])

            messagebox.showinfo("Success", f"Item '{item}' returned successfully!")
            self.master.switch_frame(StartScreen)

if __name__ == "__main__":
    app = App()
    # Apply the theme to the specific app instance
    sv_ttk.set_theme("light")
    app.mainloop()