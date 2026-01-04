from controller import Robot
from base import Base
from arm import Arm
from gripper import Gripper
from perception import Perception
import math

class YouBotController:
    def __init__(self):
        # --- INICIALIZAÇÃO ---
        self.robot = Robot()
        self.time_step = int(self.robot.getBasicTimeStep())

        self.base = Base(self.robot)
        self.arm = Arm(self.robot)
        self.gripper = Gripper(self.robot)

        # --- VISÃO ---
        self.camera = self.robot.getDevice("camera")
        self.camera.enable(self.time_step)
        self.cam_width = self.camera.getWidth()
        
        self.perception = Perception(self.camera, "best.pt")
        self.perception.interval = 0.05  

        # --- LIDARS ---
        self.lidar_front = self.robot.getDevice("lidar")
        self.lidar_front.enable(self.time_step)
        self.lidar_front.enablePointCloud()
        self.lidar_width = self.lidar_front.getHorizontalResolution()
        self.lidar_fov = self.lidar_front.getFov()

        self.lidar_top = self.robot.getDevice("lidar2") 
        self.lidar_top.enable(self.time_step)
        self.lidar_top.enablePointCloud()

        # --- ESTADOS ---
        self.state = "SEARCH_RADAR" 
        self.target_cube_label = None 
        self.last_target_center = None 
        
        self.state_timer = 0
        self.grab_timer = 0
        self.avoid_timer = 0
        
        # --- PARÂMETROS ---
        self.turn_speed = 0.5
        self.distancia_ideal_pegar = 0.11

    def obter_erro_angular_lidar(self):
        range_front = self.lidar_front.getRangeImage()
        range_top = self.lidar_top.getRangeImage()
        
        if not range_front: return None, 99.0

        melhor_distancia = 999.0
        melhor_indice = -1

        for i in range(self.lidar_width):
            d_baixo = range_front[i]
            d_cima = range_top[i]

            # Filtros
            if d_baixo > 1.2 or d_baixo < 0.05: continue

            # Geometria
            eh_cubo = (d_baixo < 2.0) and (d_cima == float('inf') or (d_cima > d_baixo + 0.15))

            if eh_cubo:
                if d_baixo < melhor_distancia:
                    melhor_distancia = d_baixo
                    melhor_indice = i

        if melhor_indice != -1:
            center_index = self.lidar_width / 2
            erro_index = (melhor_indice - center_index)
            angulo_erro = (erro_index / self.lidar_width) * self.lidar_fov
            return -angulo_erro, melhor_distancia
        
        return None, 99.0

    def get_lidar_center_dist(self):
        range_front = self.lidar_front.getRangeImage()
        if not range_front: return 99.0
        mid = int(self.lidar_width / 2)
        vals = [x for x in range_front[mid-20 : mid+20] if 0.04 < x < 2.0]
        return min(vals) if vals else 99.0

    def run(self):
        print("=== YOUBOT: MODO DEBUG ATIVADO ===")
        center_cam = self.camera.getWidth() / 2
        self.arm.reset()
        self.gripper.release()

        while self.robot.step(self.time_step) != -1:
            img, detections = self.perception.get_detections()
            dist_centro = self.get_lidar_center_dist()

            # ---------------------------------------------------------
            # 1. SEARCH_RADAR
            # ---------------------------------------------------------
            if self.state == "SEARCH_RADAR":
                erro_ang, dist_obj = self.obter_erro_angular_lidar()

                if erro_ang is not None:
                    # DEBUG RADAR
                    # print(f"   [RADAR] Alvo Potencial: {dist_obj:.2f}m | Erro: {erro_ang:.2f}")

                    if dist_obj < 0.40: 
                        print(f"--> [RADAR] Perto o suficiente ({dist_obj:.2f}m). Identificando...")
                        self.base.reset()
                        self.state = "IDENTIFY_COLOR"
                        self.state_timer = 0
                        continue

                    if abs(erro_ang) < 0.05:
                        self.base.reset()
                        self.state = "IDENTIFY_COLOR"
                        self.state_timer = 0
                    else:
                        rot = erro_ang * 0.8
                        rot = max(min(rot, 0.6), -0.6)
                        self.base.move(0.0, 0.0, rot)
                else:
                    self.base.move(0.0, 0.0, -self.turn_speed)

            # ---------------------------------------------------------
            # 2. IDENTIFY_COLOR (DEBUG DETALHADO AQUI)
            # ---------------------------------------------------------
            elif self.state == "IDENTIFY_COLOR":
                self.base.reset()
                self.state_timer += 1
                if self.state_timer < 5: continue 

                melhor_candidato = None
                
                if detections:
                    cubos = [d for d in detections if 'cubo' in d['label'] or 'cube' in d['label']]
                    
                    if cubos:
                        print(f"--- [DEBUG VISÃO] Analisando {len(cubos)} candidatos ---")
                        # Imprime a lista para você ver quem é quem
                        for i, c in enumerate(cubos):
                            # bbox[3] é a base do cubo. Quanto MAIOR, mais embaixo (perto).
                            print(f"   Cand {i}: {c['label']} | Base Y (bbox3): {c['bbox'][3]:.1f} | Centro X: {c['center'][0]:.1f}")

                        # A LÓGICA DE ESCOLHA:
                        melhor_candidato = max(cubos, key=lambda c: c['bbox'][3])
                        print(f"   >>> ESCOLHIDO: {melhor_candidato['label']} (Maior Y)")

                if melhor_candidato:
                    self.target_cube_label = melhor_candidato['label']
                    self.last_target_center = melhor_candidato['center']
                    print(f"--> [DECISÃO] Alvo travado: {self.target_cube_label}. Iniciando aproximação.")
                    self.state = "APPROACH"
                else:
                    if dist_centro < 0.2:
                        print("--> [CEGO] Muito perto e sem visual. Tentando pegar mesmo assim.")
                        self.state = "GRAB"
                    else:
                        print("--> [FALHA] Nenhum cubo identificado. Voltando ao Radar.")
                        self.state = "SEARCH_RADAR"

            # ---------------------------------------------------------
            # 3. APPROACH
            # ---------------------------------------------------------
            elif self.state == "APPROACH":
                candidatos = [d for d in detections if d['label'] == self.target_cube_label]
                alvo = None
                if candidatos:
                    alvo = max(candidatos, key=lambda c: c['bbox'][3])

                if dist_centro <= self.distancia_ideal_pegar:
                    print(f"--> [NAV] Cheguei no alvo ({dist_centro:.3f}m).")
                    self.base.reset()
                    self.state = "GRAB"
                    self.grab_timer = 0
                    continue

                vel_frente = 0.0
                rotacao = 0.0

                if alvo:
                    # DEBUG APPROACH
                    # print(f"   [APP] Visual Ok. Dist: {dist_centro:.2f}m")
                    self.last_target_center = alvo['center']
                    erro = center_cam - alvo['center'][0]
                    rotacao = -0.003 * erro
                    
                    if dist_centro > 0.3: vel_frente = 0.4
                    else: vel_frente = 0.15 

                elif dist_centro < 0.6:
                    print(f"   [APP] Modo Cego (Perto: {dist_centro:.2f}m).")
                    vel_frente = 0.15 
                    rotacao = 0.0
                else:
                    print("--> [PERDA] Perdi alvo longe. Reiniciando.")
                    self.state = "SEARCH_RADAR"
                    vel_frente = 0.0

                self.base.move(vel_frente, 0.0, rotacao)

            # ---------------------------------------------------------
            # 4. GRAB
            # ---------------------------------------------------------
            elif self.state == "GRAB":
                self.base.reset()
                self.grab_timer += 1
                
                if self.grab_timer == 1: print("--> [GRAB] Iniciando sequência de pega.")

                if self.grab_timer == 20: 
                    self.gripper.release()
                    self.arm.set_height(Arm.FRONT_FLOOR)
                elif self.grab_timer == 100: 
                    self.gripper.grip()
                elif self.grab_timer == 150: 
                    self.arm.set_height(Arm.FRONT_PLATE)
                elif self.grab_timer > 220:
                    print("--> [SUCESSO] Peguei! Voltando a buscar.")
                    self.target_cube_label = None 
                    self.state = "SEARCH_RADAR"

            # ---------------------------------------------------------
            # AVOID
            # ---------------------------------------------------------
            elif self.state == "AVOID":
                self.base.move(0.0, 0.0, -self.turn_speed)
                self.avoid_timer += 1
                if self.avoid_timer > 30:
                    self.state = "SEARCH_RADAR"

if __name__ == "__main__":
    controller = YouBotController()
    controller.run()