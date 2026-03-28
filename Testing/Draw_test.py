import tkinter as tk
from PIL import Image, ImageDraw

class SignaturePad:
    def __init__(self, root):
        self.root = root
        self.canvas = tk.Canvas(root, bg="white", width=400, height=200)
        self.canvas.pack(pady=20)
        
        # Create a blank PIL image to draw on in the background
        self.image = Image.new("RGB", (400, 200), "white")
        self.draw = ImageDraw.Draw(self.image)
        
        self.canvas.bind("<B1-Motion>", self.paint)
        
        tk.Button(root, text="Save & Upload", command=self.save_sig).pack()
        tk.Button(root, text="Clear", command=self.clear).pack()

    def paint(self, event):
        x1, y1 = (event.x - 1), (event.y - 1)
        x2, y2 = (event.x + 1), (event.y + 1)
        self.canvas.create_oval(x1, y1, x2, y2, fill="black", width=3)
        self.draw.line([x1, y1, x2, y2], fill="black", width=3)

    def clear(self):
        self.canvas.delete("all")
        self.image = Image.new("RGB", (400, 200), "white")
        self.draw = ImageDraw.Draw(self.image)

    def save_sig(self):
        self.image.save("signature.png")
        # Trigger your upload function here
        print("Signature saved locally!")