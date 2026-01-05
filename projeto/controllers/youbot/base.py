"""
Python wrapper for YouBot base control (versão corrigida com ganho de rotação)
"""

from controller import Robot
import math

# Constants
SPEED = 4.0
MAX_SPEED = 0.3
SPEED_INCREMENT = 0.05
DISTANCE_TOLERANCE = 0.001
ANGLE_TOLERANCE = 0.001

# Robot geometry
WHEEL_RADIUS = 0.05
LX = 0.228  # longitudinal distance from robot's COM to wheel [m]
LY = 0.158  # lateral distance from robot's COM to wheel [m]


def bound(value, min_val, max_val):
    return max(min_val, min(max_val, value))


class Base:
    """Controls the YouBot mobile base with omnidirectional wheels"""

    def __init__(self, robot):
        self.robot = robot
        self.time_step = int(robot.getBasicTimeStep())

        self.wheels = [
            robot.getDevice("wheel1"),
            robot.getDevice("wheel2"),
            robot.getDevice("wheel3"),
            robot.getDevice("wheel4")
        ]

        for wheel in self.wheels:
            wheel.setPosition(float('inf'))
            wheel.setVelocity(0.0)

        self.vx = 0.0
        self.vy = 0.0
        self.omega = 0.0

    def _set_wheel_speeds_helper(self, speeds):
        for i in range(4):
            self.wheels[i].setVelocity(speeds[i])

    def move(self, vx, vy, omega):
        """
        vx    : velocidade linear frente (+) / trás (-)
        vy    : velocidade lateral esquerda (+) / direita (-)
        omega : velocidade angular (rad/s)
        """
        OMEGA_GAIN = 3.0  # ganho físico para vencer inércia

        omega_cmd = omega * OMEGA_GAIN

        speeds = [0.0] * 4
        speeds[0] = (1.0 / WHEEL_RADIUS) * (vx - vy -
                                            (LX + LY) * omega_cmd)  # front-left
        speeds[1] = (1.0 / WHEEL_RADIUS) * (vx + vy +
                                            # front-right
                                            (LX + LY) * omega_cmd)
        speeds[2] = (1.0 / WHEEL_RADIUS) * (vx + vy -
                                            (LX + LY) * omega_cmd)  # rear-left
        speeds[3] = (1.0 / WHEEL_RADIUS) * (vx - vy +
                                            (LX + LY) * omega_cmd)  # rear-right

        self._set_wheel_speeds_helper(speeds)

        self.vx = vx
        self.vy = vy
        self.omega = omega

    def reset(self):
        self._set_wheel_speeds_helper([0.0, 0.0, 0.0, 0.0])
        self.vx = 0.0
        self.vy = 0.0
        self.omega = 0.0

    def forwards(self):
        self._set_wheel_speeds_helper([SPEED, SPEED, SPEED, SPEED])

    def backwards(self):
        self._set_wheel_speeds_helper([-SPEED, -SPEED, -SPEED, -SPEED])

    def turn_left(self):
        self._set_wheel_speeds_helper([-SPEED, SPEED, -SPEED, SPEED])

    def turn_right(self):
        self._set_wheel_speeds_helper([SPEED, -SPEED, SPEED, -SPEED])

    def strafe_left(self):
        self._set_wheel_speeds_helper([SPEED, -SPEED, -SPEED, SPEED])

    def strafe_right(self):
        self._set_wheel_speeds_helper([-SPEED, SPEED, SPEED, -SPEED])

    def forwards_increment(self):
        self.vx += SPEED_INCREMENT
        self.vx = min(self.vx, MAX_SPEED)
        self.move(self.vx, self.vy, self.omega)

    def backwards_increment(self):
        self.vx -= SPEED_INCREMENT
        self.vx = max(self.vx, -MAX_SPEED)
        self.move(self.vx, self.vy, self.omega)

    def turn_left_increment(self):
        self.omega += SPEED_INCREMENT
        self.omega = min(self.omega, MAX_SPEED)
        self.move(self.vx, self.vy, self.omega)

    def turn_right_increment(self):
        self.omega -= SPEED_INCREMENT
        self.omega = max(self.omega, -MAX_SPEED)
        self.move(self.vx, self.vy, self.omega)

    def strafe_left_increment(self):
        self.vy += SPEED_INCREMENT
        self.vy = min(self.vy, MAX_SPEED)
        self.move(self.vx, self.vy, self.omega)

    def strafe_right_increment(self):
        self.vy -= SPEED_INCREMENT
        self.vy = max(self.vy, -MAX_SPEED)
        self.move(self.vx, self.vy, self.omega)
