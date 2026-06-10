from __future__ import annotations  # makes all hints strings at runtime
import tkinter as tk
import socket
import random
import threading
from tkinter import messagebox

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from App import GyroPlotterApp  # only imported by type checkers, never at runtime


class MainPage(tk.Frame):
    def __init__(self, parent, contr):
        super().__init__(parent)
        self.contr = contr

        title = tk.Label(self, text="Main Menu", font=("Arial", 20))
        title.pack(pady=20, padx=40)

        interface_btn = tk.Button(
            self,
            text="Interface",
            command=lambda: self.open_interface(contr)
        )
        interface_btn.pack(pady=10)

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

    def open_interface(self, contr: GyroPlotterApp) -> None:
        if contr.l1_sensor is None or contr.s1_sensor is None:
            if contr.l1_sensor is None and contr.s1_sensor is None:
                msg = "Both l1 and s1 vertebrae sensors not set."
            else:
                msg = "s1" if contr.l1_sensor is None else "l1" + " vertebrae sensor not set."

            messagebox.showerror(
                "Setup Error",
                f"Unable to open interface.\n"
                    + msg,
                parent=self
            )
        else:
            contr.show_frame("InterfacePage")

    def send_to_esp(self, contr: GyroPlotterApp) -> None:
        """Send message to ESP on separate Thread"""
        thread = threading.Thread(target=self._esp_task, args=(contr,))
        thread.daemon = True
        thread.start()

    def _esp_task(self, contr: GyroPlotterApp) -> None:
        num = random.randint(0, 2)
        print(num)
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5)  # Don't hang forever
                s.connect((contr.ESP_IP, contr.SERVER_PORT))
                s.sendall(str(num).encode())
        except (ConnectionResetError, OSError) as e:
            print(f"Connection failed: {e}")