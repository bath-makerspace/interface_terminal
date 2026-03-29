import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageDraw
import csv
import sv_ttk
import os
import subprocess
from Bath_Cost_Code import Calculate_Personal_Cost


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Makerspace Debt Portal")
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


from tkinter import messagebox  # Add this to your imports at the top


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
        ttk.Label(left_col, text="(Only fill if paying now - 4 digits)", font=("Arial", 10, "italic")).pack(anchor="w")
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

        ttk.Button(btn_frame, text="Save & Exit", style="Accent.TButton",
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

class EquipChoiceScreen(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)

        label = ttk.Label(self, text="", font=("Arial", 24))
        label.pack(pady=100)

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
        label.pack(pady=100)

        btn1 = ttk.Button(self, text="Log New Print Debt",
                         command=lambda: master.switch_frame(PaymentInputScreen))
        btn1.pack(ipadx=20, ipady=10, pady=10)

        btn2 = ttk.Button(self, text="Mark Debt As Paid",
                         command=lambda: master.switch_frame(PaymentUpdateScreen))
        btn2.pack(ipadx=20, ipady=10, pady=10)

        btn3 = ttk.Button(self, text="Cancel",
                         command=lambda: master.switch_frame(StartScreen))
        btn3.pack(ipadx=20, ipady=10, pady=10)

if __name__ == "__main__":
    app = App()
    # Apply the theme to the specific app instance
    sv_ttk.set_theme("light")
    app.mainloop()