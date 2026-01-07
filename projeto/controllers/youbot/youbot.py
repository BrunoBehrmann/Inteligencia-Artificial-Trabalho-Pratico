from controller import Robot
from base import Base
from arm import Arm
from gripper import Gripper
from perception import Perception
from fuzzy_control import FuzzyControl


class YouBotController:
    def __init__(self):
        self.robot = Robot()
        self.time_step = int(self.robot.getBasicTimeStep())

        self.steps_para_2s = int(2000 / self.time_step)

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

        self.ds_left = self.robot.getDevice("sensor_esquerda")
        self.ds_left.enable(self.time_step)

        self.ds_right = self.robot.getDevice("sensor_direita")
        self.ds_right.enable(self.time_step)

        self.limiar_desvio = 0.60
        self.velocidade_strafe = 0.5

        self.strafe_timer = 0
        self.last_strafe_vy = 0.0

        self.ignore_side_sensors = False

        self.fuzzy = FuzzyControl()

        self.state = "SEARCH_CUBE"
        self.last_state = None

        self.target_cube_label = None
        self.target_box_label = None
        self.cube_color = None

        self.collected_cubes = 0
        self.max_cubes = 15

        self.turn_speed = 0.5
        self.distancia_parar_cubo = 0.11
        self.distancia_parar_caixa = 0.20

        self.VEL_MAX = 0.5
        self.ROT_MAX = 1.0

        self.step_counter = 0
        self.grab_timer = 0
        self.drop_timer = 0
        self.backup_timer = 0

    def on_state_enter(self, state):
        if self.last_state != state:
            print(f"\n=== ESTADO: {state} ===")
            self.last_state = state

    def find_objects(self, detections, labels):
        objs = [d for d in detections if d["label"] in labels]
        return max(objs, key=lambda o: o["bbox"][3]) if objs else None

    def box_from_cube(self, cube_label):
        if "azul" in cube_label:
            return "caixa_azul"
        if "vermelho" in cube_label:
            return "caixa_vermelha"
        if "verde" in cube_label:
            return "caixa_verde"
        return None

    def get_lidar_center_dist(self):
        ranges = self.lidar_front.getRangeImage()
        mid = int(self.lidar_width / 2)
        vals = [x for x in ranges[mid - 20:mid + 20] if 0.05 < x < 3.0]
        return min(vals) if vals else 99.0

    def run(self):
        print("=== YOUBOT FSM CONTROLLER START ===")

        self.arm.reset()
        self.gripper.release()

        center_cam = self.cam_width / 2

        while self.robot.step(self.time_step) != -1:
            self.step_counter += 1
            _, detections = self.perception.get_detections()
            dist = self.get_lidar_center_dist()

            if self.state == "SEARCH_CUBE":
                self.on_state_enter("SEARCH_CUBE")
                alvo = self.find_objects(
                    detections, ["cubo_azul", "cubo_vermelho", "cubo_verde"])

                if alvo:
                    self.target_cube_label = alvo["label"]
                    self.cube_color = alvo["label"]
                    print(f"-> Alvo detectado: {self.target_cube_label}")
                    self.state = "APPROACH_CUBE"
                else:
                    self.base.move(0, 0, -self.turn_speed)

            elif self.state == "APPROACH_CUBE":
                self.on_state_enter("APPROACH_CUBE")
                alvo = self.find_objects(detections, [self.target_cube_label])

                if not alvo:
                    print("Perdi o cubo!")
                    self.state = "SEARCH_CUBE"
                    continue

                erro_px = center_cam - alvo["center"][0]
                v_norm, w_norm = self.fuzzy.compute(erro_px, dist)
                self.base.move(v_norm * self.VEL_MAX, 0, w_norm * self.ROT_MAX)

                if dist <= self.distancia_parar_cubo:
                    print(f"Cheguei no cubo! Dist: {dist:.2f}")
                    self.base.reset()
                    self.grab_timer = 0
                    self.state = "GRAB_CUBE"

            elif self.state == "GRAB_CUBE":
                self.on_state_enter("GRAB_CUBE")
                self.base.reset()
                self.grab_timer += 1

                if self.grab_timer == 1:
                    self.gripper.release()
                    self.arm.set_height(Arm.FRONT_PLATE)
                elif self.grab_timer == 40:
                    self.arm.set_height(Arm.FRONT_FLOOR)
                elif self.grab_timer == 80:
                    self.gripper.grip()
                elif self.grab_timer == 140:
                    self.arm.set_height(Arm.FRONT_PLATE)
                elif self.grab_timer > 180:
                    self.target_box_label = self.box_from_cube(self.cube_color)
                    print(f"Buscando caixa: {self.target_box_label}")
                    self.state = "SEARCH_BOX"

            elif self.state == "SEARCH_BOX":
                self.on_state_enter("SEARCH_BOX")
                alvo = self.find_objects(detections, [self.target_box_label])

                if alvo:
                    print(f"-> Caixa encontrada: {alvo['label']}")
                    self.state = "APPROACH_BOX"
                else:
                    self.base.move(0, 0, -self.turn_speed)

            elif self.state == "APPROACH_BOX":
                self.on_state_enter("APPROACH_BOX")
                alvo = self.find_objects(detections, [self.target_box_label])

                if not alvo:
                    print("Perdi a caixa!")
                    self.state = "SEARCH_BOX"

                    self.ignore_side_sensors = False
                    continue

                objetos_intrusos = [
                    d for d in detections if d['label'] != self.target_box_label]

                if len(objetos_intrusos) == 0:
                    if not self.ignore_side_sensors:
                        print(
                            ">>> Visão Limpa (Só Caixa)! Desativando sensores laterais.")
                        self.ignore_side_sensors = True

                if self.strafe_timer > 0:
                    self.strafe_timer -= 1
                    self.base.move(0.0, self.last_strafe_vy, 0.0)
                    continue

                val_esq = self.ds_left.getValue()
                val_dir = self.ds_right.getValue()

                final_vx = 0.0
                final_vy = 0.0
                final_w = 0.0

                if not self.ignore_side_sensors:
                    if val_esq - 0.20 < self.limiar_desvio:
                        print(
                            f"[OBSTRUÇÃO] Esquerda ({val_esq:.2f}m) -> Strafe Direita")
                        self.last_strafe_vy = self.velocidade_strafe

                        self.base.move(0.0, self.last_strafe_vy, 0.0)
                        continue

                    elif val_dir - 0.20 < self.limiar_desvio:
                        print(
                            f"[OBSTRUÇÃO] Direita ({val_dir:.2f}m) -> Strafe Esquerda")
                        self.last_strafe_vy = -self.velocidade_strafe

                        self.base.move(0.0, self.last_strafe_vy, 0.0)
                        continue

                erro_px = center_cam - alvo["center"][0]
                fuzzy_dist = dist if dist < 3.0 else 1.0
                v_norm, w_norm = self.fuzzy.compute(erro_px, fuzzy_dist)

                final_vx = v_norm * self.VEL_MAX
                final_vy = 0.0
                final_w = w_norm * self.ROT_MAX

                self.base.move(final_vx, final_vy, final_w)

                if dist <= self.distancia_parar_caixa and final_vy != 0.0:
                    print(
                        f"Cheguei e alinhei! (Esq:{val_esq:.2f} Dir:{val_dir:.2f})")
                    self.base.reset()
                    self.drop_timer = 0
                    self.state = "DROP_CUBE"

            elif self.state == "DROP_CUBE":
                self.on_state_enter("DROP_CUBE")
                self.base.reset()
                self.drop_timer += 1

                if self.drop_timer == 20:
                    self.arm.set_height(Arm.FRONT_PLATE)
                elif self.drop_timer == 60:
                    self.gripper.release()
                elif self.drop_timer > 100:
                    self.collected_cubes += 1
                    print(f"Cubo entregue! Total: {self.collected_cubes}")
                    self.state = "BACKUP"
                    self.backup_timer = 0

            elif self.state == "BACKUP":
                self.backup_timer += 1
                self.base.move(-0.3, 0, 0)

                if self.ignore_side_sensors:
                    self.ignore_side_sensors = False
                    print(">>> Sensores laterais REATIVADOS para o próximo ciclo.")

                if self.backup_timer > 30:
                    self.state = "SEARCH_CUBE"


if __name__ == "__main__":
    YouBotController().run()
