import tkinter as tk
import numpy as np
from tkinter import messagebox
import threading
import queue
import time

import ScatterPlot
from LinePlot import LinePlot
from ScatterPlot import ScatterPlot
from typing import Optional


class SensorControlPanel:
    """Individual sensor window with calibration and settings"""

    def __init__(self, parent, sensor_id):
        self.sensor_id = sensor_id
        self.parent = parent

        # Create popup window
        self.window = tk.Toplevel(parent)
        self.window.title(f"Control Panel: {sensor_id}")
        self.window.geometry("1000x800")

        # Queue for passing processed data from background thread to main thread
        self.draw_queue = queue.Queue(maxsize=1)  # Keep only latest frame

        # Calibration state
        self.calibrating_gyr = False
        self.gyr_samples = []
        self.calibrating_mag = False
        self.mag_lim = {'x_max': 0, 'x_min': 0, 'y_max': 0, 'y_min': 0, 'z_max': 0, 'z_min': 0}
        self.mag_updated_flag = False

        # Plot container
        self.plot_frame = tk.Frame(self.window)
        self.plot_frame.pack(fill=tk.BOTH, expand=True)

        # 3x2 grid
        self.plot_frame.grid_rowconfigure(0, weight=1)
        self.plot_frame.grid_rowconfigure(1, weight=1)
        self.plot_frame.grid_columnconfigure(0, weight=1)
        self.plot_frame.grid_columnconfigure(1, weight=1)
        self.plot_frame.grid_columnconfigure(2, weight=1)

        self.MAX_READINGS = 300

        plt1 = LinePlot(self, 0, 0, f'Gyro raw', [-3.14, 3.14], resizable=.1, ylabel='Radians/s')
        plt1.add_lines(('X', 'gyr_x', '#FF6B6B'),
                        ('Y', 'gyr_y', '#4ECDC4'),
                        ('Z', 'gyr_z', '#0000ff'))

        plt2 = LinePlot(self, 0, 1 ,f'Accelerometer raw', [-3.14, 3.14], resizable=.15, ylabel='Meters/s')
        plt2.add_lines(('X', 'acc_x', '#FF6B6B'),
                        ('Y', 'acc_y', '#4ECDC4'),
                        ('Z', 'acc_z', '#0000ff'))

        plt3 = LinePlot(self, 0, 2, f'Magnetometer raw', [-3.14, 3.14], resizable=.1, ylabel='a.u.')
        plt3.add_lines(('X', 'acc_x', '#FF6B6B'),
                       ('Y', 'acc_y', '#4ECDC4'),
                       ('Z', 'acc_z', '#0000ff'))

        plt4 = LinePlot(self, 1, 0, 'Acc Angle', [-3.14, 3.14], ylabel='Radians')
        plt4.add_lines(('pitch', 'acc_pitch', '#FF6B6B'),
                       ('roll', 'acc_roll', '#4ECDC4'))

        plt5 = LinePlot(self, 1, 1, 'Complementary Filter Angle', [-3.14, 3.14], ylabel='Radians')
        plt5.add_lines(('pitch', 'pitch', '#FF6B6B'),
                       ('roll', 'roll', '#4ECDC4'),
                       ('yaw', 'yaw', '#0000ff'))

        plt6 = ScatterPlot(self, 1, 2, 'XY Magnetometer', [-1.5, 1.5], [-1.5, 1.5])
        plt6.add_scatter(('XY', 'mag_x', 'mag_y', '#0000ff'))

        self.plots = [plt1, plt2, plt3, plt4, plt5, plt6]

        # Resizing
        self.plot_frame.bind("<Configure>", self.on_resize)

        # Gyro Calibration
        self.gyro_control = tk.Frame(self.window, bg="lightgray")
        self.gyro_control.pack(side=tk.BOTTOM, fill=tk.X)

        # Magnetometer Calibration
        self.mag_control = tk.Frame(self.window, bg="lightgray")
        self.mag_control.pack(side=tk.BOTTOM, fill=tk.X)

        # Status label
        self.status_frame = tk.Frame(self.window, bg="lightgray")
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        self.status_label = tk.Label(
            self.status_frame,
            text=f"{sensor_id}: Waiting for data...",
            fg="blue",
            bg="lightgray",
            font=("Arial", 9)
        )
        self.status_label.pack(anchor=tk.W)

        # Gyro calibration button
        self.cal_gyr_button = tk.Button(
            self.gyro_control,
            text="Calibrate Gyr",
            command=self.calibrate_gyro,
            bg="#4CAF50",
            fg="white",
            padx=10,
            pady=5,
            font=("Arial", 9, "bold")
        )
        self.cal_gyr_button.pack(side=tk.LEFT, padx=5, pady=5)

        # Reset gyro calibration button
        self.reset_gyr_cal_button = tk.Button(
            self.gyro_control,
            text="Reset Cal",
            command=self.reset_gyr_calibration,
            bg="#FF9800",
            fg="white",
            padx=10,
            pady=5,
            font=("Arial", 8)
        )
        self.reset_gyr_cal_button.pack(side=tk.LEFT, padx=5, pady=5)

        # Gyro calibration info label
        self.gyr_cal_info_label = tk.Label(
            self.gyro_control,
            text="Bias: X=0.00°/s, Y=0.00°/s, Z=0.00°/s",
            bg="lightgray",
            font=("Arial", 8)
        )
        self.gyr_cal_info_label.pack(side=tk.LEFT, padx=15, pady=5)

        # Gyro calibration status label
        self.gyr_cal_status_label = tk.Label(
            self.gyro_control,
            text="",
            bg="lightgray",
            fg="red",
            font=("Arial", 8)
        )
        self.gyr_cal_status_label.pack(side=tk.LEFT, padx=5, pady=5)

        # Magnetometer calibration button
        self.cal_mag_button = tk.Button(
            self.mag_control,
            text="Calibrate Mag",
            command=self.calibrate_mag,
            bg="#4CAF50",
            fg="white",
            padx=10,
            pady=5,
            font=("Arial", 9, "bold")
        )
        self.cal_mag_button.pack(side=tk.LEFT, padx=5, pady=5)

        # Reset magnetometer calibration button
        self.reset_mag_cal_button = tk.Button(
            self.mag_control,
            text="Reset Cal",
            command=self.reset_mag_calibration,
            bg="#FF9800",
            fg="white",
            padx=10,
            pady=5,
            font=("Arial", 8)
        )
        self.reset_mag_cal_button.pack(side=tk.LEFT, padx=5, pady=5)

        # Magnetometer calibration info label
        self.mag_cal_info_label = tk.Label(
            self.mag_control,
            text="Bias: X=0.00°/s, Y=0.00°/s, Z=0.00°/s",
            bg="lightgray",
            font=("Arial", 8)
        )
        self.mag_cal_info_label.pack(side=tk.LEFT, padx=15, pady=5)

        # Magnetometer calibration status label
        self.mag_cal_status_label = tk.Label(
            self.mag_control,
            text="",
            bg="lightgray",
            fg="red",
            font=("Arial", 8)
        )
        self.mag_cal_status_label.pack(side=tk.LEFT, padx=5, pady=5)

        # Set up close handler
        self.window.protocol("WM_DELETE_WINDOW", lambda: self.parent.close_sensor_cp(sensor_id))

        # Start background thread for data processing
        self.background_thread = threading.Thread(
            target=self.background_update_loop,
            daemon=True
        )
        self.background_thread.start()

        # Start main thread polling loop to check queue and draw
        self.poll_draw_queue()

    def background_update_loop(self) -> None:
        """All processing happens here."""
        while self.window.winfo_exists():
            try:
                # Get data from parent
                data = self.parent.data[self.sensor_id]

                if data:
                    # Extract and process data (EXPENSIVE - in background)
                    plot_data = self.process_plot_data(data)

                    # Queue the result for main thread to draw
                    # Use maxsize=1 so we skip old frames if main thread is slow
                    try:
                        self.draw_queue.put_nowait(plot_data)
                    except queue.Full:
                        # Main thread is busy, skip this frame
                        pass

                    time.sleep(0.1) # ~10fps updating

            except Exception as e:
                print(f"Error in background thread for {self.sensor_id}: {e}")
                time.sleep(1)

    def poll_draw_queue(self) -> None:
        """Poll the queue and draw any pending frames."""
        try:
            # Non-blocking check for queued data
            plot_data = self.draw_queue.get_nowait()
            # Draw immediately (no lock needed, main thread only)
            self._draw_plot(plot_data)
        except queue.Empty:
            # No data ready, that's fine
            pass
        except Exception as e:
            print(f"Error drawing {self.sensor_id}: {e}")

        # Schedule next poll
        self.window.after(100, self.poll_draw_queue)  # >10fps polling. System events bottleneck

    def _draw_plot(self, plot_data: dict) -> None:
        if len(plot_data['time']) < 2:
            return

        for plot in self.plots:
            plot.draw_plot(plot_data)

    def process_plot_data(self, data: list[dict]) -> Optional[dict[str, float]]:
        """Extract and process data for plotting.
        This is the expensive numpy/list comprehension work."""

        if not data:
            return None

        with self.parent.lock:
            gyr_x, gyr_y, gyr_z = np.array(
                [[d for d in datapoint["gyr"]]
                 for datapoint in data]
            ).T

            acc_x, acc_y, acc_z = np.array(
                [[d for d in datapoint["acc"]]
                 for datapoint in data]
            ).T

            mag_x, mag_y, mag_z = np.array(
                [[d for d in datapoint["mag"]]
                 for datapoint in data]
            ).T

            acc_roll = np.array([d["acc_roll"] for d in data])
            acc_pitch = np.array([d["acc_pitch"] for d in data])

            roll = np.array([d["h_roll"] for d in data])
            pitch = np.array([d["h_pitch"] for d in data])
            yaw = np.array([d["h_yaw"] for d in data])

            t0 = data[-1]["time_sec"]
            time_list = np.fromiter(
                (datapoint['time_sec'] - t0 for datapoint in data),
                dtype=np.float32
            )

        data_formatted = {'time': time_list, 'gyr_x': gyr_x, 'gyr_y': gyr_y, 'gyr_z': gyr_z,
                'acc_x': acc_x, 'acc_y': acc_y, 'acc_z': acc_z,
                'mag_x': mag_x, 'mag_y': mag_y, 'mag_z': mag_z,
                'acc_roll': acc_roll, 'acc_pitch': acc_pitch,
                'roll': roll, 'pitch': pitch, 'yaw': yaw
                }

        if len(time_list) != self.MAX_READINGS:
            for key in data_formatted:
                val = data_formatted[key]
                data_formatted[key] = np.pad(val, (0, max(0, self.MAX_READINGS - len(val))), constant_values=np.nan)[-self.MAX_READINGS:]

        for plot in self.plots:
            if plot.resizable:
                plot.resize_automatic(data_formatted)

        return data_formatted

    def collect_gyr_cal_samples(self, data: list[dict[str, tuple]]) -> None:
        """Collect raw gyro samples during calibration"""
        with self.parent.lock:
            for datapoint in data:
                self.gyr_samples.append(datapoint["gyr"])

    def collect_mag_cal_samples(self, data: list[dict[str, tuple]]) -> None:
        """Collect raw magnetometer samples during calibration"""
        self.mag_updated_flag = True
        with self.parent.lock:
            for datapoint in data:
                vals = datapoint["mag"]
                for i, axis in enumerate(('x', 'y', 'z')):
                    self.mag_lim[axis + '_max'] = max(self.mag_lim[axis + '_max'], vals[i])
                    self.mag_lim[axis + '_min'] = min(self.mag_lim[axis + '_min'], vals[i])

    def calibrate_gyro(self) -> None:
        """Start gyro calibration - non-blocking"""
        if self.calibrating_gyr:
            messagebox.showwarning(
                "Calibration",
                "Calibration of gyro already in progress!",
                parent=self.window
            )
            return

        self.calibrating_gyr = True
        self.cal_gyr_button.config(state=tk.DISABLED, bg="#CCCCCC")

        messagebox.showinfo(
            "Calibration",
            f"Keep {self.sensor_id} completely still for 5 seconds.\n"
            f"Dialog will close automatically.",
            parent=self.window
        )

        # Schedule finish in 5 seconds
        self.window.after(5000, self.finish_gyr_calibration)

    def finish_gyr_calibration(self) -> None:
        """Finish calibration and calculate average bias"""
        self.calibrating_gyr = False
        self.cal_gyr_button.config(state=tk.NORMAL, bg="#4CAF50")

        if not self.gyr_samples:
            messagebox.showerror(
                "Calibration Error",
                "No samples collected!",
                parent=self.window
            )
            return

        # Calculate average bias
        gyr_bias = np.mean(self.gyr_samples, axis=0)

        self.parent.gyr_biases[self.sensor_id] = gyr_bias

        self.gyr_samples = []

        self.gyr_cal_status_label.config(text="✓ Calibrated")

        self.update_gyr_cal_display(gyr_bias)

        messagebox.showinfo(
            "Calibration Complete",
            f"Gyro bias calculated for {self.sensor_id}:\n"
            f"X: {gyr_bias[0]:.4f}°/s\n"
            f"Y: {gyr_bias[1]:.4f}°/s\n"
            f"Z: {gyr_bias[2]:.4f}°/s\n\n"
            f"This offset will now be subtracted from all readings.",
            parent=self.window
        )

    def reset_gyr_calibration(self) -> None:
        """Reset calibration to zero"""
        zeros = np.zeros(3, dtype=np.float64)
        self.parent.gyr_biases[self.sensor_id] = zeros
        self.update_gyr_cal_display(zeros)
        self.gyr_cal_status_label.config(text="")
        messagebox.showinfo(
            "Reset",
            f"Bias calibration for {self.sensor_id} reset to zero.",
            parent=self.window
        )

    def update_gyr_cal_display(self, bias: np.ndarray) -> None:
        """Update the calibration info label"""
        self.gyr_cal_info_label.config(
            text=f"Bias: X={bias[0]:.4f}°/s, "
                 f"Y={bias[1]:.4f}°/s, "
                 f"Z={bias[2]:.4f}°/s"
        )

    def calibrate_mag(self) -> None:
        """Start gyro calibration - non-blocking"""
        if self.calibrating_mag:
            messagebox.showwarning(
                "Calibration",
                "Calibration of magnetometer already in progress!",
                parent=self.window
            )
            return

        self.calibrating_mag = True
        self.cal_mag_button.config(text="Stop Calibrating", command=self.finish_mag_calibration, bg="#CCCCCC")


    def finish_mag_calibration(self) -> None:
        """Finish calibration and calculate average bias"""
        self.calibrating_mag = False
        if not self.mag_updated_flag:
            messagebox.showerror(
                "Calibration Error",
                "No samples collected!",
                parent=self.window
            )
            return

        x_offset = (self.mag_lim['x_min'] + self.mag_lim['x_max']) / 2.
        y_offset = (self.mag_lim['y_min'] + self.mag_lim['y_max']) / 2.
        z_offset = (self.mag_lim['z_min'] + self.mag_lim['z_max']) / 2.

        offset = np.array([x_offset, y_offset, z_offset])
        self.parent.mag_biases[self.sensor_id] = offset

        self.cal_mag_button.config(text="Start Calibrating", command=self.calibrate_mag, bg="#4CAF50")
        self.update_mag_cal_display(offset)
        self.mag_cal_status_label.config(text="✓ Calibrated")

        messagebox.showinfo(
            "Calibration Complete",
            f"Mag bias calculated for {self.sensor_id}:\n"
            f"X: {x_offset:.4f}, min: {self.mag_lim['x_min']:.4f}, max: {self.mag_lim['x_max']:.4f}\n"
            f"Y: {y_offset:.4f}, min: {self.mag_lim['y_min']:.4f}, max: {self.mag_lim['y_max']:.4f}\n"
            f"Z: {z_offset:.4f}, min: {self.mag_lim['z_min']:.4f}, max: {self.mag_lim['z_max']:.4f}\n"
            f"This offset will now be subtracted from all readings.",
            parent=self.window
        )

    def reset_mag_calibration(self) -> None:
        """Reset calibration to zero"""
        zeros = np.zeros(3, dtype=np.float64)
        self.parent.mag_biases[self.sensor_id] = zeros
        self.update_mag_cal_display(zeros)
        self.mag_cal_status_label.config(text="")
        messagebox.showinfo(
            "Reset",
            f"Mag bias calibration for {self.sensor_id} reset to zero.",
            parent=self.window
        )

    def update_mag_cal_display(self, bias: np.ndarray) -> None:
        """Update the calibration info label"""
        self.mag_cal_info_label.config(
            text=f"Bias: X={bias[0]:.4f}a.u., "
                 f"Y={bias[1]:.4f}a.u., "
                 f"Z={bias[2]:.4f}a.u."
        )

    def on_resize(self, event: tk.Event) -> None:
        """Resize plot backgrounds for blitting"""
        for plot in self.plots:
            plot.background_needs_cache = True