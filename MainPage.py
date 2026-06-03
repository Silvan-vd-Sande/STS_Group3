import tkinter as tk
import socket
import random
import threading
from Main import Controller

class MainPage(tk.Frame):
    def __init__(self, parent, contr):
        super().__init__(parent)

        title = tk.Label(self, text="Main Menu", font=("Arial", 20))
        title.pack(pady=20, padx=40)

        settings_btn = tk.Button(
            self,
            text="Go to Settings",
            command=lambda: contr.show_frame("SettingsPage")
        )
        settings_btn.pack(pady=10)

        extra_btn = tk.Button(
            self,
            text="Send Number",
            command=lambda: self.send_to_esp(contr)
        )
        extra_btn.pack(pady=10)

    def send_to_esp(self, contr: Controller) -> None:
        """Send message to ESP on separate Thread"""
        thread = threading.Thread(target=self._esp_task, args=(contr,))
        thread.daemon = True
        thread.start()

    def _esp_task(self, contr: Controller) -> None:
        num = random.randint(0, 2)
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5)  # Don't hang forever
                s.connect((contr.ESP_IP, contr.SERVER_PORT))
                s.sendall(str(num).encode())
        except (ConnectionResetError, OSError) as e:
            print(f"Connection failed: {e}")