"""
Controlador YouBot - Versão Estável com Fuzzy separado para ALIGN
"""

from controller import Robot
import math

from base import Base
from arm import Arm, ArmHeight, ArmOrientation
from gripper import Gripper
from perception import Perception
from fuzzy_control import FuzzyControl
from fuzzy_align import FuzzyAlign

# Estados
ST_SEARCH = "SEARCH"
ST_ALIGN = "ALIGN"
ST_APPROACH = "APPROACH"
ST_COLLECT = "COLLECT"
ST_DEPOSIT = "DEPOSIT"


class YouBotController:
    def __init__(self):
        self.robot = Robot()
        self.time_step = int(self.robot.getBasicTimeStep())

        # Atuadores
        self.base = Base(self.robot)
        self.arm = Arm(self.robot)
        self.gripper = Gripper(self.robot)

        # Sensores
        self.camera = self.robot.getDevice("camera")
        self.camera.enable(self.time_step)
        self.camera_width = self.camera.getWidth()

        self.lidar = self.robot.getDevice("lidar")
        if self.lidar:
            self.lidar.enable(self.time_step)

        # IA
        self.perception = Perception(self.camera, self.lidar, "best.pt")
        self.fuzzy = FuzzyControl()
        self.fuzzy_align = FuzzyAlign(self.camera_width)

        # Estado
        self.state = ST_SEARCH

        self.targets_cubes = ["cubo_azul", "cubo_vermelho", "cubo_verde"]
        self.targets_boxes = ["caixa_azul", "caixa_vermelha", "caixa_verde"]

        self.current_target_list = self.targets_cubes
        self.detected_target_label = None

        self.patience_max = 50
        self.patience = 0

        self.arm.reset()
        self.gripper.release()

    def wait(self, seconds):
        start = self.robot.getTime()
        while self.robot.step(self.time_step) != -1:
            if self.robot.getTime() - start > seconds:
                break

    # -------- STATES ----------

    def run_search(self, detections):
        self.base.move(0, 0, 0.15)

        if detections:
            for d in detections:
                if d["label"] in self.current_target_list:
                    print(f"[SEARCH] Alvo: {d['label']}")
                    self.detected_target_label = d["label"]
                    self.base.reset()
                    self.state = ST_ALIGN
                    return

    def run_align(self, detections):
        target_bbox = None
        if detections:
            for d in detections:
                if d["label"] == self.detected_target_label:
                    target_bbox = d["bbox"]
                    break

        if target_bbox is None:
            self.base.move(0, 0, 0.1)
            return

        bbox_center_x = (target_bbox[0] + target_bbox[2]) / 2
        screen_center = self.camera_width / 2
        error = screen_center - bbox_center_x

        omega = self.fuzzy_align.compute(error)

        print(f"[ALIGN] erro_px={error:.1f} omega={omega:.2f}")

        if omega == 0.0:
            self.base.reset()
            self.state = ST_APPROACH
            print("[ALIGN] Alinhado!")
        else:
            self.base.move(0.0, 0.0, omega)

    def run_approach(self, detections, dist_lidar):
        target_bbox = None
        if detections:
            for d in detections:
                if d["label"] == self.detected_target_label:
                    target_bbox = d["bbox"]
                    break

        if target_bbox is None:
            self.base.reset()
            return

        bbox_center_x = (target_bbox[0] + target_bbox[2]) / 2
        screen_center = self.camera_width / 2
        error = screen_center - bbox_center_x

        vx, omega = self.fuzzy.compute(error, dist_lidar, self.camera_width)

        if vx == 0 and abs(omega) < 0.1:
            self.base.reset()
            print("[APPROACH] Chegou ao alvo.")

            if "cubo" in self.detected_target_label:
                self.state = ST_COLLECT
            else:
                self.state = ST_DEPOSIT
        else:
            self.base.move(vx, 0.0, omega)

    def run_collect(self):
        print("[COLLECT] Pegando...")
        self.gripper.release()
        self.wait(0.5)

        self.arm.set_height(ArmHeight.FRONT_FLOOR)
        self.arm.set_orientation(ArmOrientation.FRONT)
        self.wait(2)

        self.gripper.grip()
        self.wait(1)

        self.arm.reset()
        self.wait(2)

        cor = self.detected_target_label.split("_")[1]
        self.current_target_list = [f"caixa_{cor}"]
        self.state = ST_SEARCH

    def run_deposit(self):
        print("[DEPOSIT] Depositando...")
        self.arm.set_height(ArmHeight.FRONT_PLATE)
        self.wait(2)

        self.gripper.release()
        self.wait(1)

        self.arm.reset()
        self.wait(2)

        self.base.move(-0.2, 0, 0)
        self.wait(1)

        self.base.reset()

        self.current_target_list = self.targets_cubes
        self.state = ST_SEARCH

    # -------- MAIN LOOP --------

    def run(self):
        print("=== YOU BOT CONTROLADOR INICIADO ===")

        while self.robot.step(self.time_step) != -1:
            dist_lidar = self.perception.get_lidar_dist()
            _, detections = self.perception.get_detections()

            if self.state == ST_SEARCH:
                self.run_search(detections)

            elif self.state == ST_ALIGN:
                self.run_align(detections)

            elif self.state == ST_APPROACH:
                self.run_approach(detections, dist_lidar)

            elif self.state == ST_COLLECT:
                self.run_collect()

            elif self.state == ST_DEPOSIT:
                self.run_deposit()


if __name__ == "__main__":
    controller = YouBotController()
    controller.run()
