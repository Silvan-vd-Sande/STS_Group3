import os.path
import time
from typing import Literal, cast

from .base_controller import BaseController
from .sensor_mapping import MAC_TO_DOT_MAPPING

import movelladot_pc_sdk
from .xdpchandler import XdpcHandler


class DotController(BaseController):

    def __init__(self, sensor_ids, plot_type: Literal['custom', 'ori', 'acc', 'gyr', 'disabled'] = 'custom', record_data: bool = False):
        super().__init__(sensor_ids, plot_type=plot_type)
        self._record_data = record_data

        self._xdpcHandler = XdpcHandler(self._mac_addresses)
        self.deviceList = []


    def _setup_devices(self):
        # Initializes and configures the Movella DOT devices for measurement.
        if not self._xdpcHandler.initialize():
            self._xdpcHandler.cleanup()
            raise RuntimeError("Could not initialize handler")

        # Scan for sensors
        self._xdpcHandler.scanForDots()
        if not self._xdpcHandler.detectedDots():
            self._xdpcHandler.cleanup()
            raise RuntimeError("No devices found, make sure bluetooth is enabled.")

        # Discover sensors
        self._xdpcHandler.connectDots()
        self.deviceList = self._xdpcHandler.connectedDots()

        for device in self.deviceList:
            device.setOnboardFilterProfile("General")
            device.setOutputRate(60)

        # Update discovered sensor list
        if len(self.deviceList) > 1:
            manager = self._xdpcHandler.manager()
            root_sensor = self.deviceList[-1].bluetoothAddress()
            print("Synchronizing sensors. This may take a while.")
            if not manager.startSync(root_sensor):
                manager.stopSync()
                if not manager.startSync(self.deviceList[-1].bluetoothAddress()):
                    self._xdpcHandler.cleanup()
                    raise RuntimeError("Could not synchronize devices")

        # Set logging, records the sensor data.
        if self._record_data:  # defined in the constructor
            print("checking /data folder")
            if not os.path.exists('./data'):
                print("not found, creating folder")
                os.mkdir('./data')  # Create folder if it doesn't exist
        for device in self.deviceList:
            if self._record_data:
                device.setLogOptions(movelladot_pc_sdk.XsLogOptions_QuaternionAndEuler)
                log_file = f"./data/logfile_{MAC_TO_DOT_MAPPING[device.bluetoothAddress()]}_{self._timestamp}.csv"
                device.enableLogging(log_file)
            device.startMeasurement(movelladot_pc_sdk.XsPayloadMode_HighFidelitywMag)

    def _fetch_data(self):
        """Continuously fetches sensor data and stores it in internal buffers.

        This function runs in a background thread and pushes data to the queue
        for processing.
        """
        while not self._exit_flag:
            if self._xdpcHandler.packetsAvailable():
                for device in self._xdpcHandler.connectedDots():
                    packet = self._xdpcHandler.getNextPacket(device.portInfo().bluetoothAddress())
                    if packet.containsCalibratedAcceleration():
                        sample_time = cast(int, packet.sampleTime64())

                        # For PayLoad Custom Mode 1
                        # ori = packet.orientationEuler()
                        # acc = tuple(packet.rawAcceleration())#
                        # gyr = tuple(packet.calibratedGyroscopeData())

                        # For mode ID1: HighFidelitywMag
                        acc = packet.calibratedAcceleration()
                        mag = packet.calibratedMagneticField()
                        gyr = packet.calibratedGyroscopeData()

                        # For PayLoad Custom Mode 5
                        # ori = packet.orientationQuaternion()
                        # acc = packet.calibratedAcceleration()
                        # gyr = packet.calibratedGyroscopeData()


                        sensor_mac = device.portInfo().bluetoothAddress()
                        sensor_id = MAC_TO_DOT_MAPPING[sensor_mac]
                        self._queue.put((sensor_id, sample_time, mag, acc, gyr))
            time.sleep(0.01)


    def start(self):
        self._setup_devices()
        super().start()


    def stop(self):
        super().stop()
        self._xdpcHandler.cleanup()
