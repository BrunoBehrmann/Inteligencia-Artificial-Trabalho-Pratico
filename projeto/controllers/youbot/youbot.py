from controller import Robot
from base import Base
from arm import Arm, ArmHeight
from gripper import Gripper

# Importando nossos módulos
from fuzzy_control import FuzzyController
from manipulation import ManipulationManager
from perception import PerceptionSystem


class MissionController:
    def __init__(self):
        self.robot = Robot()
        self.timestep = int(self.robot.getBasicTimeStep())

        # Hardware
        self.base = Base(self.robot)
        self.arm = Arm(self.robot)
        self.gripper = Gripper(self.robot)

        # Módulos Personalizados
        self.fuzzy = FuzzyController()
        self.manipulation = ManipulationManager(self.arm, self.gripper)
        self.perception = PerceptionSystem(
            self.robot.getDevice("lidar"),
            self.robot.getDevice("camera")
        )

        # Habilitar sensores
        self.robot.getDevice("lidar").enable(self.timestep)
        self.robot.getDevice("camera").enable(self.timestep)
        self.robot.getDevice("lidar").enablePointCloud()

        # Estado Inicial
        self.state = "SEARCH_CUBE"
        self.current_target_color = None

        # Config Inicial
        self.arm.set_height(ArmHeight.RESET)
        self.gripper.release()

        # --- Variáveis de Controle ---
        self.step_counter = 0
        self.last_cube_detection = (False, 0.0, None)
        self.last_box_detection = (False, 0.0, None)

        # --- SUAVIZAÇÃO (Rampa) ---
        self.current_vx = 0.0
        self.current_omega = 0.0

    def run(self):
        while self.robot.step(self.timestep) != -1:

            run_vision = (self.step_counter % 5 == 0)

            # 1. PERCEPÇÃO
            _, raw_dist = self.perception.get_fuzzy_dist()

            # Cálculo Real do Risco (para quando estiver detectando algo)
            if raw_dist < 0.1:
                risco_real = 1.0
            else:
                risco_real = min(1.0, 0.5 / raw_dist)

            # 2. MÁQUINA DE ESTADOS
            # Por padrão, assumimos risco real e direção 0
            risco_input = risco_real
            direcao_input = 0.0

            found = False

            # --- ESTADO: PROCURAR CUBO ---
            if self.state == "SEARCH_CUBE":
                if run_vision:
                    found, error, color = self.perception.detect_target('cubo')
                    self.last_cube_detection = (found, error, color)
                    if found:
                        print(f"[YOLO] Cubo: {color} | Erro: {error:.2f}")

                found, error, color = self.last_cube_detection

                if found:
                    # Se achou, usa o erro real e o risco real
                    direcao_input = error

                    if raw_dist < 0.35 and abs(error) < 0.15:
                        print("--- PEGANDO CUBO ---")
                        self.base.reset()
                        self.current_target_color = color
                        self.manipulation.reset_sequence()
                        self.state = "PICKUP_SEQUENCE"
                        self.current_vx = 0.0
                        self.current_omega = 0.0
                else:
                    # --- MODO BUSCA (SOLUÇÃO FUZZY PURA) ---
                    # Criamos um "Alvo Fantasma" na direita
                    # 1.5 rad é "Muito à Direita" no universo do Fuzzy
                    direcao_input = 1.5

                    # Forçamos Risco Zero para o Fuzzy liberar velocidade
                    risco_input = 0.0

            # --- ESTADO: PEGAR ---
            elif self.state == "PICKUP_SEQUENCE":
                if self.manipulation.run_pickup_sequence():
                    self.state = "SEARCH_BOX"
                    self.last_box_detection = (False, 0.0, None)
                self.step_counter += 1
                continue

            # --- ESTADO: PROCURAR CAIXA ---
            elif self.state == "SEARCH_BOX":
                if run_vision:
                    found, error, _ = self.perception.detect_target(
                        'caixa', self.current_target_color)
                    self.last_box_detection = (found, error, None)

                found, error, _ = self.last_box_detection

                if found:
                    direcao_input = error
                    if raw_dist < 0.45 and abs(error) < 0.15:
                        print("--- DEPOSITANDO ---")
                        self.base.reset()
                        self.manipulation.reset_sequence()
                        self.state = "DEPOSIT_SEQUENCE"
                        self.current_vx = 0.0
                        self.current_omega = 0.0
                else:
                    # Busca Circular à Direita
                    direcao_input = 1.5
                    risco_input = 0.0

            # --- ESTADO: DEPOSITAR ---
            elif self.state == "DEPOSIT_SEQUENCE":
                if self.manipulation.run_deposit_sequence():
                    self.state = "BACKING_UP"
                    self.backup_timer = 0
                self.step_counter += 1
                continue

            # --- ESTADO: RECUO ---
            elif self.state == "BACKING_UP":
                self.backup_timer += 1
                self.base.move(-0.2, 0, 0)
                if self.backup_timer > 40:
                    print("--- REINICIANDO ---")
                    self.base.reset()
                    self.state = "SEARCH_CUBE"
                    self.last_cube_detection = (False, 0.0, None)
                self.step_counter += 1
                continue

            # 3. NAVEGAÇÃO FUZZY (A Lógica acontece aqui!)
            # O controlador recebe (Direita=1.5, Risco=0)
            # Regra ativada interna: IF Risco Baixo AND Direção Direita THEN W = Dir_Suave/Medio
            target_v, target_w = self.fuzzy.compute(direcao_input, risco_input)

            # --- FILTRO DE RAMPA ---
            alpha = 0.2
            self.current_vx = (1 - alpha) * self.current_vx + alpha * target_v
            self.current_omega = (1 - alpha) * \
                self.current_omega + alpha * target_w

            # Envia para a base
            self.base.move(self.current_vx, 0, self.current_omega)

            self.step_counter += 1


if __name__ == "__main__":
    controller = MissionController()
    controller.run()
