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

Description: Python wrapper for YouBot arm control
"""

from controller import Robot
import math


class ArmHeight:
    """Classe similar a enum para predefinições de altura do braço."""
    FRONT_FLOOR = 0
    FRONT_PLATE = 1
    FRONT_CARDBOARD_BOX = 2
    RESET = 3
    BACK_PLATE_HIGH = 4
    BACK_PLATE_LOW = 5
    HANOI_PREPARE = 6
    MAX_HEIGHT = 7


class ArmOrientation:
    """Classe similar a enum para predefinições de orientação do braço."""
    BACK_LEFT = 0
    LEFT = 1
    FRONT_LEFT = 2
    FRONT = 3
    FRONT_RIGHT = 4
    RIGHT = 5
    BACK_RIGHT = 6
    MAX_SIDE = 7


class Arm:
    """Controla o braço 5-DOF do YouBot."""

    # Class constants
    FRONT_FLOOR = ArmHeight.FRONT_FLOOR
    FRONT_PLATE = ArmHeight.FRONT_PLATE
    FRONT_CARDBOARD_BOX = ArmHeight.FRONT_CARDBOARD_BOX
    RESET = ArmHeight.RESET
    BACK_PLATE_HIGH = ArmHeight.BACK_PLATE_HIGH
    BACK_PLATE_LOW = ArmHeight.BACK_PLATE_LOW
    HANOI_PREPARE = ArmHeight.HANOI_PREPARE

    BACK_LEFT = ArmOrientation.BACK_LEFT
    LEFT = ArmOrientation.LEFT
    FRONT_LEFT = ArmOrientation.FRONT_LEFT
    FRONT = ArmOrientation.FRONT
    FRONT_RIGHT = ArmOrientation.FRONT_RIGHT
    RIGHT = ArmOrientation.RIGHT
    BACK_RIGHT = ArmOrientation.BACK_RIGHT

    def __init__(self, robot):
        """Inicializa os motores do braço.

        Args:
            robot: instância `Robot` do Webots
        """
        self.robot = robot
        self.time_step = int(robot.getBasicTimeStep())

        # Get arm motors
        self.motors = [
            robot.getDevice("arm1"),
            robot.getDevice("arm2"),
            robot.getDevice("arm3"),
            robot.getDevice("arm4"),
            robot.getDevice("arm5")
        ]

        # Ajusta velocidade do motor 2 (caso especial do código em C)
        self.motors[1].setVelocity(0.5)

        self.current_height = ArmHeight.RESET
        self.current_orientation = ArmOrientation.FRONT

        self.set_height(ArmHeight.RESET)
        self.set_orientation(ArmOrientation.FRONT)

    def reset(self):
        """Reseta o braço para a posição inicial."""
        self.set_height(ArmHeight.RESET)
        self.set_orientation(ArmOrientation.FRONT)

    def set_height(self, height):
        """Define o braço para uma predefinição de altura.

        Args:
            height: predefinição de altura da classe `ArmHeight`
        """
        if height == ArmHeight.FRONT_FLOOR:
            self.motors[1].setPosition(-0.97)
            self.motors[2].setPosition(-1.55)
            self.motors[3].setPosition(-0.61)
            self.motors[4].setPosition(0.0)
        elif height == ArmHeight.FRONT_PLATE:
            self.motors[1].setPosition(-0.62)
            self.motors[2].setPosition(-0.98)
            self.motors[3].setPosition(-1.53)
            self.motors[4].setPosition(0.0)
        elif height == ArmHeight.FRONT_CARDBOARD_BOX:
            self.motors[1].setPosition(0.0)
            self.motors[2].setPosition(-0.77)
            self.motors[3].setPosition(-1.21)
            self.motors[4].setPosition(0.0)
        elif height == ArmHeight.RESET:
            self.motors[1].setPosition(1.57)
            self.motors[2].setPosition(-2.635)
            self.motors[3].setPosition(1.78)
            self.motors[4].setPosition(0.0)
        elif height == ArmHeight.BACK_PLATE_HIGH:
            self.motors[1].setPosition(0.678)
            self.motors[2].setPosition(0.682)
            self.motors[3].setPosition(1.74)
            self.motors[4].setPosition(0.0)
        elif height == ArmHeight.BACK_PLATE_LOW:
            self.motors[1].setPosition(0.92)
            self.motors[2].setPosition(0.42)
            self.motors[3].setPosition(1.78)
            self.motors[4].setPosition(0.0)
        elif height == ArmHeight.HANOI_PREPARE:
            self.motors[1].setPosition(-0.4)
            self.motors[2].setPosition(-1.2)
            self.motors[3].setPosition(-math.pi / 2)
            self.motors[4].setPosition(math.pi / 2)
        else:
            print("Erro: arm_set_height() chamado com argumento inválido")
            return

        self.current_height = height

    def set_orientation(self, orientation):
        """Define a orientação do braço (rotação da base).

        Args:
            orientation: predefinição de orientação da classe `ArmOrientation`
        """
        if orientation == ArmOrientation.BACK_LEFT:
            self.motors[0].setPosition(-2.949)
        elif orientation == ArmOrientation.LEFT:
            self.motors[0].setPosition(-math.pi / 2)
        elif orientation == ArmOrientation.FRONT_LEFT:
            self.motors[0].setPosition(-0.2)
        elif orientation == ArmOrientation.FRONT:
            self.motors[0].setPosition(0.0)
        elif orientation == ArmOrientation.FRONT_RIGHT:
            self.motors[0].setPosition(0.2)
        elif orientation == ArmOrientation.RIGHT:
            self.motors[0].setPosition(math.pi / 2)
        elif orientation == ArmOrientation.BACK_RIGHT:
            self.motors[0].setPosition(2.949)
        else:
            print("Erro: arm_set_orientation() chamado com argumento inválido")
            return

        self.current_orientation = orientation

    def increase_height(self):
        """Aumenta a altura do braço para a próxima predefinição."""
        new_height = self.current_height + 1

        # Prevent from going beyond index
        if new_height >= ArmHeight.MAX_HEIGHT:
            new_height = ArmHeight.MAX_HEIGHT - 1

        # Prevent self-colliding poses
        if new_height == ArmHeight.FRONT_FLOOR:
            if (self.current_orientation == ArmOrientation.BACK_LEFT or
                    self.current_orientation == ArmOrientation.BACK_RIGHT):
                new_height = self.current_height

        self.set_height(new_height)

    def decrease_height(self):
        """Diminui a altura do braço para a predefinição anterior."""
        new_height = self.current_height - 1

        if new_height < 0:
            new_height = 0

        self.set_height(new_height)

    def increase_orientation(self):
        """Gira a base do braço no sentido anti-horário para a próxima predefinição."""
        new_orientation = self.current_orientation + 1

        # Prevent from going beyond index
        if new_orientation >= ArmOrientation.MAX_SIDE:
            new_orientation = ArmOrientation.MAX_SIDE - 1

        # Prevent self-colliding poses
        if new_orientation == ArmOrientation.BACK_LEFT:
            if self.current_height == ArmHeight.FRONT_FLOOR:
                new_orientation = self.current_orientation

        self.set_orientation(new_orientation)

    def decrease_orientation(self):
        """Gira a base do braço no sentido horário para a predefinição anterior."""
        new_orientation = self.current_orientation - 1

        # Prevent from going beyond index
        if new_orientation < 0:
            new_orientation = 0

        # Prevent self-colliding poses
        if new_orientation == ArmOrientation.BACK_RIGHT:
            if self.current_height == ArmHeight.FRONT_FLOOR:
                new_orientation = self.current_orientation

        self.set_orientation(new_orientation)

    def set_sub_arm_rotation(self, arm_index, radian):
        """Define a posição de uma junta individual.

        Args:
            arm_index: índice da junta (0-4)
            radian: posição alvo em radianos
        """
        if 0 <= arm_index < 5:
            self.motors[arm_index].setPosition(radian)

    def get_sub_arm_length(self, arm_index):
        """Retorna o comprimento de um segmento específico do braço.

        Args:
            arm_index: índice da junta (0-4)

        Returns:
            float: comprimento do segmento em metros
        """
        lengths = [0.253, 0.155, 0.135, 0.081, 0.105]
        if 0 <= arm_index < 5:
            return lengths[arm_index]
        return 0.0

    def inverse_kinematics(self, x, y, z):
        """Define a posição do braço usando cinemática inversa.

        Args:
            x: posição alvo em x (metros)
            y: posição alvo em y (metros)
            z: posição alvo em z (metros)
        """
        # Calculate intermediate values
        y1 = math.sqrt(x * x + y * y)
        z1 = z + \
            self.get_sub_arm_length(
                3) + self.get_sub_arm_length(4) - self.get_sub_arm_length(0)

        a = self.get_sub_arm_length(1)
        b = self.get_sub_arm_length(2)
        c = math.sqrt(y1 * y1 + z1 * z1)

        # Calculate joint angles
        alpha = -math.asin(x / y1) if y1 != 0 else 0.0

        # Law of cosines for beta
        cos_beta_part = (a * a + c * c - b * b) / (2.0 * a * c)
        cos_beta_part = max(-1.0, min(1.0, cos_beta_part)
                            )  # Clamp to valid range
        beta = -(math.pi / 2 - math.acos(cos_beta_part) - math.atan2(z1, y1))

        # Law of cosines for gamma
        cos_gamma_part = (a * a + b * b - c * c) / (2.0 * a * b)
        cos_gamma_part = max(-1.0, min(1.0, cos_gamma_part)
                             )  # Clamp to valid range
        gamma = -(math.pi - math.acos(cos_gamma_part))

        delta = -(math.pi + (beta + gamma))
        epsilon = math.pi / 2 + alpha

        # Set motor positions
        self.motors[0].setPosition(alpha)
        self.motors[1].setPosition(beta)
        self.motors[2].setPosition(gamma)
        self.motors[3].setPosition(delta)
        self.motors[4].setPosition(epsilon)
