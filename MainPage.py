import tkinter as tk
import socket
import random
import threading


class MainPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        title = tk.Label(self, text="Main Menu", font=("Arial", 20))
        title.pack(pady=20, padx=40)

        settings_btn = tk.Button(
            self,
            text="Go to Settings",
            command=lambda: controller.show_frame("SettingsPage")
        )
        settings_btn.pack(pady=10)

        extra_btn = tk.Button(
            self,
            text="Send Number",
            command=lambda: self.send_to_esp(controller)
        )
        extra_btn.pack(pady=10)

    def send_to_esp(self, controller):
        thread = threading.Thread(target=self._esp_task, args=(controller,))
        thread.daemon = True
        thread.start()

    def _esp_task(self, controller):
        num = random.randint(0, 2)
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5)  # Don't hang forever
                s.connect((controller.ESP_IP, controller.SERVER_PORT))
                s.sendall(str(num).encode())
        except (ConnectionResetError, OSError) as e:
            print(f"Connection failed: {e}")