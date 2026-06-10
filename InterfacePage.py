from __future__ import annotations
import tkinter as tk
import math
import numpy as np
from tkinter import messagebox

from typing import TYPE_CHECKING
import threading
import random
import socket


if TYPE_CHECKING:
    from App import GyroPlotterApp


class InterfacePage(tk.Frame):
    def __init__(self, parent, contr):
        super().__init__(parent)
        self.config(bg="#f5f5f5")
        self.contr = contr

        self.base_x = 350
        self.base_y = 360
        self.max_degrees = 80
        self.body_length = 130
        self.head_radius = 28

        self.l1_offset = 0.
        self.s1_offset = 0.
        self.lumbar_offset = 0.
        self.calibrating_up = False
        self.cal_samples_l1 = []
        self.cal_samples_s1 = []

        self.feedback_label_states = {
            "GOOD": ("Good lifting posture: the back is almost straight.", "green"),
            "WARNING": ("Warning: the upper body is bending forward.", "orange"),
            "BAD": ("Bad lifting posture: the back is bending too much.", "red")
        }

        title_label = tk.Label(
            self,
            text="Lifting Posture Detection",
            font=("Arial", 24, "bold"),
            bg="#f5f5f5"
        )
        title_label.grid(row=0, column=1, columnspan=2)

        vis = tk.Frame(self)
        vis.grid(row=1, column=1, sticky="nsew")

        self.status_label = tk.Label(
            vis,
            text="Status: -",
            font=("Arial", 20, "bold"),
            bg="#f5f5f5"
        )
        self.status_label.pack()

        self.sensor_label = tk.Label(
            vis,
            text="Sensor value: -",
            font=("Arial", 14),
            bg="#f5f5f5"
        )
        self.sensor_label.pack(pady=5)

        self.canvas = tk.Canvas(
            vis,
            width=900,
            height=450,
            bg="white",
            highlightthickness=2,
            highlightbackground="#cccccc"
        )
        self.canvas.pack(pady=20)

        self.feedback_label = tk.Label(
            vis,
            text="Waiting for sensor data...",
            font=("Arial", 13),
            bg="#f5f5f5",
            wraplength=800
        )
        self.feedback_label.pack(pady=10)

        buttons = tk.Frame(self)
        buttons.grid(row=1, column=2, sticky="nsew")

        back_btn = tk.Button(
            buttons,
            text="Back",
            command=lambda: contr.show_frame("MainPage")
        )
        back_btn.pack(pady=10, side='top')

        self.cal_btn = tk.Button(
            buttons,
            text="Calibrate",
            command=self.start_cal_up
        )
        self.cal_btn.pack(pady=10, side='top')

        self.columnconfigure(0, weight=1)
        self.columnconfigure(3, weight=1)

        self.status = 0

    def determine_status(self, l1_angle: float, s1_angle: float) -> tuple[float, str, str, int]:
        raw_lumbar = self.angle_diff(s1_angle, l1_angle)
        print(l1_angle, s1_angle)

        lumbar_angle = self.angle_diff(raw_lumbar, self.lumbar_offset)
        angle_deg = np.rad2deg(lumbar_angle)

        if  30 > angle_deg  :
            return angle_deg, "GOOD", "green", 0
        elif  40 > angle_deg :
            return angle_deg, "WARNING", "orange", 1
        else :
            return angle_deg, "BAD", "red", 1


    def draw_stickman(self, l1_angle: float, s1_angle: float) -> None:
        self.canvas.delete("all")

        #base coordinates
        sensor_degrees, status, color, level = self.determine_status(l1_angle, s1_angle)
        if level != self.status:
            self.send_to_esp(self.contr)

        angle_degrees = min(sensor_degrees, self.max_degrees)
        angle_rad = math.radians(angle_degrees)

        hip_x = self.base_x
        hip_y = self.base_y - 90

        shoulder_x = hip_x + math.sin(angle_rad) * self.body_length
        shoulder_y = hip_y - math.cos(angle_rad) * self.body_length

        curve_strength = - math.sin(angle_rad) * 80

        mid_x = (hip_x + shoulder_x) / 2 + curve_strength
        mid_y = (hip_y + shoulder_y) / 2

        head_x = shoulder_x + math.sin(angle_rad) * 35
        head_y = shoulder_y - math.cos(angle_rad) * 35

        arm_start_x = shoulder_x
        arm_start_y = shoulder_y + 20

        hand_x = shoulder_x + 70
        hand_y = shoulder_y + 85

        box_x = hand_x + 20
        box_y = hand_y - 25

        ground_y = self.base_y + 20

        #ground line
        self.canvas.create_line(
            80, ground_y,
            820, ground_y,
            width=5,
            fill="#4CAF50"
        )

        #body line
        self.canvas.create_line(
            [hip_x, hip_y,
            mid_x, mid_y,
            shoulder_x, shoulder_y],
            width=7,
            fill=color,
            smooth=True
        )

        #head
        self.canvas.create_oval(
            head_x - self.head_radius,
            head_y - self.head_radius,
            head_x + self.head_radius,
            head_y + self.head_radius,
            width=3,
            outline="black",
            fill="#f2c6a0"
        )

        # head black
        self.canvas.create_oval(
            head_x + 10,
            head_y - 5,
            head_x + 14,
            head_y - 1,
            fill="black"
        )

        #leg1
        self.canvas.create_line(
            hip_x, hip_y,
            hip_x - 30, ground_y,
            width=4,
            fill="black"
        )

        #leg2
        self.canvas.create_line(
            hip_x, hip_y,
            hip_x + 50, ground_y,
            width=4,
            fill="black"
        )

        #feet1
        self.canvas.create_line(
            hip_x - 30, ground_y,
            hip_x - 60, ground_y,
            width=6,
            fill="black"
        )

        #feet2
        self.canvas.create_line(
            hip_x + 50, ground_y,
            hip_x + 80, ground_y,
            width=6,
            fill="black"
        )

        #arm1
        self.canvas.create_line(
            arm_start_x, arm_start_y,
            hand_x, hand_y,
            width=4,
            fill="black"
        )

        #arm2
        self.canvas.create_line(
            arm_start_x - 5, arm_start_y + 15,
            hand_x, hand_y + 35,
            width=4,
            fill="black"
        )

        self.canvas.create_rectangle(
            box_x, box_y,
            box_x + 75, box_y + 55,
            fill="#c49a6c",
            outline="black",
            width=2
        )

        self.canvas.create_text(
            box_x + 37,
            box_y + 27,
            text="BOX",
            font=("Arial", 10, "bold")
        )

        self.canvas.create_line(
            box_x + 37,
            box_y + 100,
            box_x + 37,
            box_y + 65,
            width=5,
            fill=color,
            arrow=tk.LAST
        )

        self.status_label.config(
            text=f"Status: {status}",
            fg=color
        )

        self.sensor_label.config(
            text=f"Sensor value: {sensor_degrees:.1f}°"
        )

        label_data = self.feedback_label_states[status]
        self.feedback_label.config(text=label_data[0], fg=label_data[1])

    def start_cal_up(self) -> None:
        self.calibrating_up = True
        self.cal_btn.config(state=tk.DISABLED, bg="#CCCCCC")

        messagebox.showinfo(
            "Calibration",
            f"Stand upright and completely still for 5 seconds.\n"
            f"Dialog will close automatically.",
            parent=self
        )

        self.contr.after(5000, self.finish_cal_up)

    @staticmethod
    def circular_mean(angles: list[float]) -> np.ndarray:
        return np.arctan2(
            np.mean(np.sin(angles)),
            np.mean(np.cos(angles))
        )

    @staticmethod
    def angle_diff(a, b) -> np.ndarray:
        """Returns a - b wrapped to [-pi, pi)."""
        return np.arctan2(
            np.sin(a - b),
            np.cos(a - b)
        )

    def finish_cal_up(self) -> None:
        self.cal_btn.config(state=tk.NORMAL, bg="#4CAF50")

        if not (self.cal_samples_l1 and self.cal_samples_s1):
            messagebox.showerror(
                "Calibration Error",
                "No samples collected!",
                parent=self
            )
            return

        self.l1_offset = self.circular_mean(self.cal_samples_l1)
        self.s1_offset = self.circular_mean(self.cal_samples_s1)
        self.lumbar_offset = self.angle_diff(self.s1_offset, self.l1_offset)

        self.cal_samples_l1 = []
        self.cal_samples_s1 = []

        messagebox.showinfo(
            "Calibration Complete",
            f"Bias of {np.rad2deg(self.l1_offset):.1f} degrees at l1.\n"
            f"Bias of {np.rad2deg(self.s1_offset):.1f} degrees at s1.\n"
            f"Lumbar Offset is {np.rad2deg(self.lumbar_offset):.1f} degrees.\n",
            parent=self
        )

    def collect_l1_cal_data(self, data: list[dict[str, tuple]]) -> None:
        """Collect l1 roll samples during calibration"""
        ori = -1 if self.contr.l1_ori == "LEFT" else 1
        with self.contr.lock:
            for datapoint in data:
                self.cal_samples_l1.append(datapoint["h_roll"] * ori)

    def collect_s1_cal_data(self, data: list[dict[str, tuple]]) -> None:
        """Collect s1 roll samples during calibration"""
        ori = -1 if self.contr.s1_ori == "LEFT" else 1

        with self.contr.lock:
            for datapoint in data:
                self.cal_samples_s1.append(datapoint["h_roll"] * ori)

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