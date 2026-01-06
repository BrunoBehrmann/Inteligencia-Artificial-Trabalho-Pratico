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

        self.lidar2 = self.robot.getDevice("lidar2")
        if self.lidar2:
            self.lidar2.enable(self.time_step)
            self.lidar2_width = self.lidar2.getHorizontalResolution()
        else:
            self.lidar2_width = 0

        self.ds_left = self.robot.getDevice("sensor_esquerda")
        self.ds_left.enable(self.time_step)
        self.ds_right = self.robot.getDevice("sensor_direita")
        self.ds_right.enable(self.time_step)

        self.limiar_desvio = 0.60
        self.velocidade_strafe = 0.4

        self.fuzzy = FuzzyControl()

        self.state = "SEARCH_CUBE"
        self.last_state = None

        self.target_cube_label = None
        self.target_box_label = None
        self.cube_color = None

        self.turn_speed = 0.5

        self.distancia_parar_cubo = 0.11
        self.distancia_parar_caixa = 0.16

        self.VEL_MAX = 0.5
        self.ROT_MAX = 1.0

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
        vals = [x for x in ranges[mid - 10:mid + 10] if 0.05 < x < 3.0]
        return min(vals) if vals else 99.0

    def get_lidar2_dist(self):
        if not self.lidar2:
            return self.get_lidar_center_dist()
        ranges = self.lidar2.getRangeImage()
        mid = int(self.lidar2_width / 2)
        vals = [x for x in ranges[mid - 15:mid + 15] if 0.05 < x < 3.0]
        return min(vals) if vals else 99.0

    def run(self):
        print("=== YOUBOT CONTROLLER START ===")
        self.arm.reset()
        self.gripper.release()
        center_cam = self.cam_width / 2

        while self.robot.step(self.time_step) != -1:
            _, detections = self.perception.get_detections()
            dist_cubo = self.get_lidar_center_dist()
            dist_caixa = self.get_lidar2_dist()

            # SEARCH CUBE
            if self.state == "SEARCH_CUBE":
                self.on_state_enter("SEARCH_CUBE")
                alvo = self.find_objects(
                    detections, ["cubo_azul", "cubo_vermelho", "cubo_verde"])
                if alvo:
                    self.target_cube_label = alvo["label"]
                    self.cube_color = alvo["label"]
                    self.state = "APPROACH_CUBE"
                else:
                    self.base.move(0, 0, -self.turn_speed)

            # APPROACH CUBE
            elif self.state == "APPROACH_CUBE":
                self.on_state_enter("APPROACH_CUBE")
                alvo = self.find_objects(detections, [self.target_cube_label])
                if not alvo:
                    self.state = "SEARCH_CUBE"
                    continue

                erro_px = center_cam - alvo["center"][0]
                v_norm, w_norm = self.fuzzy.compute(erro_px, dist_cubo)
                self.base.move(v_norm * self.VEL_MAX, 0, w_norm * self.ROT_MAX)

                if dist_cubo <= self.distancia_parar_cubo:
                    self.base.reset()
                    self.state = "GRAB_CUBE"
                    self.grab_timer = 0

            # GRAB CUBE
            elif self.state == "GRAB_CUBE":
                self.on_state_enter("GRAB_CUBE")
                self.base.reset()
                self.grab_timer += 1
                if self.grab_timer == 1:
                    self.arm.set_height(Arm.FRONT_FLOOR)
                elif self.grab_timer == 40:
                    self.gripper.grip()
                elif self.grab_timer == 80:
                    self.arm.set_height(Arm.FRONT_PLATE)
                elif self.grab_timer > 120:
                    self.target_box_label = self.box_from_cube(self.cube_color)
                    self.state = "SEARCH_BOX"

            # SEARCH BOX
            elif self.state == "SEARCH_BOX":
                self.on_state_enter("SEARCH_BOX")
                alvo = self.find_objects(detections, [self.target_box_label])
                if alvo:
                    self.state = "APPROACH_BOX"
                else:
                    self.base.move(0, 0, -self.turn_speed)

            # APPROACH BOX
            elif self.state == "APPROACH_BOX":
                self.on_state_enter("APPROACH_BOX")
                alvo = self.find_objects(detections, [self.target_box_label])
                if not alvo:
                    self.state = "SEARCH_BOX"
                    continue

                val_esq = self.ds_left.getValue()
                val_dir = self.ds_right.getValue()

                if val_esq < 0.35:
                    self.base.move(0, self.velocidade_strafe, 0)
                    continue
                elif val_dir < 0.35:
                    self.base.move(0, -self.velocidade_strafe, 0)
                    continue

                erro_px = center_cam - alvo["center"][0]
                if dist_caixa < 0.4:
                    erro_px *= 1.5

                dist_segura = max(0.0, dist_caixa - 0.06)
                v_norm, w_norm = self.fuzzy.compute(erro_px, dist_segura)
                self.base.move(v_norm * self.VEL_MAX, 0, w_norm * self.ROT_MAX)

                if dist_caixa <= (self.distancia_parar_caixa + 0.05) and abs(erro_px) < 12:
                    self.base.reset()
                    self.arm.set_height(Arm.FRONT_PLATE)
                    self.arm.set_orientation(Arm.FRONT)
                    self.drop_timer = 0
                    self.state = "DROP_CUBE"

            # DROP CUBE
            elif self.state == "DROP_CUBE":
                self.on_state_enter("DROP_CUBE")
                self.base.reset()
                self.drop_timer += 1

                if self.drop_timer == 40:
                    self.gripper.release()
                elif self.drop_timer == 80:
                    self.arm.reset()
                elif self.drop_timer > 120:
                    self.state = "BACKUP"
                    self.backup_timer = 0

            # BACKUP
            elif self.state == "BACKUP":
                self.backup_timer += 1
                self.base.move(-0.3, 0, 0)
                if self.backup_timer > 30:
                    self.state = "SEARCH_CUBE"
