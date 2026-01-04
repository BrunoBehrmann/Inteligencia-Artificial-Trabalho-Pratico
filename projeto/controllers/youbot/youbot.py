from controller import Robot
from base import Base
from arm import Arm
from gripper import Gripper
from perception import Perception


class YouBotController:
    def __init__(self):
        self.robot = Robot()
        self.time_step = int(self.robot.getBasicTimeStep())

        self.base = Base(self.robot)
        self.arm = Arm(self.robot)
        self.gripper = Gripper(self.robot)

        self.camera = self.robot.getDevice("camera")
        self.camera.enable(self.time_step)

        self.perception = Perception(self.camera, "best.pt")

        self.state = "SEARCH"
        self.turn_speed = 0.1

        # Timers
        self.timer = 0

        # Configuração de tempos (convertidos para steps)
        self.pause_duration = int(3000 / self.time_step)  # 3 seg parado
        self.avoid_duration = int(
            2000 / self.time_step)  # 2 seg girando "cego"

    def run(self):
        print(f"=== MODO BUSCA COM GIRO CEGO ===")

        while self.robot.step(self.time_step) != -1:
            _, detections = self.perception.get_detections()

            # --- ESTADO 1: PROCURANDO ---
            if self.state == "SEARCH":
                self.base.move(0.0, 0.0, -self.turn_speed)

                if detections:
                    print("\nDetectado:")
                    for d in detections:
                        print(f" - {d['label']} ({d['conf']:.2f})")

                    self.base.reset()
                    self.state = "PAUSE"
                    self.timer = 0

            # --- ESTADO 2: PAUSA (ADMIRANDO O OBJETO) ---
            elif self.state == "PAUSE":
                self.base.reset()  # Garante que está parado
                self.timer += 1

                if self.timer >= self.pause_duration:
                    print("Saindo da pausa, girando para afastar...")
                    self.state = "AVOID"
                    self.timer = 0

            # --- ESTADO 3: AFASTANDO (GIRO CEGO) ---
            elif self.state == "AVOID":
                # Gira, mas NÃO verifica 'detections' aqui
                self.base.move(0.0, 0.0, -self.turn_speed)
                self.timer += 1

                # Se já girou o suficiente para tirar o objeto da tela
                if self.timer >= self.avoid_duration:
                    print("Retomando busca visual...")
                    self.state = "SEARCH"


if __name__ == "__main__":
    controller = YouBotController()
    controller.run()
