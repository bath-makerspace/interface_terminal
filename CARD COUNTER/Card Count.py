import tkinter as tk
import time
import board
import busio
from adafruit_pn532.i2c import PN532_I2C


class RFIDScannerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("NFC Scanner")
        self.root.attributes("-fullscreen", True)
        self.root.configure(bg="#2c3e50")

        # Application State
        self.is_scanning = False
        self.unique_tags = set()
        self.scan_start_time = 0
        self.pn532 = None
        self.i2c = None

        # Start with the initialization UI
        self.build_init_ui()

        # Schedule the hardware check 500ms after the UI loads so the user sees the message
        self.root.after(500, self.attempt_hardware_init)

    def build_init_ui(self):
        """Builds the startup screen that shows while detecting hardware."""
        self.init_frame = tk.Frame(self.root, bg="#2c3e50")
        self.init_frame.pack(expand=True, fill=tk.BOTH)

        # Center content
        inner_frame = tk.Frame(self.init_frame, bg="#2c3e50")
        inner_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        self.status_label = tk.Label(inner_frame, text="Detecting NFC Reader...", font=("Helvetica", 28, "bold"),
                                     bg="#2c3e50", fg="white")
        self.status_label.pack(pady=20)

        # Buttons (Hidden by default, shown if init fails)
        self.btn_frame = tk.Frame(inner_frame, bg="#2c3e50")

        self.retry_btn = tk.Button(self.btn_frame, text="Retry Connection", font=("Helvetica", 18, "bold"),
                                   bg="#3498db", fg="white", width=15, command=self.retry_init)
        self.retry_btn.pack(side=tk.LEFT, padx=10)

        self.init_exit_btn = tk.Button(self.btn_frame, text="Exit App", font=("Helvetica", 18, "bold"), bg="#e74c3c",
                                       fg="white", width=10, command=self.exit_app)
        self.init_exit_btn.pack(side=tk.LEFT, padx=10)

    def retry_init(self):
        """Resets the UI and tries to connect again."""
        self.btn_frame.pack_forget()
        self.status_label.config(text="Detecting NFC Reader...", fg="white")
        self.root.after(500, self.attempt_hardware_init)

    def attempt_hardware_init(self):
        """Tries to initialize the I2C bus and the PN532 module."""
        try:
            # Clean up old I2C if a previous attempt failed
            if self.i2c:
                self.i2c.deinit()

            self.i2c = busio.I2C(board.SCL, board.SDA)
            self.pn532 = PN532_I2C(self.i2c, debug=False)
            self.pn532.SAM_configuration()

            # If we reach here, it succeeded. Destroy init screen and load main UI.
            self.init_frame.destroy()
            self.build_main_ui()

        except Exception as e:
            print(f"Hardware initialization failed: {e}")
            self.status_label.config(text="Failed to detect NFC Reader.\nCheck wiring on I2C pins.", fg="#e74c3c")
            # Show the Retry and Exit buttons
            self.btn_frame.pack(pady=20)

    def build_main_ui(self):
        """Builds the main scanner interface."""
        btn_font = ("Helvetica", 18, "bold")
        lbl_font = ("Helvetica", 20)

        # --- TOP FRAME ---
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

        # --- MIDDLE FRAME ---
        mid_frame = tk.Frame(self.root, bg="#2c3e50")
        mid_frame.pack(expand=True, fill=tk.BOTH, padx=40, pady=20)

        self.count_label = tk.Label(mid_frame, text="Unique Cards Scanned: 0", font=("Helvetica", 28, "bold"),
                                    bg="#2c3e50", fg="#f1c40f")
        self.count_label.pack(pady=15)

        scrollbar = tk.Scrollbar(mid_frame, width=40)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tag_listbox = tk.Listbox(mid_frame, font=("Helvetica", 16), yscrollcommand=scrollbar.set,
                                      selectbackground="#34495e")
        self.tag_listbox.pack(expand=True, fill=tk.BOTH)
        scrollbar.config(command=self.tag_listbox.yview)

        # --- BOTTOM FRAME ---
        bottom_frame = tk.Frame(self.root, bg="#2c3e50")
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=20)

        self.exit_btn = tk.Button(bottom_frame, text="Exit Application", font=btn_font, bg="#95a5a6", height=2,
                                  command=self.exit_app)
        self.exit_btn.pack(fill=tk.X, padx=40)

    def start_scan(self):
        if not self.is_scanning:
            self.is_scanning = True
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.scan_start_time = time.time()

            self.update_timer()
            self.poll_rfid()

    def stop_scan(self):
        self.is_scanning = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)

    def update_timer(self):
        if self.is_scanning:
            elapsed = int(time.time() - self.scan_start_time)
            hours, remainder = divmod(elapsed, 3600)
            minutes, seconds = divmod(remainder, 60)

            time_str = f"Time: {hours:02d}:{minutes:02d}:{seconds:02d}"
            self.timer_label.config(text=time_str)
            self.root.after(1000, self.update_timer)

    def poll_rfid(self):
        if self.is_scanning and self.pn532:
            try:
                uid = self.pn532.read_passive_target(timeout=0.05)

                if uid is not None:
                    tag_data = ":".join([hex(i)[2:].zfill(2).upper() for i in uid])

                    if tag_data not in self.unique_tags:
                        self.unique_tags.add(tag_data)
                        self.count_label.config(text=f"Unique Cards Scanned: {len(self.unique_tags)}")

                        timestamp = time.strftime('%H:%M:%S')
                        self.tag_listbox.insert(0, f"[{timestamp}] Tag ID: {tag_data}")
            except Exception as e:
                print(f"Error reading NFC data: {e}")

            self.root.after(200, self.poll_rfid)

    def exit_app(self):
        self.is_scanning = False
        if self.i2c:
            self.i2c.deinit()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = RFIDScannerApp(root)
    root.mainloop()