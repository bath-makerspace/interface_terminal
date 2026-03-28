import tkinter as tk
from tkinter import ttk  # We need this for the themed widgets
from PIL import Image, ImageDraw
import csv
import sv_ttk

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Signature Application")
        self.geometry("1024x600")

        # Start with the Main Menu
        self.current_frame = None
        self.switch_frame(StartScreen)

    def switch_frame(self, frame_class):
        new_frame = frame_class(self)
        if self.current_frame is not None:
            self.current_frame.destroy()
        self.current_frame = new_frame
        self.current_frame.pack(fill="both", expand=True)

class StartScreen(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)

        label = ttk.Label(self, text="Welcome to the App", font=("Arial", 24))
        label.pack(pady=100)

        # Using style="Accent.TButton" (provided by sv_ttk) for the primary action
        btn1 = ttk.Button(self, text="Go to Signature Pad",
                         style="Accent.TButton",
                         command=lambda: master.switch_frame(SignatureScreen))
        btn1.pack(ipadx=20, ipady=10, pady=10)

        btn2 = ttk.Button(self, text="Go to Data Input",
                         command=lambda: master.switch_frame(InputScreen))
        btn2.pack(ipadx=20, ipady=10, pady=10)


class SignatureScreen(ttk.Frame): # Changed to ttk.Frame
    def __init__(self, master):
        super().__init__(master)
        self.master = master

        ttk.Label(self, text="Please Sign Below", font=("Arial", 18)).pack(pady=10)

        # Note: Canvas remains tk.Canvas (there is no ttk equivalent)
        # We manually set the highlightthickness to 0 so it blends with the dark theme
        self.canvas = tk.Canvas(self, bg="white", width=800, height=400,
                               relief="ridge", bd=0, highlightthickness=0)
        self.canvas.pack(pady=20)

        self.image = Image.new("RGB", (800, 400), "white")
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
        self.image = Image.new("RGB", (800, 400), "white")
        self.draw = ImageDraw.Draw(self.image)

    def save_sig(self):
        self.image.save("signature.png")
        self.master.switch_frame(StartScreen)

class InputScreen(ttk.Frame): # Changed to ttk.Frame
    def __init__(self, master):
        super().__init__(master)
        self.master = master

        ttk.Label(self, text="Log Your Entry", font=("Arial", 24)).pack(pady=50)

        # ttk.Entry looks much better with sv_ttk
        self.user_input = ttk.Entry(self, font=("Arial", 14), width=50)
        self.user_input.pack(pady=20)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=20)

        ttk.Button(btn_frame, text="Save to CSV & Close", style="Accent.TButton",
                  command=self.handle_save).pack(side="left", padx=10)

        ttk.Button(btn_frame, text="Back to Home",
                  command=lambda: master.switch_frame(StartScreen)).pack(side="left", padx=10)

    def handle_save(self):
        data = self.user_input.get()
        if data:
            with open("entries.csv", "a", newline="") as f:
                csv.writer(f).writerow([data])
            self.user_input.delete(0, tk.END)
            self.master.switch_frame(StartScreen)


if __name__ == "__main__":
    app = App()
    # Apply the theme to the specific app instance
    sv_ttk.set_theme("light")
    app.mainloop()