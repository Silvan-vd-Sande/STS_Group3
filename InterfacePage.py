import tkinter as tk
import math
import numpy as np

class InterfacePage(tk.Frame):
    def __init__(self, parent, contr):
        super().__init__(parent)
        self.contr = contr
        self.config(bg="#f5f5f5")

        self.base_x = 350
        self.base_y = 360
        self.max_degrees = 80
        self.body_length = 130
        self.head_radius = 28

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
        title_label.pack(pady=15)

        self.status_label = tk.Label(
            self,
            text="Status: -",
            font=("Arial", 20, "bold"),
            bg="#f5f5f5"
        )
        self.status_label.pack()

        self.sensor_label = tk.Label(
            self,
            text="Sensor value: -",
            font=("Arial", 14),
            bg="#f5f5f5"
        )
        self.sensor_label.pack(pady=5)

        self.canvas = tk.Canvas(
            self,
            width=900,
            height=500,
            bg="white",
            highlightthickness=2,
            highlightbackground="#cccccc"
        )
        self.canvas.pack(pady=20)

        self.feedback_label = tk.Label(
            self,
            text="Waiting for sensor data...",
            font=("Arial", 13),
            bg="#f5f5f5",
            wraplength=800
        )
        self.feedback_label.pack(pady=10)

        back_btn = tk.Button(
            self,
            text="Back",
            command=lambda: contr.show_frame("MainPage")
        )
        back_btn.pack(pady=10)

    @staticmethod
    def determine_status(sensor_rad):
        sensor_degrees = np.rad2deg(sensor_rad)

        if  30 > sensor_degrees  :
            return "GOOD", "green"
        elif  40 > sensor_degrees > 30 :
            return "WARNING", "orange"
        else :
            return "BAD", "red"


    def draw_stickman(self, sensor_rad):
        self.canvas.delete("all")

        #base coordinates
        status, color = self.determine_status(sensor_rad)
        sensor_degrees = math.degrees(sensor_rad)

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
            hip_x, hip_y,
            mid_x, mid_y,
            shoulder_x, shoulder_y,
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
