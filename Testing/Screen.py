import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageDraw
import csv
import sv_ttk
import subprocess  # Required for launching the keyboard
from Bath_Cost_Code import Calculate_Personal_Cost


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Makerspace Debt Portal")
        self.geometry("1024x600")

        # Track the keyboard process globally so we can kill it from any screen
        self.kb_process = None

        self.current_frame = None
        self.switch_frame(StartScreen)

    def switch_frame(self, frame_class):
        # Kill keyboard if it's open when we switch screens
        self.close_keyboard()

        new_frame = frame_class(self)
        if self.current_frame is not None:
            self.current_frame.destroy()
        self.current_frame = new_frame
        self.current_frame.pack(fill="both", expand=True)

    def open_keyboard(self, event=None):
        """Launches the onboard virtual keyboard if not already running."""
        try:
            if self.kb_process is None or self.kb_process.poll() is not None:
                self.kb_process = subprocess.Popen(["onboard"])
        except FileNotFoundError:
            print("Error: Onboard is not installed. Run 'sudo apt install onboard'")

    def close_keyboard(self):
        """Terminates the virtual keyboard process."""
        if self.kb_process and self.kb_process.poll() is None:
            self.kb_process.terminate()
            self.kb_process = None

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


class PaymentInputScreen(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master

        ttk.Label(self, text="Add to tab", font=("Arial", 16)).pack(pady=30)

        # Username Entry
        ttk.Label(self, text="Username", font=("Arial", 12)).pack(pady=5)
        self.username = ttk.Entry(self, font=("Arial", 12), width=20)
        self.username.pack(pady=15)
        # Bind tap to open keyboard
        self.username.bind("<Button-1>", self.master.open_keyboard)

        # Print Mass Entry
        ttk.Label(self, text="Print mass (g)", font=("Arial", 12)).pack(pady=5)
        self.print_mass = ttk.Entry(self, font=("Arial", 12), width=10)
        self.print_mass.pack(pady=15)
        # Bind tap to open keyboard
        self.print_mass.bind("<Button-1>", self.master.open_keyboard)

        # Result display
        self.result_label = ttk.Label(self, text="Total Cost: £0.00", font=("Arial", 14, "bold"))
        self.result_label.pack(pady=10)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=20)

        # FIXED: Using a local method instead of calling the function directly
        ttk.Button(btn_frame, text="Calculate Cost", style="Accent.TButton",
                   command=self.update_display).pack(side="left", padx=10)

        ttk.Button(btn_frame, text="Save to CSV & Close", style="Accent.TButton",
                   command=self.handle_save).pack(side="left", padx=10)

        ttk.Button(btn_frame, text="Cancel",
                   command=lambda: master.switch_frame(StartScreen)).pack(side="left", padx=10)

    def update_display(self):
        """Gets value from entry and updates the UI label."""
        weight_text = self.print_mass.get()
        if weight_text.strip():
            # Pass the text string to your math function
            cost = Calculate_Personal_Cost(weight_text)
            self.result_label.config(text=f"Total Cost: £{cost:.2f}")
            return cost
        return 0.0

    def handle_save(self):
        user = self.username.get()
        cost = self.update_display()  # Ensure we have the latest cost

        if user and cost > 0:
            with open("entries.csv", "a", newline="") as f:
                csv.writer(f).writerow([user, cost])

            self.username.delete(0, tk.END)
            self.print_mass.delete(0, tk.END)
            # Keyboard is closed automatically by switch_frame
            self.master.switch_frame(StartScreen)

class SignatureScreen(ttk.Frame): # Changed to ttk.Frame
    canvaswidth = 300
    canvasheight = 200
    def __init__(self, master):
        super().__init__(master)
        self.master = master

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

        btn_frame = ttk.Frame(self) # Changed to ttk.Frame
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
        self.image = Image.new("RGB", (self.canvaswidth , self.canvasheight), "white")
        self.draw = ImageDraw.Draw(self.image)

    def save_sig(self):
        self.image.save("signature.png")
        self.master.switch_frame(StartScreen)

if __name__ == "__main__":
    app = App()
    # Apply the theme to the specific app instance
    sv_ttk.set_theme("light")
    app.mainloop()