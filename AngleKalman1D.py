import numpy as np
from math import atan2, sqrt, sin, cos, pi


def wrap_pi(angle):
    """
    Wrap angle to [-pi, pi].
    """
    return (angle + pi) % (2.0 * pi) - pi


class AngleKalman1D:
    """
    1D Kalman filter for one attitude angle.

    State:
        x[0] = angle
        x[1] = gyro bias

    Prediction:
        angle_k = angle_(k-1) + dt * (gyro_rate - bias)

    Measurement:
        measured_angle from accelerometer or magnetometer
    """

    def __init__(
            self,
            initial_angle=0.0,
            initial_bias=0.0,
            q_angle=1e-5,
            q_bias=1e-6,
            p_angle=0.05,
            p_bias=0.01
    ):
        self.angle = wrap_pi(initial_angle)
        self.bias = initial_bias

        self.P = np.array([
            [p_angle, 0.0],
            [0.0, p_bias]
        ], dtype=float)

        self.q_angle = q_angle
        self.q_bias = q_bias

        self.last_gain = np.array([0.0, 0.0])
        self.last_innovation = 0.0

    def predict(self, gyro_rate, dt):
        """
        gyro_rate must be in rad/s.
        dt must be in seconds.
        """
        if dt <= 0:
            raise ValueError(f"dt must be positive, got {dt}")

        corrected_rate = gyro_rate - self.bias
        self.angle = wrap_pi(self.angle + dt * corrected_rate)

        F = np.array([
            [1.0, -dt],
            [0.0, 1.0]
        ])

        Q = np.array([
            [self.q_angle * dt * dt, 0.0],
            [0.0, self.q_bias * dt]
        ])

        self.P = F @ self.P @ F.T + Q
        return self.angle

    def update(self, measured_angle, R):
        """
        measured_angle must be in radians.
        R is measurement noise variance.
        Larger R = trust measurement less.
        Smaller R = trust measurement more.
        """
        measured_angle = wrap_pi(measured_angle)

        innovation = wrap_pi(measured_angle - self.angle)

        # H = [1, 0]
        S = self.P[0, 0] + R

        if S <= 1e-12:
            return self.angle, np.array([0.0, 0.0]), innovation

        K0 = self.P[0, 0] / S
        K1 = self.P[1, 0] / S

        self.angle = wrap_pi(self.angle + K0 * innovation)
        self.bias = self.bias + K1 * innovation

        # Joseph-stabilized covariance update
        K = np.array([[K0], [K1]])
        H = np.array([[1.0, 0.0]])
        I = np.eye(2)

        self.P = (I - K @ H) @ self.P @ (I - K @ H).T + R * (K @ K.T)

        self.last_gain = np.array([K0, K1])
        self.last_innovation = innovation

        return self.angle, self.last_gain, innovation

    def step(self, gyro_rate, measured_angle, dt, R):
        self.predict(gyro_rate, dt)
        return self.update(measured_angle, R)