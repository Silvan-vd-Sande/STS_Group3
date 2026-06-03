import threading
import tkinter as tk
from collections import deque
from SensorWindow import SensorControlPanel
from math import atan2, sqrt, sin, cos, pi
from MainPage import MainPage
from SettingsPage import SettingsPage
import numpy as np
#from AngleKalman1D import *
import socket


def wrap_pi(angle):
    """
    Wrap angle to [-pi, pi].
    """
    return (angle + pi) % (2.0 * pi) - pi


class GyroPlotterApp(tk.Tk):
    """Main application window - overview plot and sensor management"""

    def __init__(self, controller, sensor_ids):
        super().__init__()

        self.title("Gyroscope Live Plotter")
        self.geometry("1200x700")

        self.controller = controller
        self.sensor_ids = sensor_ids

        # Shared data
        self.sensor_cps = {}
        self.max_readings = 300
        self.l1_sensor = None
        self.s1_sensor = None

        self.data = {
            sensor_id: deque(maxlen=self.max_readings)
            for sensor_id in sensor_ids
        }

        self.gyr_biases = {
            sensor_id: np.zeros(3)
            for sensor_id in sensor_ids
        }

        self.mag_biases = {
            sensor_id: np.zeros(3)
            for sensor_id in sensor_ids
        }

        self.lock = threading.Lock()

        self.ESP_IP = "192.168.4.1"
        self.SERVER_PORT = 80
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Main container
        container = tk.Frame(self)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)

        self.frames = {}

        # Add pages here
        for Page in (MainPage, SettingsPage):
            page_name = Page.__name__

            frame = Page(container, self)

            self.frames[page_name] = frame

            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("MainPage")

        # Start update loop
        self.pull_data()

    def show_frame(self, page_name):
        self.frame = page_name
        self.frames[page_name].tkraise()

    def open_sensor_window(self, sensor_id):
        """Open or focus sensor window"""
        if sensor_id in self.sensor_cps:
            self.close_sensor_cp(sensor_id)
        else:
            self.sensor_cps[sensor_id] = SensorControlPanel(self, sensor_id)

    def close_sensor_cp(self, sensor_id):
        self.sensor_cps[sensor_id].window.destroy()
        del self.sensor_cps[sensor_id]

    def pull_data(self):
        """Called every second to fetch new data and update the overview plot"""
        buffer = self.controller.get_data_buffer()

        for sensor_id in self.sensor_ids:
            # Get the control panel
            cp = self.sensor_cps.get(sensor_id)

            if buffer[sensor_id]:
                if self.data[sensor_id]:
                    if cp:
                        if cp.calibrating_gyr:
                            cp.collect_gyr_cal_samples(buffer[sensor_id])
                        if cp.calibrating_mag:
                            cp.collect_mag_cal_samples(buffer[sensor_id])

                    # Add new readings
                    for datapoint in buffer[sensor_id]:
                        datapoint["gyr"] = datapoint["gyr"] - self.gyr_biases[sensor_id]
                        datapoint["mag"] -= self.mag_biases[sensor_id]

                        delta_time = (datapoint["timestamp"] - self.data[sensor_id][-1]["timestamp"]) / 10000

                        gyr_x, gyr_y, gyr_z = datapoint["gyr"]
                        acc_x, acc_y, acc_z = datapoint["acc"]
                        mag_x, mag_y, mag_z = datapoint["mag"]

                        acc_roll = atan2(acc_y, acc_z)

                        acc_pitch = atan2(
                            -acc_x,
                            sqrt(acc_y ** 2 + acc_z ** 2)
                        )

                        gyr_roll = wrap_pi(self.data[sensor_id][-1]["h_roll"] + gyr_x * delta_time)
                        gyr_pitch = wrap_pi(self.data[sensor_id][-1]["h_pitch"] + gyr_y * delta_time)

                        roll_delta = wrap_pi(acc_roll - gyr_roll)
                        pitch_delta = wrap_pi(acc_pitch - gyr_pitch)

                        tau = 1

                        alpha = 1 - tau / (tau + delta_time)
                        roll = wrap_pi(gyr_roll + alpha * roll_delta)
                        pitch = wrap_pi(gyr_pitch + alpha * pitch_delta)

                        Xh = mag_x * cos(pitch) + mag_z * sin(pitch)
                        Yh = (
                                mag_x * sin(roll) * sin(pitch)
                                - mag_y * cos(roll)
                                + mag_z * sin(roll) * cos(pitch)
                        )

                        mag_yaw = atan2(Yh, Xh)
                        gyr_yaw = wrap_pi(self.data[sensor_id][-1]["h_yaw"] + gyr_z * delta_time)
                        yaw_delta = wrap_pi(mag_yaw - gyr_yaw)
                        yaw = wrap_pi(gyr_yaw + alpha * yaw_delta)

                        datapoint["acc_roll"] = acc_roll
                        datapoint["acc_pitch"] = acc_pitch
                        datapoint["h_roll"] = roll
                        datapoint["h_pitch"] = pitch
                        datapoint["h_yaw"] = yaw
                        datapoint["time_sec"] = datapoint["timestamp"] / 10000

                        with self.lock:
                            self.data[sensor_id].append(datapoint)

                else:
                    # First reading
                    with self.lock:
                        self.data[sensor_id].append({
                            "gyr": np.zeros(3),
                            "acc": np.zeros(3),
                            "acc_roll": 0.,
                            "acc_pitch": 0.,
                            "mag": np.zeros(3),
                            "h_roll": 0.,
                            "h_pitch": 0.,
                            "h_yaw": 0.,
                            "timestamp": buffer[sensor_id][-1]["timestamp"],
                            "time_sec": 0.
                        })
                if cp:
                    self.sensor_cps[sensor_id].status_label.config(
                        text=f"{sensor_id}: Readings {len(self.data[sensor_id])}/{self.max_readings} | Time: {self.data[sensor_id][-1]['time_sec']:.2f}s",
                        fg="green"
                    )

                if self.frame == "SettingsPage":
                    frame = self.frames["SettingsPage"]
                    if self.s1_sensor == sensor_id:
                        frame.s1_reading.config(text=f"Roll: {self.data[sensor_id][-1]['h_roll']:.2f} Radian")
                    if self.l1_sensor == sensor_id:
                        frame.l1_reading.config(text=f"Roll: {self.data[sensor_id][-1]['h_roll']:.2f} Radian")

            else:
                if cp:
                    self.sensor_cps[sensor_id].status_label.config(
                        text=f"No new data...",
                        fg="orange"
                    )

                if self.frame == "SettingsPage":
                    frame = self.frames["SettingsPage"]
                    if self.s1_sensor == sensor_id:
                        frame.s1_reading.config(text=f"No new data...")
                    if self.l1_sensor == sensor_id:
                        frame.l1_reading.config(text=f"No new data...")

        # Schedule the next update
        self.after(50, self.pull_data)
