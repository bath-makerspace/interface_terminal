import tkinter as tk
import time
import serial
import csv
import datetime
from adafruit_pn532.uart import PN532_UART


class RFIDScannerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("NFC Scanner (UART)")
        self.root.attributes("-fullscreen", True)
        self.root.configure(bg="#2c3e50")

        # Application State
        self.is_scanning = False
        self.unique_tags = set()
        self.all_scans = []  # Stores every individual scan

        self.scan_start_time = 0
        self.scan_start_datetime = None

        # Debounce variables to prevent flooding when a card is held
        self.last_scanned_tag = None
        self.last_scanned_time = 0

        self.pn532 = None
        self.uart_connection = None

        self.build_init_ui()
        self.root.after(500, self.attempt_hardware_init)

    def build_init_ui(self):
        self.init_frame = tk.Frame(self.root, bg="#2c3e50")
        self.init_frame.pack(expand=True, fill=tk.BOTH)

        inner_frame = tk.Frame(self.init_frame, bg="#2c3e50")
        inner_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        self.status_label = tk.Label(inner_frame, text="Detecting NFC Reader...", font=("Helvetica", 28, "bold"),
                                     bg="#2c3e50", fg="white")
        self.status_label.pack(pady=20)

        self.btn_frame = tk.Frame(inner_frame, bg="#2c3e50")

        self.retry_btn = tk.Button(self.btn_frame, text="Retry Connection", font=("Helvetica", 18, "bold"),
                                   bg="#3498db", fg="white", width=15, command=self.retry_init)
        self.retry_btn.pack(side=tk.LEFT, padx=10)

        self.init_exit_btn = tk.Button(self.btn_frame, text="Exit App", font=("Helvetica", 18, "bold"), bg="#e74c3c",
                                       fg="white", width=10, command=self.exit_app)
        self.init_exit_btn.pack(side=tk.LEFT, padx=10)

    def retry_init(self):
        self.btn_frame.pack_forget()
        self.status_label.config(text="Detecting NFC Reader...", fg="white")
        self.root.after(500, self.attempt_hardware_init)

    def attempt_hardware_init(self):
        try:
            if self.uart_connection:
                self.uart_connection.close()

            self.uart_connection = serial.Serial("/dev/serial0", baudrate=115200, timeout=0.1)
            self.pn532 = PN532_UART(self.uart_connection, debug=False)
            self.pn532.SAM_configuration()

            self.init_frame.destroy()
            self.build_main_ui()

        except Exception as e:
            print(f"Hardware initialization failed: {e}")
            self.status_label.config(text="Failed to detect NFC Reader.\nCheck UART wiring and serial config.",
                                     fg="#e74c3c")
            self.btn_frame.pack(pady=20)

    def build_main_ui(self):
        btn_font = ("Helvetica", 18, "bold")
        lbl_font = ("Helvetica", 20)

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

            # Reset lists and UI for a fresh scan session
            self.unique_tags.clear()
            self.all_scans = []
            self.tag_listbox.delete(0, tk.END)
            self.count_label.config(text="Unique Cards Scanned: 0")

            self.scan_start_time = time.time()
            self.scan_start_datetime = datetime.datetime.now()

            self.update_timer()
            self.poll_rfid()

    def stop_scan(self):
        if self.is_scanning:
            self.is_scanning = False
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.generate_csv()

    def generate_csv(self):
        stop_dt = datetime.datetime.now()
        # Format: Cardscans_[YYYY-MM-DD_HH-MM-SS].csv
        filename = f"Cardscans_[{stop_dt.strftime('%Y-%m-%d_%H-%M-%S')}].csv"

        try:
            with open(filename, mode='w', newline='') as file:
                writer = csv.writer(file)

                # Write the 3 header rows required
                start_str = self.scan_start_datetime.strftime('%Y-%m-%d %H:%M:%S')
                stop_str = stop_dt.strftime('%Y-%m-%d %H:%M:%S')

                writer.writerow(["Scan Started", start_str])
                writer.writerow(["Scan Stopped", stop_str])
                writer.writerow(["Unique Cards Scanned", len(self.unique_tags)])

                # Write all individual scans
                for scan_time, tag in self.all_scans:
                    writer.writerow([scan_time, tag])

            print(f"Successfully saved {filename}")
        except Exception as e:
            print(f"Failed to save CSV: {e}")

    def update_timer(self):
        if self.is_scanning:
            elapsed = int(time.time() - self.scan_start_time)

            # Auto-stop after 12 hours (43200 seconds)
            if elapsed >= 43200:
                self.stop_scan()
                return

            hours, remainder = divmod(elapsed, 3600)
            minutes, seconds = divmod(remainder, 60)

            self.timer_label.config(text=f"Time: {hours:02d}:{minutes:02d}:{seconds:02d}")
            self.root.after(1000, self.update_timer)

    def poll_rfid(self):
        if self.is_scanning and self.pn532:
            try:
                uid = self.pn532.read_passive_target(timeout=0.05)
                current_time = time.time()

                if uid is not None:
                    tag_data = ":".join([hex(i)[2:].zfill(2).upper() for i in uid])

                    # Debounce: Ignore if it's the exact same card held against the reader for less than 2 seconds
                    if tag_data == self.last_scanned_tag and (current_time - self.last_scanned_time) < 2.0:
                        pass
                    else:
                        self.last_scanned_tag = tag_data
                        self.last_scanned_time = current_time

                        # Keep track of unique cards
                        if tag_data not in self.unique_tags:
                            self.unique_tags.add(tag_data)
                            self.count_label.config(text=f"Unique Cards Scanned: {len(self.unique_tags)}")

                        # Log every valid tap (unique or duplicate)
                        timestamp_str = time.strftime('%H:%M:%S')
                        self.all_scans.append((timestamp_str, tag_data))
                        self.tag_listbox.insert(0, f"[{timestamp_str}] Tag ID: {tag_data}")
                else:
                    # If no card is detected, clear the last tag so they can tap the same card repeatedly if they pull it away
                    self.last_scanned_tag = None

            except Exception as e:
                print(f"Error reading NFC data: {e}")

            self.root.after(200, self.poll_rfid)

    def exit_app(self):
        # Ensure we save a CSV if the user exits while a scan is actively running
        if self.is_scanning:
            self.stop_scan()

        if self.uart_connection:
            self.uart_connection.close()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = RFIDScannerApp(root)
    root.mainloop()