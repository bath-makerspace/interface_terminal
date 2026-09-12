import tkinter as tk
import serial
import time


class RFIDScannerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("RFID Scanner")

        # Make the window full screen for the 7" touch display
        self.root.attributes("-fullscreen", True)
        self.root.configure(bg="#2c3e50")  # Dark theme for better visibility

        # Application State Variables
        self.is_scanning = False
        self.unique_tags = set()
        self.scan_start_time = 0

        # Setup Serial Port
        # Raspberry Pi GPIO UART is usually /dev/serial0 (or /dev/ttyS0 / /dev/ttyAMA0)
        # timeout=0 makes it non-blocking, which is critical for GUI apps!
        try:
            self.ser = serial.Serial('/dev/serial0', 9600, timeout=0)
        except Exception as e:
            print(f"Warning: Serial port not found or permission denied. {e}")
            self.ser = None

        self.build_ui()

    def build_ui(self):
        # Styling parameters for easy touch on a 7" screen
        btn_font = ("Helvetica", 18, "bold")
        lbl_font = ("Helvetica", 20)

        # --- TOP FRAME (Controls & Timer) ---
        top_frame = tk.Frame(self.root, bg="#2c3e50")
        top_frame.pack(side=tk.TOP, fill=tk.X, pady=20)

        self.start_btn = tk.Button(top_frame, text="Start Scan", font=btn_font, bg="#27ae60", fg="white", width=10,
                                   command=self.start_scan)
        self.start_btn.pack(side=tk.LEFT, padx=30)

        self.stop_btn = tk.Button(top_frame, text="Stop Scan", font=btn_font, bg="#e74c3c", fg="white", width=10,
                                  state=tk.DISABLED, command=self.stop_scan)
        self.stop_btn.pack(side=tk.LEFT, padx=10)

        self.timer_label = tk.Label(top_frame, text="Time: 00:00:00", font=lbl_font, bg="#2c3e50", fg="white")
        self.timer_label.pack(side=tk.RIGHT, padx=40)

        # --- MIDDLE FRAME (Data Display) ---
        mid_frame = tk.Frame(self.root, bg="#2c3e50")
        mid_frame.pack(expand=True, fill=tk.BOTH, padx=40, pady=20)

        self.count_label = tk.Label(mid_frame, text="Unique Cards Scanned: 0", font=("Helvetica", 28, "bold"),
                                    bg="#2c3e50", fg="#f1c40f")
        self.count_label.pack(pady=15)

        # Scrollbar and Listbox for scanned tags
        scrollbar = tk.Scrollbar(mid_frame, width=40)  # Extra wide scrollbar for touch
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tag_listbox = tk.Listbox(mid_frame, font=("Helvetica", 16), yscrollcommand=scrollbar.set,
                                      selectbackground="#34495e")
        self.tag_listbox.pack(expand=True, fill=tk.BOTH)
        scrollbar.config(command=self.tag_listbox.yview)

        # --- BOTTOM FRAME (Exit) ---
        bottom_frame = tk.Frame(self.root, bg="#2c3e50")
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=20)

        self.exit_btn = tk.Button(bottom_frame, text="Exit Application", font=btn_font, bg="#95a5a6", height=2,
                                  command=self.exit_app)
        self.exit_btn.pack(fill=tk.X, padx=40)

    def start_scan(self):
        if not self.is_scanning:
            self.is_scanning = True

            # Update Button States
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)

            self.scan_start_time = time.time()

            # Kick off the event loops
            self.update_timer()
            self.poll_rfid()

    def stop_scan(self):
        self.is_scanning = False

        # Update Button States
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)

    def update_timer(self):
        if self.is_scanning:
            elapsed = int(time.time() - self.scan_start_time)
            hours, remainder = divmod(elapsed, 3600)
            minutes, seconds = divmod(remainder, 60)

            time_str = f"Time: {hours:02d}:{minutes:02d}:{seconds:02d}"
            self.timer_label.config(text=time_str)

            # Schedule the next timer update in 1000ms (1 second)
            self.root.after(1000, self.update_timer)

    def poll_rfid(self):
        """Poll the serial port every 200ms without freezing the GUI."""
        if self.is_scanning:
            if self.ser and self.ser.in_waiting > 0:
                try:
                    # Read the incoming bytes and decode.
                    # Seeed modules usually send a stream ending with \n or \r
                    tag_data = self.ser.readline().decode('utf-8').strip()

                    if tag_data and tag_data not in self.unique_tags:
                        self.unique_tags.add(tag_data)

                        # Update Counter
                        self.count_label.config(text=f"Unique Cards Scanned: {len(self.unique_tags)}")

                        # Insert new tag at the top of the listbox
                        timestamp = time.strftime('%H:%M:%S')
                        self.tag_listbox.insert(0, f"[{timestamp}] Tag ID: {tag_data}")
                except Exception as e:
                    print(f"Error reading serial data: {e}")

            # Schedule the next serial port poll in 200ms
            self.root.after(200, self.poll_rfid)

    def exit_app(self):
        self.is_scanning = False
        if self.ser:
            self.ser.close()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = RFIDScannerApp(root)
    root.mainloop()