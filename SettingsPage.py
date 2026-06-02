import tkinter as tk

class SettingsPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        title = tk.Label(
            self,
            text="Sensor Settings",
            font=("Arial", 22, "bold")
        )
        title.pack(pady=20)

        sensor_frame = tk.Frame(self)
        sensor_frame.pack(pady=10)

        # Create sensor buttons
        for sensor_id in controller.sensor_ids:
            btn = tk.Button(
                sensor_frame,
                text=f"Open {sensor_id}",
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

        back_btn.pack(pady=20)