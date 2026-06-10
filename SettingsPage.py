from __future__ import annotations  # makes all hints strings at runtime
import tkinter as tk
from tkinter import ttk

class SettingsPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        title = tk.Label(
            self,
            text="Sensor Settings",
            font=("Arial", 22, "bold")
        )
        title.grid(row=0, column=1, columnspan=3, pady=(16, 12), padx=20, sticky="ew")

        go_to = tk.Frame(self)
        go_to.grid(row=1, column=1, rowspan=3, padx=(40, 20), sticky="nsew")

        # Create sensor buttons
        for sensor_id in controller.sensor_ids:
            btn = tk.Button(
                go_to,
                text=f"Open {sensor_id}\nControl Panel",
                command=lambda sid=sensor_id: controller.open_sensor_window(sid),
                bg="#2196F3",
                fg="white",
                padx=10,
                pady=8,
                font=("Arial", 10)
            )

            btn.pack(pady=5)

        back_btn = tk.Button(
            self,
            text="Back",
            command=lambda: controller.show_frame("MainPage")
        )
        back_btn.grid(row=4, column=3, padx=20, pady=20, sticky="se")

        l1_frame = tk.Frame(self)
        l1_frame.grid(row=1, column=2, padx=20, sticky="nsew")

        l1_header = tk.Label(
            l1_frame,
            text="L1-Sensor"
        )
        l1_header.pack()

        # Combobox widget
        self.l1_sensor = ttk.Combobox(l1_frame, values=[*controller.sensor_ids, "None"], state="readonly")
        self.l1_sensor.set("None Selected")
        self.l1_sensor.pack()
        self.l1_sensor.bind('<<ComboboxSelected>>', self.l1_changed)

        self.l1_reading = tk.Label(
            l1_frame,
            text="No Sensor Selected"
        )
        self.l1_reading.pack()

        # l1 orientation
        self.l1_ori = ttk.Combobox(l1_frame, values=["RIGHT", "LEFT"], state="readonly")
        self.l1_ori.set(controller.l1_ori)
        self.l1_ori.pack()
        self.l1_ori.bind('<<ComboboxSelected>>', self.l1_ori_changed)

        s1_frame = tk.Frame(self)
        s1_frame.grid(row=1, column=3, padx=(20, 40), sticky="nsew")

        s1_header = tk.Label(
            s1_frame,
            text="S1-Sensor"
        )
        s1_header.pack()

        # Combobox widget
        self.s1_sensor = ttk.Combobox(s1_frame, values=[*controller.sensor_ids, "None"], state="readonly")
        self.s1_sensor.set("None Selected")
        self.s1_sensor.pack()
        self.s1_sensor.bind('<<ComboboxSelected>>', self.s1_changed)

        self.s1_reading = tk.Label(
            s1_frame,
            text="No Sensor Selected"
        )
        self.s1_reading.pack()

        # s1 orientation
        self.s1_ori = ttk.Combobox(s1_frame, values=["RIGHT", "LEFT"], state="readonly")
        self.s1_ori.set(controller.s1_ori)
        self.s1_ori.pack()
        self.s1_ori.bind('<<ComboboxSelected>>', self.s1_ori_changed)

        self.columnconfigure(0, weight=1)
        self.columnconfigure(4, weight=1)

    def l1_changed(self, event: tk.Event) -> None:
        val = self.l1_sensor.get()
        if val == "None":
            self.l1_reading.config(text="No Sensor Selected")
            self.controller.l1_sensor = None
        else:
            self.controller.l1_sensor = val

    def s1_changed(self, event: tk.Event) -> None:
        val = self.s1_sensor.get()
        if val == "None":
            self.s1_reading.config(text="No Sensor Selected")
            self.controller.s1_sensor = None
        else:
            self.controller.s1_sensor = val

    def l1_ori_changed(self, event: tk.Event) -> None:
        self.controller.l1_ori = self.l1_ori.get()
        print(self.controller.l1_ori, self.controller.l1_ori == "LEFT")

    def s1_ori_changed(self, event: tk.Event) -> None:
        self.controller.s1_ori = self.s1_ori.get()
