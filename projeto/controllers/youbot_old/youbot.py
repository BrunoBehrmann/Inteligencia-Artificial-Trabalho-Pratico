from controller import Robot
from base import Base
from arm import Arm
from gripper import Gripper
from lidar_processing import compute_vfh_direction
import sys
import os

# Garante imports locais
sys.path.append(os.path.dirname(__file__))


class YouBotController:
    def __init__(self):
        self.robot = Robot()
        self.time_step = int(self.robot.getBasicTimeStep())

        self.base = Base(self.robot)
        self.arm = Arm(self.robot)
        self.gripper = Gripper(self.robot)

        self.camera = self.robot.getDevice("camera")
        self.camera.enable(self.time_step)

        self.lidar = self.robot.getDevice("lidar")
        self.lidar.enable(self.time_step)

    def run(self):
        raise NotImplementedError


class LidarNavigationController(YouBotController):
    """Navegação local usando VFH frontal (sem recuo)."""

    def __init__(self):
        super().__init__()
        print("Controlador VFH ativo (LiDAR frontal, sem recuo).")

    def run(self):
        while self.robot.step(self.time_step) != -1:
            range_image = self.lidar.getRangeImage()

            angle = compute_vfh_direction(range_image)

            if angle is None:
                print("Sem vale livre. Girando no lugar...")
                self.base.turn_left()

            elif abs(angle) < 10:
                print("Caminho à frente. Avançando.")
                self.base.forwards()

            elif angle > 0:
                print(f"Giro à esquerda ({angle:.1f}°)")
                self.base.turn_left()

            else:
                print(f"Giro à direita ({angle:.1f}°)")
                self.base.turn_right()


if __name__ == "__main__":
    controller = LidarNavigationController()
    controller.run()
# Responsável por: Receber imagem da câmera, Pré-processar e enviar para YOLO.
# Também retorna: detected, class, theta (erro angular do objeto detectado em relação a posição da câmera)
