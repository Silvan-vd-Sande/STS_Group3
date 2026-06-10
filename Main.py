from __future__ import annotations  # makes all hints strings at runtime
from controllers import BaseController, DotController, EmuController
import tkinter as tk
import copy
from App import GyroPlotterApp

class Controller(DotController):
    def __init__(self, sensor_ids):
        super().__init__(sensor_ids, plot_type='disabled', record_data=False)
        self.data_buffer = {sensor_id: [] for sensor_id in self.sensor_ids}

    def setup_plot(self):
        BaseController.setup_plot(self)

    def process_data(self, sensor_id: str, timestamp: int, mag: tuple, acc: tuple, gyr: tuple, queue_size: int) -> None:
        self.data_buffer[sensor_id].append({"gyr": gyr, "acc": acc, "mag": mag, "timestamp": timestamp})

    def feedback(self):
        pass

    def update_plot(self, frame):
        BaseController.update_plot(self, frame)

    @BaseController.thread_safe
    def get_data_buffer(self):
        # Create a completely independent copy while holding the lock
        copied_data_buffer = copy.deepcopy(self.data_buffer)
        _ = str(copied_data_buffer)

        # Replace with a new empty list
        self.data_buffer = {sensor_id: [] for sensor_id in self.sensor_ids}

        return copied_data_buffer


def setup(sensor_ids: list) -> tuple[tk.Tk, Controller]:
    #contr = Controller(["./data/logfile_DOT-13_2026-05-07_16-06.csv"])  # Live connection to the sensors
    contr = Controller(sensor_ids)

    # Pass your actual controller here
    app = GyroPlotterApp(contr, sensor_ids)

    return app, contr

def start_mainloop(app: tk.Tk, contr: Controller) -> None:
    contr.start()
    app.mainloop()

def end_mainloop(contr: Controller) -> None:
    contr.stop()


# Usage
if __name__ == "__main__":
    app_main, controller = setup(["DOT-13", "DOT-14"])
    start_mainloop(app_main, controller)
    end_mainloop(controller)
