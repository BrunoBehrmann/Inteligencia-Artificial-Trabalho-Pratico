"""
Copyright 1996-2024 Cyberbotics Ltd.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Description: Python wrapper for YouBot base control
"""

from controller import Robot
import math

# Constantes
SPEED = 4.0
MAX_SPEED = 0.3
SPEED_INCREMENT = 0.05
DISTANCE_TOLERANCE = 0.001
ANGLE_TOLERANCE = 0.001

# Geometria do robô
WHEEL_RADIUS = 0.05
LX = 0.228  # distância longitudinal do CG do robô até a roda [m]
LY = 0.158  # distância lateral do CG do robô até a roda [m]


def bound(value, min_val, max_val):
    """Limita um valor entre `min_val` e `max_val`."""
    return max(min_val, min(max_val, value))


class Base:
    """Controla a base móvel do YouBot com rodas omnidirecionais."""

    def __init__(self, robot):
        """Inicializa motores da base e sensores.

        Args:
            robot: instância `Robot` do Webots
        """
        self.robot = robot
        self.time_step = int(robot.getBasicTimeStep())

        # Obtém motores das rodas
        self.wheels = [
            robot.getDevice("wheel1"),
            robot.getDevice("wheel2"),
            robot.getDevice("wheel3"),
            robot.getDevice("wheel4")
        ]

        # Configura as rodas para modo de controle de velocidade
        for wheel in self.wheels:
            wheel.setPosition(float('inf'))
            wheel.setVelocity(0.0)

        # Estado de movimento
        self.vx = 0.0
        self.vy = 0.0
        self.omega = 0.0

    def _set_wheel_speeds_helper(self, speeds):
        """Define velocidades das rodas a partir de uma lista de 4 valores.

        Args:
            speeds: lista com 4 velocidades para as rodas
        """
        for i in range(4):
            self.wheels[i].setVelocity(speeds[i])

    def move(self, vx, vy, omega):
        """Calcula e define velocidades das rodas para movimento omnidirecional usando cinemática."""
        speeds = [0.0] * 4
        speeds[0] = (1.0 / WHEEL_RADIUS) * (vx - vy -
                                            # dianteira-esquerda
                                            (LX + LY) * omega)
        speeds[1] = (1.0 / WHEEL_RADIUS) * (vx + vy +
                                            # dianteira-direita
                                            (LX + LY) * omega)
        speeds[2] = (1.0 / WHEEL_RADIUS) * (vx + vy -
                                            # traseira-esquerda
                                            (LX + LY) * omega)
        speeds[3] = (1.0 / WHEEL_RADIUS) * (vx - vy +
                                            # traseira-direita
                                            (LX + LY) * omega)

        self._set_wheel_speeds_helper(speeds)
        self.vx = vx
        self.vy = vy
        self.omega = omega

    def reset(self):
        """Para todo movimento das rodas."""
        speeds = [0.0, 0.0, 0.0, 0.0]
        self._set_wheel_speeds_helper(speeds)
        self.vx = 0.0
        self.vy = 0.0
        self.omega = 0.0

    def forwards(self):
        """Move para frente com a velocidade definida em `SPEED`."""
        speeds = [SPEED, SPEED, SPEED, SPEED]
        self._set_wheel_speeds_helper(speeds)

    def backwards(self):
        """Move para trás com a velocidade definida em `SPEED`."""
        speeds = [-SPEED, -SPEED, -SPEED, -SPEED]
        self._set_wheel_speeds_helper(speeds)

    def turn_left(self):
        """Gira no sentido anti-horário com velocidade `SPEED`."""
        speeds = [-SPEED, SPEED, -SPEED, SPEED]
        self._set_wheel_speeds_helper(speeds)

    def turn_right(self):
        """Gira no sentido horário com velocidade `SPEED`."""
        speeds = [SPEED, -SPEED, SPEED, -SPEED]
        self._set_wheel_speeds_helper(speeds)

    def strafe_left(self):
        """Desloca lateralmente para a esquerda com velocidade `SPEED`."""
        speeds = [SPEED, -SPEED, -SPEED, SPEED]
        self._set_wheel_speeds_helper(speeds)

    def strafe_right(self):
        """Desloca lateralmente para a direita com velocidade `SPEED`."""
        speeds = [-SPEED, SPEED, SPEED, -SPEED]
        self._set_wheel_speeds_helper(speeds)

    def forwards_increment(self):
        """Incrementa a velocidade para frente."""
        self.vx += SPEED_INCREMENT
        self.vx = min(self.vx, MAX_SPEED)
        self.move(self.vx, self.vy, self.omega)

    def backwards_increment(self):
        """Incrementa a velocidade para trás."""
        self.vx -= SPEED_INCREMENT
        self.vx = max(self.vx, -MAX_SPEED)
        self.move(self.vx, self.vy, self.omega)

    def turn_left_increment(self):
        """Incrementa a velocidade de rotação para a esquerda."""
        self.omega += SPEED_INCREMENT
        self.omega = min(self.omega, MAX_SPEED)
        self.move(self.vx, self.vy, self.omega)

    def turn_right_increment(self):
        """Incrementa a velocidade de rotação para a direita."""
        self.omega -= SPEED_INCREMENT
        self.omega = max(self.omega, -MAX_SPEED)
        self.move(self.vx, self.vy, self.omega)

    def strafe_left_increment(self):
        """Incrementa a velocidade de deslocamento lateral para a esquerda."""
        self.vy += SPEED_INCREMENT
        self.vy = min(self.vy, MAX_SPEED)
        self.move(self.vx, self.vy, self.omega)

    def strafe_right_increment(self):
        """Incrementa a velocidade de deslocamento lateral para a direita."""
        self.vy -= SPEED_INCREMENT
        self.vy = max(self.vy, -MAX_SPEED)
        self.move(self.vx, self.vy, self.omega)
