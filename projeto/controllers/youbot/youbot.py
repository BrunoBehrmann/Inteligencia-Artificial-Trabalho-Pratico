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

        self.fuzzy = FuzzyControl()

        self.state = "SEARCH_CUBE"
        self.last_state = None

        self.target_cube_label = None
        self.target_box_label = None
        self.cube_color = None

        self.collected_cubes = 0
        self.max_cubes = 15

        self.turn_speed = 0.5

        # Distâncias de parada diferentes
        self.distancia_parar_cubo = 0.12
        self.distancia_parar_caixa = 0.30  # Caixa precisa de mais espaço

        self.VEL_MAX = 0.5
        self.ROT_MAX = 1.0

        self.step_counter = 0

    def on_state_enter(self, state):
        if self.last_state != state:
            print(f"\n=== ESTADO: {state} ===")
            self.last_state = state

    def find_objects(self, detections, labels):
        objs = [d for d in detections if d["label"] in labels]
        # Retorna o objeto com maior altura (mais próximo)
        return max(objs, key=lambda o: o["bbox"][3]) if objs else None

    def box_from_cube(self, cube_label):
        # Ajuste os nomes exatamente como o seu YOLO retorna
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
        # Janela mais larga para pegar a caixa
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

            # ================= SEARCH CUBE =================
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

            # ================= APPROACH CUBE =================
            elif self.state == "APPROACH_CUBE":
                self.on_state_enter("APPROACH_CUBE")
                alvo = self.find_objects(detections, [self.target_cube_label])

                if not alvo:
                    print("Perdi o cubo!")
                    self.state = "SEARCH_CUBE"
                    continue

                erro_px = center_cam - alvo["center"][0]

                # Controle Fuzzy
                v_norm, w_norm = self.fuzzy.compute(erro_px, dist)
                self.base.move(v_norm * self.VEL_MAX, 0, w_norm * self.ROT_MAX)

                # Checagem de parada
                if dist <= self.distancia_parar_cubo:
                    print(f"Cheguei no cubo! Dist: {dist:.2f}")
                    self.base.reset()
                    self.grab_timer = 0
                    self.state = "GRAB_CUBE"

            # ================= GRAB CUBE =================
            elif self.state == "GRAB_CUBE":
                self.on_state_enter("GRAB_CUBE")
                self.base.reset()
                self.grab_timer += 1

                if self.grab_timer == 1:
                    self.gripper.release()
                    self.arm.set_height(Arm.FRONT_PLATE)
                elif self.grab_timer == 40:
                    self.arm.set_height(Arm.FRONT_FLOOR)  # Desce
                elif self.grab_timer == 80:
                    self.gripper.grip()  # Pega
                elif self.grab_timer == 140:
                    self.arm.set_height(Arm.FRONT_PLATE)  # Sobe
                elif self.grab_timer > 180:
                    self.target_box_label = self.box_from_cube(self.cube_color)
                    print(f"Buscando caixa: {self.target_box_label}")
                    self.state = "SEARCH_BOX"

            # ================= SEARCH BOX =================
            elif self.state == "SEARCH_BOX":
                self.on_state_enter("SEARCH_BOX")
                alvo = self.find_objects(detections, [self.target_box_label])

                if alvo:
                    print(f"-> Caixa encontrada: {alvo['label']}")
                    self.state = "APPROACH_BOX"
                else:
                    self.base.move(0, 0, -self.turn_speed)

            # ================= APPROACH BOX =================
            elif self.state == "APPROACH_BOX":
                self.on_state_enter("APPROACH_BOX")
                alvo = self.find_objects(detections, [self.target_box_label])

                if not alvo:
                    print("Perdi a caixa!")
                    self.state = "SEARCH_BOX"
                    continue

                erro_px = center_cam - alvo["center"][0]

                # --- TRUQUE DO LIDAR CEGO ---
                # Se o lidar retornar 99.0 (não viu a caixa) mas a câmera vê,
                # assumimos que está "Longe" (1.0m) para o robô andar para frente.
                fuzzy_dist = dist if dist < 3.0 else 1.0

                v_norm, w_norm = self.fuzzy.compute(erro_px, fuzzy_dist)
                self.base.move(v_norm * self.VEL_MAX, 0, w_norm * self.ROT_MAX)

                # Condição de parada (mais longe para caixa)
                if dist <= self.distancia_parar_caixa:
                    print(f"Na caixa! Dist: {dist:.2f}")
                    self.base.reset()
                    self.drop_timer = 0
                    self.state = "DROP_CUBE"

            # ================= DROP CUBE =================
            elif self.state == "DROP_CUBE":
                self.on_state_enter("DROP_CUBE")
                self.base.reset()
                self.drop_timer += 1

                if self.drop_timer == 20:
                    # Posição segura de entrega
                    self.arm.set_height(Arm.FRONT_PLATE)
                elif self.drop_timer == 60:
                    self.gripper.release()  # Solta
                elif self.drop_timer > 100:
                    self.collected_cubes += 1
                    print(f"Cubo entregue! Total: {self.collected_cubes}")

                    # Estado de Recuo para não bater na caixa ao sair
                    self.state = "BACKUP"
                    self.backup_timer = 0

            # ================= BACKUP =================
            elif self.state == "BACKUP":
                self.backup_timer += 1
                self.base.move(-0.3, 0, 0)  # Ré
                if self.backup_timer > 30:
                    self.state = "SEARCH_CUBE"


if __name__ == "__main__":
    YouBotController().run()
