#Adaptive Sensor Noise Model


#This is the part that makes the filter “smart”.

#If the accelerometer magnitude is close to gravity,
#the filter trusts it more.


#If the accelerometer magnitude is far from gravity,
#the filter assumes vibration / movement acceleration and trusts it less.


#For the magnetometer, if the magnetic field norm changes too much,
#the filter assumes magnetic disturbance and trusts yaw correction less.
from AngleKalman1D import *
from math import sin, cos, atan2, sqrt

class SmartKalmanComplementaryAHRS:
    """
    Adaptive Kalman complementary filter for accelerometer + gyroscope + magnetometer.

    Output:
        h_roll
        h_pitch
        h_yaw

    All output angles are in radians.
    """

    def __init__(
        self,
        timestamp_scale=10000.0,
        default_dt=0.01,
        max_dt=0.2,
        acc_base_noise_deg=2.0,
        acc_max_noise_deg=60.0,
        mag_base_noise_deg=5.0,
        mag_max_noise_deg=90.0,
        acc_noise_gain=80.0,
        mag_noise_gain=80.0
    ):
        self.timestamp_scale = timestamp_scale
        self.default_dt = default_dt
        self.max_dt = max_dt

        self.acc_base_R = np.deg2rad(acc_base_noise_deg) ** 2
        self.acc_max_R = np.deg2rad(acc_max_noise_deg) ** 2

        self.mag_base_R = np.deg2rad(mag_base_noise_deg) ** 2
        self.mag_max_R = np.deg2rad(mag_max_noise_deg) ** 2

        self.acc_noise_gain = acc_noise_gain
        self.mag_noise_gain = mag_noise_gain

        self.filters = {}
        self.last_timestamp = {}
        self.mag_reference_norm = {}

    def _get_bias(self, bias_source, sensor_id):
        if bias_source is None:
            return np.zeros(3)

        if isinstance(bias_source, dict):
            return np.asarray(bias_source.get(sensor_id, np.zeros(3)), dtype=float)

        return np.asarray(bias_source, dtype=float)

    def acc_to_roll_pitch(self, acc):
        ax, ay, az = acc

        roll = atan2(ay, az)

        pitch = atan2(-ax, sqrt(ay ** 2 + az ** 2))

        return wrap_pi(roll), wrap_pi(pitch)

    def tilt_compensated_yaw(self, mag, roll, pitch):
        mx, my, mz = mag

        Xh = mx * cos(pitch) + mz * sin(pitch)

        Yh = (
            mx * sin(roll) * sin(pitch)
            - my * cos(roll)
            + mz * sin(roll) * cos(pitch)
        )

        return wrap_pi(atan2(Yh, Xh))

    def adaptive_acc_R(self, acc):
        acc_norm = np.linalg.norm(acc)

        if acc_norm < 1e-9:
            return self.acc_max_R

        # Detect whether accelerometer is probably measured in g or m/s^2.
        expected_g = 9.80665 if acc_norm > 3.0 else 1.0

        gravity_error = abs(acc_norm - expected_g) / expected_g

        R = self.acc_base_R * (1.0 + self.acc_noise_gain * gravity_error ** 2)

        return min(R, self.acc_max_R)

    def adaptive_mag_R(self, mag, sensor_id):
        mag_norm = np.linalg.norm(mag)

        if mag_norm < 1e-9:
            return self.mag_max_R

        ref = self.mag_reference_norm.get(sensor_id, None)

        if ref is None or ref < 1e-9:
            self.mag_reference_norm[sensor_id] = mag_norm
            return self.mag_base_R

        magnetic_error = abs(mag_norm - ref) / ref

        R = self.mag_base_R * (1.0 + self.mag_noise_gain * magnetic_error ** 2)

        return min(R, self.mag_max_R)

    def initialize_sensor(self, sensor_id, datapoint, gyr_biases=None, mag_biases=None):
        gyr_bias = self._get_bias(gyr_biases, sensor_id)
        mag_bias = self._get_bias(mag_biases, sensor_id)

        acc = np.asarray(datapoint["acc"], dtype=float)
        mag = np.asarray(datapoint["mag"], dtype=float) - mag_bias

        roll, pitch = self.acc_to_roll_pitch(acc)
        yaw = self.tilt_compensated_yaw(mag, roll, pitch)

        self.filters[sensor_id] = {
            "roll": AngleKalman1D(initial_angle=roll),
            "pitch": AngleKalman1D(initial_angle=pitch),
            "yaw": AngleKalman1D(initial_angle=yaw)
        }

        self.last_timestamp[sensor_id] = datapoint["timestamp"]
        self.mag_reference_norm[sensor_id] = np.linalg.norm(mag)

        datapoint["h_roll"] = roll
        datapoint["h_pitch"] = pitch
        datapoint["h_yaw"] = yaw

        datapoint["kalman_debug"] = {
            "initialized": True,
            "R_acc": None,
            "R_mag": None,
            "K_roll": None,
            "K_pitch": None,
            "K_yaw": None
        }

        return datapoint

    def update(self, sensor_id, datapoint, gyr_biases=None, mag_biases=None):
        """
        Main update function.

        Expected datapoint:
            datapoint["timestamp"]
            datapoint["acc"] = [ax, ay, az]
            datapoint["gyr"] = [gx, gy, gz] in deg/s
            datapoint["mag"] = [mx, my, mz]

        Returns datapoint with:
            h_roll
            h_pitch
            h_yaw
            kalman_debug
        """

        if sensor_id not in self.filters:
            return self.initialize_sensor(sensor_id, datapoint, gyr_biases, mag_biases)

        gyr_bias = self._get_bias(gyr_biases, sensor_id)
        mag_bias = self._get_bias(mag_biases, sensor_id)

        acc = np.asarray(datapoint["acc"], dtype=float)

        # Your current code converts gyro from deg/s to rad/s after bias removal.
        gyr = np.deg2rad(np.asarray(datapoint["gyr"], dtype=float) - gyr_bias)

        mag = np.asarray(datapoint["mag"], dtype=float) - mag_bias

        current_timestamp = datapoint["timestamp"]
        previous_timestamp = self.last_timestamp[sensor_id]

        dt = (current_timestamp - previous_timestamp) / self.timestamp_scale

        if dt > self.max_dt:
            raise TimeoutError(f"No readings received on time: {dt}")

        self.last_timestamp[sensor_id] = current_timestamp

        acc_roll, acc_pitch = self.acc_to_roll_pitch(acc)

        R_acc = self.adaptive_acc_R(acc)

        roll, K_roll, innov_roll = self.filters[sensor_id]["roll"].step(
            gyro_rate=gyr[0],
            measured_angle=acc_roll,
            dt=dt,
            R=R_acc
        )

        pitch, K_pitch, innov_pitch = self.filters[sensor_id]["pitch"].step(
            gyro_rate=gyr[1],
            measured_angle=acc_pitch,
            dt=dt,
            R=R_acc
        )

        mag_yaw = self.tilt_compensated_yaw(mag, roll, pitch)

        R_mag = self.adaptive_mag_R(mag, sensor_id)

        yaw, K_yaw, innov_yaw = self.filters[sensor_id]["yaw"].step(
            gyro_rate=gyr[2],
            measured_angle=mag_yaw,
            dt=dt,
            R=R_mag
        )

        datapoint["gyr"] = gyr
        datapoint["mag"] = mag

        datapoint["h_roll"] = roll
        datapoint["h_pitch"] = pitch
        datapoint["h_yaw"] = yaw

        datapoint["kalman_debug"] = {
            "initialized": False,
            "dt": dt,
            "R_acc": R_acc,
            "R_mag": R_mag,
            "K_roll": K_roll.tolist(),
            "K_pitch": K_pitch.tolist(),
            "K_yaw": K_yaw.tolist(),
            "innovation_roll": innov_roll,
            "innovation_pitch": innov_pitch,
            "innovation_yaw": innov_yaw,
            "estimated_roll_bias": self.filters[sensor_id]["roll"].bias,
            "estimated_pitch_bias": self.filters[sensor_id]["pitch"].bias,
            "estimated_yaw_bias": self.filters[sensor_id]["yaw"].bias
        }

        return datapoint