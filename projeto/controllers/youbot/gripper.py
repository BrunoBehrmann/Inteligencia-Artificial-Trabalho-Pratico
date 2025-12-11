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

Description: Python wrapper for YouBot gripper control
"""

# Posições do gripper
MIN_POS = 0.0
MAX_POS = 0.025
OFFSET_WHEN_LOCKED = 0.021


def bound(value, min_val, max_val):
    """Limita um valor entre `min_val` e `max_val`."""
    return max(min_val, min(max_val, value))


class Gripper:
    """Controla o gripper paralelo do YouBot."""

    def __init__(self, robot):
        """Inicializa o motor do gripper.

        Args:
            robot: instância `Robot` do Webots
        """
        self.robot = robot
        self.time_step = int(robot.getBasicTimeStep())

        # Obtém o motor do dedo do gripper (um motor controla ambos os dedos)
        self.finger = robot.getDevice("finger::left")

        # Configura velocidade para controle de posição
        if self.finger:
            self.finger.setVelocity(0.03)
        else:
            print("Aviso: Não foi possível encontrar o motor do gripper 'finger::left'")

        # Estado atual
        self.is_gripping = False

    def grip(self):
        """Fecha o gripper para agarrar um objeto."""
        if self.finger:
            self.finger.setPosition(MIN_POS)
        self.is_gripping = True

    def release(self):
        """Abre o gripper para soltar um objeto."""
        if self.finger:
            self.finger.setPosition(MAX_POS)
        self.is_gripping = False

    def set_gap(self, gap):
        """Define a folga específica entre os dedos do gripper.

        Args:
            gap: folga desejada entre os dedos em metros
        """
        # Calcula a posição do motor com compensação de offset
        v = bound(0.5 * (gap - OFFSET_WHEN_LOCKED), MIN_POS, MAX_POS)

        if self.finger:
            self.finger.setPosition(v)

        self.is_gripping = (v < MAX_POS / 2)

    def is_closed(self):
        """Verifica se o gripper está fechado/agarrando.

        Returns:
            bool: True se o gripper estiver agarrando
        """
        return self.is_gripping
