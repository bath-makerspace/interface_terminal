import tkinter as tk
from PIL import Image, ImageDraw

class SignaturePad:
    def __init__(self, root):
        self.root = root
        self.root.title("Signature Pad")

        # Track the last known mouse position
        self.last_x, self.last_y = None, None

        self.canvas = tk.Canvas(root, bg="white", width=1024, height=600)
        self.canvas.pack(pady=20)

        self.image = Image.new("RGB", (400, 200), "white")
        self.draw = ImageDraw.Draw(self.image)

        # Bind mouse movement AND mouse release
        self.canvas.bind("<B1-Motion>", self.paint)
        self.canvas.bind("<ButtonRelease-1>", self.reset_coords)

        tk.Button(root, text="Save & Upload", command=self.save_sig).pack(side="left", padx=50)
        tk.Button(root, text="Clear", command=self.clear).pack(side="right", padx=50)

    def paint(self, event):
        if self.last_x and self.last_y:
            # Draw a continuous line from the last point to the current point
            # On the screen:
            self.canvas.create_line(self.last_x, self.last_y, event.x, event.y,
                                    width=3, fill="black", capstyle=tk.ROUND, smooth=True)
            # On the hidden PIL image:
            self.draw.line([self.last_x, self.last_y, event.x, event.y], fill="black", width=3)

        # Update the last position
        self.last_x, self.last_y = event.x, event.y

    def reset_coords(self, event):
        # Reset coordinates when the mouse is lifted so lines don't jump
        self.last_x, self.last_y = None, None

    def clear(self):
        self.canvas.delete("all")
        self.image = Image.new("RGB", (400, 200), "white")
        self.draw = ImageDraw.Draw(self.image)

    def save_sig(self):
        self.image.save("signature.png")
        print("Check your folder for 'signature.png' to see the line in action!")


if __name__ == "__main__":
    root = tk.Tk()
    app = SignaturePad(root)
    root.mainloop()