

from controller import Robot
import math


SPEED = 4.0
MAX_SPEED = 0.3
SPEED_INCREMENT = 0.05
DISTANCE_TOLERANCE = 0.001
ANGLE_TOLERANCE = 0.001


WHEEL_RADIUS = 0.05
LX = 0.228
LY = 0.158


def bound(value, min_val, max_val):

    return max(min_val, min(max_val, value))


class Base:

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

        speeds = [0.0] * 4
        speeds[0] = (1.0 / WHEEL_RADIUS) * (vx - vy - (LX + LY) * omega)
        speeds[1] = (1.0 / WHEEL_RADIUS) * (vx + vy + (LX + LY) * omega)
        speeds[2] = (1.0 / WHEEL_RADIUS) * (vx + vy - (LX + LY) * omega)
        speeds[3] = (1.0 / WHEEL_RADIUS) * (vx - vy + (LX + LY) * omega)

        self._set_wheel_speeds_helper(speeds)
        self.vx = vx
        self.vy = vy
        self.omega = omega

    def reset(self):

        speeds = [0.0, 0.0, 0.0, 0.0]
        self._set_wheel_speeds_helper(speeds)
        self.vx = 0.0
        self.vy = 0.0
        self.omega = 0.0

    def forwards(self):

        speeds = [SPEED, SPEED, SPEED, SPEED]
        self._set_wheel_speeds_helper(speeds)

    def backwards(self):

        speeds = [-SPEED, -SPEED, -SPEED, -SPEED]
        self._set_wheel_speeds_helper(speeds)

    def turn_left(self):

        speeds = [-SPEED, SPEED, -SPEED, SPEED]
        self._set_wheel_speeds_helper(speeds)

    def turn_right(self):

        speeds = [SPEED, -SPEED, SPEED, -SPEED]
        self._set_wheel_speeds_helper(speeds)

    def strafe_left(self):

        speeds = [SPEED, -SPEED, -SPEED, SPEED]
        self._set_wheel_speeds_helper(speeds)

    def strafe_right(self):

        speeds = [-SPEED, SPEED, SPEED, -SPEED]
        self._set_wheel_speeds_helper(speeds)

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
