from queue import Queue, Empty
from threading import Thread, RLock
from typing import Literal

from matplotlib.animation import FuncAnimation
import matplotlib.pyplot as plt
import numpy as np

from datetime import datetime

from .sensor_mapping import verify_dot_mapping, DOT_TO_MAC_MAPPING

SensorPayload = tuple[str, int, tuple, tuple, tuple]

class BaseController:

    def __init__(self, sensor_ids: list[str], plot_type: Literal['custom', 'ori', 'acc', 'gyr', 'disabled'] = 'custom'):
        # Verify sensor IDs
        if not verify_dot_mapping(sensor_ids):
            raise InvalidSensorId(f"Invalid sensor IDs have been entered, they should be in the shape of 'DOT-01', from 01 - 20. Entered IDs: {sensor_ids}")

        self.sensor_ids = sensor_ids
        self._plot_type = plot_type

        self._mac_addresses = [DOT_TO_MAC_MAPPING[sid] for sid in sensor_ids]
        self._timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        self._queue: Queue[SensorPayload] = Queue[SensorPayload]()
        self.MAX_QUEUE_SIZE = 300
        self._exit_flag = False
        self._lock = RLock()

        self._sensor_data = {}  # Used for the default plots

    def _fetch_data(self):
        raise NotImplementedError("'_fetch_data' should be overridden in derived class. If you get this error ask a TA because you are inheriting the wrong class")

    def _processing_thread(self):
        """
            Continuously send data from queue to the user defined logic.
            This function runs in a background thread and calls `processing_code()`
            for each new data point.
        """
        while not self._exit_flag:
            try:
                # Remove the last datapoint when the max queue size has been reached
                while self._queue.qsize() > self.MAX_QUEUE_SIZE:
                    self._queue.get_nowait()

                # Pull the last item from the queue
                data = self._queue.get(timeout=0.1)
                queue_size = self._queue.qsize()

                # Ensure that processing, plotting and main threads do not interfere
                with self._lock:
                    # For the defaults plot store the sensor data
                    if self._plot_type not in ('custom', 'disabled'):
                        sensor_id, timestamp, ori, acc, gyr = data
                        if sensor_id not in self._sensor_data:
                            self._sensor_data[sensor_id] = {"time": [], "ori": [], "acc": [], "gyr": []}

                        self._sensor_data[sensor_id]["time"].append(timestamp)
                        self._sensor_data[sensor_id]["ori"].append(ori)  # For PayLoad Mode Custom 1
                        # self.sensor_data[sensor_id]["ori"].append(
                        #     [ori[0], ori[1], ori[2], ori[3]])  # For PayLoad Mode Custom 5
                        self._sensor_data[sensor_id]["acc"].append(acc)
                        self._sensor_data[sensor_id]["gyr"].append(gyr)

                        for key in ["time", "ori", "acc", "gyr"]:
                            if len(self._sensor_data[sensor_id][key]) > 1000:
                                self._sensor_data[sensor_id][key].pop(0)

                    # Send new data to be processed
                    sensor_id, timestamp, ori, acc, gyr = data
                    self.process_data(sensor_id, timestamp, ori, acc, gyr, queue_size)
            except Empty:
                continue

    def _feedback_thread(self):
        """
            Continuously runs the feedback function in a separate thread.
            This thread is optional and can be used to implement a feedback system that runs independently of the data processing and plotting.
            It will continuously call the `feedback()` function, which can be overridden by the students to implement their own feedback logic.
        """
        while not self._exit_flag:
            if not self.feedback():
                break


    def process_data(self, sensor_id: str, timestamp: int, ori: tuple, acc: tuple, gyr: tuple, queue_size: int) -> None:
        """
            To be overridden by the students, currently it prints out the received datapoint and remaining length of the queue.
            It receives the following parameters:
                **sensor_id (str)**: The ID of the sensor that the data belongs to.\n
                **timestamp (int)**: The timestamp of the data point in milliseconds.\n
                **ori (tuple)**: The orientation data. The format depends on the payload mode used. For Custom Mode 1 (default), it is Euler, a 3D vector (roll, pitch, yaw). For Custom Mode 5, it is a quaternion.\n
                **acc (tuple)**: The acceleration data (x, y, z).\n
                **gyr (tuple)**: The gyroscope data (x, y, z).\n
                **queue_size (int)**: The number of data points currently in the queue waiting to be processed. This can be used to monitor the processing speed and adjust the logic accordingly.\n
        """
        print(f"[{timestamp:.2f}s] Sensor {sensor_id} | Queue size: {queue_size}", flush=True)


    def feedback(self) -> bool:
        """
        To be overridden by the students.\n
        Override this method to implement the optional feedback system.

        Note:
            1. This function is continuously called in a separate thread. For performance reasons, add a sleep timer (e.g., `time.sleep(0.1)` to run it at 10Hz).
            2. Use the `thread_safe`decorator for any function that retrieves or uses variables that are also accessed in the `process_data` and plotting methods

        Returns:
            bool: True if the feedback thread should continue running, False to stop the thread.
        """
        return False

    def setup_plot(self) -> None:
        """
           To be overridden by the students, currently it sets up a default plot, if enabled.
       """

        # Only run this method when the default plot is supposed to be used
        if self._plot_type == 'custom':
            raise ValueError("cannot use 'custom' plot type without supplying a custom 'setup_plot' method")

        num_sensors = len(self.sensor_ids)
        self.fig, self.axes = plt.subplots(num_sensors, 1, figsize=(8, 5 * num_sensors))
        if num_sensors == 1:
            self.axes = [ self.axes]

        self.lines = []
        labels = {
            "ori": ("Orientation (degrees)", ["Roll", "Pitch", "Yaw"]),
            "acc": ("Acceleration (m/s²)", ["X", "Y", "Z"]),
            "gyr": ("Angular Velocity (°/s)", ["X", "Y", "Z"]),
        }

        for ax, sensor_id in zip(self.axes, self.sensor_ids):
            ax.set_title(f"{self._plot_type.upper()} - {sensor_id}")
            ax.set_xlabel("Time (s)")
            ax.set_ylabel(labels[self._plot_type][0])

            line_x, = ax.plot([], [], label=labels[self._plot_type][1][0], color='r')
            line_y, = ax.plot([], [], label=labels[self._plot_type][1][1], color='g')
            line_z, = ax.plot([], [], label=labels[self._plot_type][1][2], color='b')

            ax.set_xlim(0, 10)
            ax.set_ylim(-180, 180 if self._plot_type == "ori" else 1)
            ax.legend(loc="upper left")
            self.lines.append([line_x, line_y, line_z])

    def update_plot(self, frame) -> None:
        """
            To be overridden by the students, currently it shows a default plot, if enabled.
        """
        # Only run this method when the default plot is supposed to be used
        if self._plot_type == 'custom':
            raise ValueError("Cannot use 'custom' plot type without supplying a custom 'update_plot' method.")

        # Updates the plot with new data during animation.
        for i, (sensor_id, ax, line_set) in enumerate(zip(self.sensor_ids, self.axes, self.lines)):
            plot_type = self._plot_type

            if sensor_id in self._sensor_data and len(self._sensor_data[sensor_id]["time"]) > 0:
                t = np.array(self._sensor_data[sensor_id]["time"]) / 10000  # Convert to seconds
                values = np.array(self._sensor_data[sensor_id][plot_type])
                min_len = min(len(t), len(values))
                t = t[:min_len]
                values = values[:min_len]

                for j in range(3):
                    line_set[j].set_data(t, values[:, j])

                ax.set_xlim(max(0, t[-1] - 10), t[-1])
                if plot_type in ["acc", "gyr"]:
                    ax.set_ylim(np.min(values) - 1, np.max(values) + 1)

        return sum(self.lines, [])

    def _update_plot_wrapper(self, frame) -> None:
        """
            Ensures that the plot and process functions do not happen at the same time, to prevent race conditions.
            This ensures students don't have to think about threads at all.
        """
        with self._lock:
            return self.update_plot(frame)

    def start(self) -> None:
        """
            Starts the controller by spinning up threads for fetching, processing and plotting data
            It only is a blocking function when plotting is enabled.
        """
        # Create and start the threads for data retrieving and processing
        self.data_thread = Thread(target=self._fetch_data, daemon=True)
        self.processing_thread = Thread(target=self._processing_thread, daemon=True)
        self.feedback_tread = Thread(target=self._feedback_thread, daemon=True)
        self.data_thread.start()
        self.processing_thread.start()
        self.feedback_tread.start()

        # Sets up the plotting and starts a thread for it. plt.show() is a blocking call
        if self._plot_type != 'disabled':
            self.setup_plot()
            if not hasattr(self, 'fig'):
                if self._plot_type == 'custom':
                    raise ValueError("Create a 'self.fig' inside the setup plot in order to show the plotted data. 'self.fig, self.axes = plt.subplots(nr_rows, nr_columns)")
                else:
                    raise ValueError("When using a default plot, do not supply 'setup_plot'.")

            self.ani = FuncAnimation(self.fig, self._update_plot_wrapper, interval=100, cache_frame_data=False)
            plt.show(block=True)


    def stop(self) -> None:
        """
            Sends the stop command to the threads and waits for them to terminate.
        """
        # Stop the threads and wait for them to terminate
        self._exit_flag = True
        self.data_thread.join()
        self.processing_thread.join()


    @staticmethod
    def thread_safe(func):
        """
            A Declarator to be used like `'@BaseController.thread_safe'` above a function.\n
            It ensures that the function can retrieve and use variables that are accessed in the process method.
        """
        def wrapper(self, *args, **kwargs):
            with self._lock:
                return func(self, *args, **kwargs)
        return wrapper


class InvalidSensorId(ValueError):
    """Raised when an invalid SensorID format is found"""
    pass
