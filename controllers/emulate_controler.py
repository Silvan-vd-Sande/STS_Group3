import time
from copy import deepcopy
from typing import Literal, List

from .base_controller import BaseController


class EmuController(BaseController):

    def __init__(self, recording_files: List[str], plot_type: Literal['custom', 'ori', 'acc', 'gyr', 'disabled'] = 'custom', record_data: bool = False):
        self._recorded_data = {}

        # Processes all files
        for file in recording_files:
            with open(file) as f:
                file_lines = f.readlines()

            # Retrieves the sensorID
            info_line = file_lines[0]
            dot_num = info_line.split(',')[0][20:]
            sensor_id = 'DOT-' + ('0' if len(dot_num) < 2 else '') + dot_num

            # Finds the last non-empty measurement
            last_full_line = len(file_lines) - 1
            while len(file_lines[last_full_line].split(',')) < 14:
                last_full_line -= 1

            # Cuts, formats, and stores the data
            data_lines = file_lines[2:last_full_line]
            data = [[float(val) for val in line.split(',')] for line in data_lines]
            self._recorded_data[sensor_id] = data

        super().__init__(list(self._recorded_data.keys()), plot_type=plot_type)



    def _fetch_data(self):
        """Continuously fetches sensor data and stores it in internal buffers.

        This function runs in a background thread and pushes data to the queue
        for processing.
        """

        start_timestamp = max([data[0][0] for data in self._recorded_data.values()])
        end_timestamp = min([data[-1][0] for data in self._recorded_data.values()])

        start_time = time.time()

        loop_count = 0

        working_data = deepcopy(self._recorded_data)
        while not self._exit_flag:
            cur_time = time.time()

            cur_timestamp = (cur_time - start_time) * 10000 + start_timestamp

            last_timestamp = 0

            # Retrieves the 'passed' datapoints from the data list
            for sensor_id, data in working_data.items():
                while cur_timestamp > data[0][0]:
                    val = data.pop(0)
                    self._queue.put((sensor_id, val[0], val[8:11], val[11:14], val[1:4]))
                    last_timestamp = max(last_timestamp, val[0])

                    # Break out of the while loop when there are no more data points left
                    # This will also reset the recording loop as it restarts when the first sensor stops
                    if len(data) == 0: break

            # Restarts the recording loop
            if last_timestamp >= end_timestamp:
                start_time = time.time()
                working_data = deepcopy(self._recorded_data)
                loop_count += 1

            time.sleep(0.01)


    def start(self):
        super().start()


    def stop(self):
        super().stop()
