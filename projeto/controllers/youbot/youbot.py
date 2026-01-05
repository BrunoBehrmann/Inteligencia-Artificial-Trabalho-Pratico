from controller import Robot
from base import Base
from arm import Arm
from gripper import Gripper
from perception import Perception
import math


class YouBotController:
    def __init__(self):
        self.robot = Robot()
        self.time_step = int(self.robot.getBasicTimeStep())

        self.base = Base(self.robot)
        self.arm = Arm(self.robot)
        self.gripper = Gripper(self.robot)

        self.camera = self.robot.getDevice("camera")
        self.camera.enable(self.time_step)
        self.cam_width = self.camera.getWidth()

        self.perception = Perception(self.camera, "best.pt")
        self.perception.interval = 0.05

        self.lidar_front = self.robot.getDevice("lidar")
        self.lidar_front.enable(self.time_step)
        self.lidar_width = self.lidar_front.getHorizontalResolution()

        # FSM
        self.state = "SEARCH_CUBE"
        self.last_state = None

        self.target_cube_label = None
        self.target_box_label = None
        self.cube_color = None

        self.collected_cubes = 0
        self.max_cubes = 15

        self.turn_speed = 0.6
        self.distancia_parar = 0.12

    # ================== UTIL ==================

    def on_state_enter(self, state_name):
        if self.last_state != state_name:
            print(f"\n=== ESTADO: {state_name} ===")
            self.last_state = state_name

    def print_distance(self, label, dist):
        if dist < 99:
            print(f"[LIDAR] Distância até {label}: {dist:.3f} m")

    def find_objects(self, detections, labels):
        objs = [d for d in detections if d["label"] in labels]
        return max(objs, key=lambda o: o["bbox"][3]) if objs else None

    def box_from_cube(self, cube_label):
        if "azul" in cube_label:
            return "caixa azul"
        if "vermelho" in cube_label:
            return "caixa vermelha"
        if "verde" in cube_label:
            return "caixa verde"
        return None

    # ================== FUZZY ==================

    def fuzzy_velocidade(self, d):
        if d < 0.12:
            return 0.0
        elif d < 0.25:
            return 0.08
        elif d < 0.5:
            return 0.2
        else:
            return 0.35

    def fuzzy_rotacao(self, erro_px):
        if abs(erro_px) < 15:
            return 0.0
        return -0.003 * erro_px

    # ================== LIDAR ==================

    def get_lidar_center_dist(self):
        ranges = self.lidar_front.getRangeImage()
        if not ranges:
            return 99.0
        mid = int(self.lidar_width / 2)
        vals = [x for x in ranges[mid - 10:mid + 10] if 0.05 < x < 2.0]
        return min(vals) if vals else 99.0

    # ================== LOOP ==================

    def run(self):
        print("=== YOUBOT FSM CONTROLLER ===")

        self.arm.reset()
        self.gripper.release()

        center_cam = self.cam_width / 2

        while self.robot.step(self.time_step) != -1:
            _, detections = self.perception.get_detections()
            dist = self.get_lidar_center_dist()

            # ================= SEARCH CUBE =================
            if self.state == "SEARCH_CUBE":
                self.on_state_enter("SEARCH_CUBE")

                if self.collected_cubes >= self.max_cubes:
                    print("🎉 MISSÃO CONCLUÍDA!")
                    self.base.reset()
                    break

                alvo = self.find_objects(
                    detections,
                    ["cubo_azul", "cubo_vermelho", "cubo_verde"]
                )

                if alvo:
                    self.target_cube_label = alvo["label"]
                    self.cube_color = alvo["label"]
                    print(f"[VISÃO] Cubo detectado: {self.target_cube_label}")
                    self.state = "APPROACH_CUBE"
                else:
                    self.base.move(0, 0, -self.turn_speed)

            # ================= APPROACH CUBE =================
            elif self.state == "APPROACH_CUBE":
                self.on_state_enter("APPROACH_CUBE")

                alvo = self.find_objects(detections, [self.target_cube_label])

                if not alvo:
                    print("[NAV] Cubo perdido → SEARCH_CUBE")
                    self.state = "SEARCH_CUBE"
                    continue

                self.print_distance(self.target_cube_label, dist)

                erro_px = center_cam - alvo["center"][0]
                vel = self.fuzzy_velocidade(dist)
                rot = self.fuzzy_rotacao(erro_px)

                if dist <= self.distancia_parar:
                    print("[NAV] Cheguei ao cubo")
                    self.base.reset()
                    self.grab_timer = 0
                    self.state = "GRAB_CUBE"
                    continue

                self.base.move(vel, 0.0, rot)

            # ================= GRAB CUBE =================
            elif self.state == "GRAB_CUBE":
                self.on_state_enter("GRAB_CUBE")

                self.base.reset()
                self.grab_timer += 1

                if self.grab_timer == 20:
                    print("[GRAB] Abrindo garra")
                    self.gripper.release()
                    self.arm.set_height(Arm.FRONT_FLOOR)

                elif self.grab_timer == 80:
                    print("[GRAB] Fechando garra")
                    self.gripper.grip()

                elif self.grab_timer == 130:
                    print("[GRAB] Elevando cubo (posição segura)")
                    self.arm.set_height(Arm.FRONT_PLATE)

                elif self.grab_timer > 200:
                    self.target_box_label = self.box_from_cube(self.cube_color)
                    print(f"[OK] Cubo preso → buscar {self.target_box_label}")
                    self.state = "SEARCH_BOX"

            # ================= SEARCH BOX =================
            elif self.state == "SEARCH_BOX":
                self.on_state_enter("SEARCH_BOX")

                alvo = self.find_objects(detections, [self.target_box_label])

                if alvo:
                    print(f"[VISÃO] Caixa detectada: {self.target_box_label}")
                    self.state = "APPROACH_BOX"
                else:
                    self.base.move(0, 0, -self.turn_speed)

            # ================= APPROACH BOX =================
            elif self.state == "APPROACH_BOX":
                self.on_state_enter("APPROACH_BOX")

                alvo = self.find_objects(detections, [self.target_box_label])

                if not alvo:
                    print("[NAV] Caixa perdida → SEARCH_BOX")
                    self.state = "SEARCH_BOX"
                    continue

                self.print_distance(self.target_box_label, dist)

                erro_px = center_cam - alvo["center"][0]
                vel = self.fuzzy_velocidade(dist)
                rot = self.fuzzy_rotacao(erro_px)

                if dist <= self.distancia_parar:
                    print("[NAV] Cheguei à caixa")
                    self.base.reset()
                    self.drop_timer = 0
                    self.state = "DROP_CUBE"
                    continue

                self.base.move(vel, 0.0, rot)

            # ================= DROP CUBE =================
            elif self.state == "DROP_CUBE":
                self.on_state_enter("DROP_CUBE")

                self.drop_timer += 1

                if self.drop_timer == 20:
                    print("[DROP] Baixando braço")
                    self.arm.set_height(Arm.FRONT_FLOOR)

                elif self.drop_timer == 60:
                    print("[DROP] Soltando cubo")
                    self.gripper.release()

                elif self.drop_timer > 100:
                    self.collected_cubes += 1
                    print(
                        f"[SUCESSO] Cubo depositado | Total: {self.collected_cubes}"
                    )

                    self.target_cube_label = None
                    self.target_box_label = None
                    self.cube_color = None
                    self.state = "SEARCH_CUBE"


if __name__ == "__main__":
    controller = YouBotController()
    controller.run()
