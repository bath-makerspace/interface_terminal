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


class PaymentInputScreen(ttk.Frame):
    canvaswidth = 300
    canvasheight = 200
    def __init__(self, master):

        super().__init__(master)
        self.master = master

        # Bind the background of this screen to close the keyboard
        self.bind("<Button-1>", lambda e: self.master.close_keyboard())

        ttk.Label(self, text="Add to Tab", font=("Arial", 18, "bold")).pack(pady=10)

        # Username
        ttk.Label(self, text="Username", font=("Arial", 12)).pack()
        self.username = ttk.Entry(self, font=("Arial", 14), width=25)
        self.username.pack(pady=10)
        self.username.bind("<Button-1>", lambda e: self.master.open_keyboard(mode="full"))
        # Close keyboard when 'Enter' is pressed
        self.username.bind("<Return>", lambda e: self.master.close_keyboard())

        # Mass
        ttk.Label(self, text="Print Mass (nearest gram)", font=("Arial", 12)).pack()
        self.print_mass = ttk.Entry(self, font=("Arial", 14), width=15)
        self.print_mass.pack(pady=10)
        self.print_mass.bind("<Button-1>", lambda e: self.master.open_keyboard(mode="numeric"))
        # Run calculation AND close keyboard when 'Enter' is pressed
        self.print_mass.bind("<Return>", self.handle_enter_key)

        self.cost_display = ttk.Label(self, text="Cost: £0.00", font=("Arial", 16, "bold"))
        self.cost_display.pack(pady=10)

        ttk.Label(self, text="Authentication Key", font=("Arial", 12)).pack()
        ttk.Label(self, text="(Committee Will Fill When You Pay)", font=("Arial", 12)).pack()
        self.auth_key = ttk.Entry(self, font=("Arial", 14), width=15)
        self.auth_key.pack(pady=10)
        self.auth_key.bind("<Button-1>", lambda e: self.master.open_keyboard(mode="numeric"))
        # Run calculation AND close keyboard when 'Enter' is pressed
        self.auth_key.bind("<Return>", self.handle_enter_key)

        ttk.Label(self, text="Please Sign Below", font=("Arial", 18)).pack(pady=10)
        # Note: Canvas remains tk.Canvas (there is no ttk equivalent)
        # We manually set the highlightthickness to 0 so it blends with the dark theme
        self.canvas = tk.Canvas(self, bg="white", width=self.canvaswidth, height=self.canvasheight,
                                relief="ridge", bd=0, highlightthickness=0)
        self.canvas.pack(pady=20)

        self.image = Image.new("RGB", (self.canvaswidth, self.canvasheight), "white")
        self.draw = ImageDraw.Draw(self.image)
        self.last_x, self.last_y = None, None

        self.canvas.bind("<B1-Motion>", self.paint)
        self.canvas.bind("<ButtonRelease-1>", self.reset_coords)

        btn_frame = ttk.Frame(self)  # Changed to ttk.Frame
        btn_frame.pack(pady=10)

        # ttk.Buttons do not support 'bg' or 'fg'. sv_ttk uses styles instead.
        ttk.Button(btn_frame, text="Save & Close", style="Accent.TButton",
                   command=self.save_sig).pack(side="left", padx=20)

        ttk.Button(btn_frame, text="Clear",
                   command=self.clear).pack(side="left", padx=20)

        ttk.Button(btn_frame, text="Back to Home",
                   command=lambda: master.switch_frame(StartScreen)).pack(side="left", padx=20)

    def paint(self, event):
        if self.last_x and self.last_y:
            self.canvas.create_line(self.last_x, self.last_y, event.x, event.y,
                                    width=4, fill="black", capstyle=tk.ROUND, smooth=True)
            self.draw.line([self.last_x, self.last_y, event.x, event.y], fill="black", width=4)
        self.last_x, self.last_y = event.x, event.y

    def reset_coords(self, event):
        self.last_x, self.last_y = None, None

    def clear(self):
        self.canvas.delete("all")
        self.image = Image.new("RGB", (self.canvaswidth, self.canvasheight), "white")
        self.draw = ImageDraw.Draw(self.image)

    def save_sig(self):
        self.image.save("signature.png")
        self.master.switch_frame(StartScreen)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=20)

        ttk.Button(btn_frame, text="Save & Exit", style="Accent.TButton",
                   command=self.handle_save).pack(side="left", padx=10)

        ttk.Button(btn_frame, text="Cancel",
                   command=lambda: self.master.switch_frame(StartScreen)).pack(side="left", padx=10)

    def handle_enter_key(self, event):
        """Triggered when user hits Enter/Return on the virtual keyboard."""
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
        user = self.username.get()
        price = self.update_price()
        auth = self.auth_key.get()
        if user and price and auth:
            with open("entries.csv", "a", newline="") as f:
                csv.writer(f).writerow([user, price, auth])
            self.master.switch_frame(StartScreen)

class StartScreen(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)

        label = ttk.Label(self, text="Welcome To The Makerspace Debt Portal", font=("Arial", 24))
        label.pack(pady=100)

        # Using style="Accent.TButton" (provided by sv_ttk) for the primary action
        # btn1 = ttk.Button(self, text="Test Signature Pad",
        #                  style="Accent.TButton",
        #                  command=lambda: master.switch_frame(SignatureScreen))
        # btn1.pack(ipadx=20, ipady=10, pady=10)

        btn2 = ttk.Button(self, text="Log 3D Print Debt",
                         command=lambda: master.switch_frame(PaymentInputScreen))
        btn2.pack(ipadx=20, ipady=10, pady=10)

        btn2 = ttk.Button(self, text="Equipment",
                         command=lambda: master.switch_frame(EquipChoiceScreen))
        btn2.pack(ipadx=20, ipady=10, pady=10)

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

class SignatureScreen(ttk.Frame): # Changed to ttk.Frame
    pass

if __name__ == "__main__":
    app = App()
    # Apply the theme to the specific app instance
    sv_ttk.set_theme("light")
    app.mainloop()