from controller import Robot
from base import Base
from arm import Arm
from gripper import Gripper
from perception import Perception
import math

class YouBotController:
    def __init__(self):
        # --- INICIALIZAÇÃO DO ROBÔ ---
        self.robot = Robot()
        self.time_step = int(self.robot.getBasicTimeStep())

        self.base = Base(self.robot)
        self.arm = Arm(self.robot)
        self.gripper = Gripper(self.robot)

        # --- SENSORES DE VISÃO ---
        self.camera = self.robot.getDevice("camera")
        self.camera.enable(self.time_step)
        
        # Perception: Intervalo baixo para tracking fluido
        self.perception = Perception(self.camera, "best.pt")
        self.perception.interval = 0.05  

        # --- SENSORES LIDAR ---
        self.lidar_front = self.robot.getDevice("lidar")
        self.lidar_front.enable(self.time_step)
        self.lidar_front.enablePointCloud()

        self.lidar_top = self.robot.getDevice("lidar2") 
        self.lidar_top.enable(self.time_step)
        self.lidar_top.enablePointCloud()

        # --- VARIÁVEIS DE ESTADO ---
        self.state = "SEARCH"
        self.target_cube_label = None 
        
        # Guarda a última posição (x,y) do alvo para rastreamento
        self.last_target_center = None 
        
        # Timers
        self.state_timer = 0
        self.grab_timer = 0
        self.avoid_timer = 0
        
        # --- PARÂMETROS FÍSICOS ---
        self.turn_speed = 0.5
        self.distancia_ideal_pegar = 0.10

    # --- LEITURA DOS LIDARS ---
    def get_lidar_distances(self):
        range_front = self.lidar_front.getRangeImage()
        range_top = self.lidar_top.getRangeImage()

        if not range_front or not range_top:
            return 99.0, 99.0

        width = self.lidar_front.getHorizontalResolution()
        mid = int(width / 2)
        window = 10 
        
        vals_front = [x for x in range_front[mid-window : mid+window] 
                      if x < 20.0 and x != float('inf')]
        dist_baixo = sum(vals_front)/len(vals_front) if vals_front else 10.0

        vals_top = [x for x in range_top[mid-window : mid+window] 
                    if x < 20.0 and x != float('inf')]
        dist_cima = sum(vals_top)/len(vals_top) if vals_top else 10.0

        return dist_baixo, dist_cima

    # --- LÓGICA FUZZY ---
    def calcular_velocidade_fuzzy(self, distancia_alvo):
        # 1. Pertinência
        is_perto = 1.0 if distancia_alvo < 0.4 else max(0, 1 - (distancia_alvo - 0.4)/0.5)
        is_longe = 1.0 - is_perto

        # 2. Regras
        peso_rapido = is_longe
        peso_lento = is_perto

        # 3. Defuzzification
        numerador = (peso_rapido * 1.5) + (peso_lento * 0.2)
        denominador = peso_rapido + peso_lento + 0.0001
        
        return numerador / denominador

    # --- FUNÇÃO AUXILIAR DE TRACKING ---
    def encontrar_melhor_alvo(self, detections, center_cam):
        candidatos = [d for d in detections if d['label'] == self.target_cube_label]
        
        if not candidatos:
            return None

        if self.last_target_center is not None:
            # MODO TRACKING
            return min(candidatos, key=lambda c: math.dist(c['center'], self.last_target_center))
        else:
            # MODO BUSCA
            return min(candidatos, key=lambda c: abs(center_cam - c['center'][0]))

    # --- LOOP PRINCIPAL ---
    def run(self):
        print("=== YOUBOT: TIMING DA GARRA AJUSTADO ===")
        center_cam = self.camera.getWidth() / 2
        
        self.arm.reset()
        self.gripper.release()

        while self.robot.step(self.time_step) != -1:
            img, detections = self.perception.get_detections()
            dist_baixo, dist_cima = self.get_lidar_distances()

            # ---------------------------------------------------------
            # 1. SEARCH
            # ---------------------------------------------------------
            if self.state == "SEARCH":
                self.base.move(0.0, 0.0, -self.turn_speed) 
                
                self.last_target_center = None 

                if detections:
                    cubos = [d for d in detections if 'cubo' in d['label'] or 'cube' in d['label']]
                    if cubos:
                        melhor_cubo = min(cubos, key=lambda c: abs(center_cam - c['center'][0]))
                        
                        self.target_cube_label = melhor_cubo['label']
                        self.last_target_center = melhor_cubo['center'] 
                        
                        print(f"--> [VISÃO] Alvo Novo: {self.target_cube_label}")
                        self.base.reset()
                        self.state = "PRE_ALIGN"

            # ---------------------------------------------------------
            # 2. PRE_ALIGN
            # ---------------------------------------------------------
            elif self.state == "PRE_ALIGN":
                alvo = self.encontrar_melhor_alvo(detections, center_cam)
                
                if alvo:
                    self.last_target_center = alvo['center'] 
                    
                    erro = center_cam - alvo['center'][0]
                    
                    if abs(erro) < 30: 
                        self.base.reset()
                        self.state = "VERIFY"
                        self.state_timer = 0
                    else:
                        kp = -0.005 
                        rot = kp * erro
                        rot = max(min(rot, 0.8), -0.8)
                        self.base.move(0.0, 0.0, rot)
                else:
                    print("Perdi o alvo no tracking (Pre-Align).")
                    self.base.move(0.0, 0.0, 0.0)
                    self.state = "SEARCH"

            # ---------------------------------------------------------
            # 3. VERIFY
            # ---------------------------------------------------------
            elif self.state == "VERIFY":
                self.base.reset()
                self.state_timer += 1
                if self.state_timer < 10: continue

                eh_baixo = (dist_baixo < 2.5)
                eh_alto = (dist_cima < 2.5)
                
                if eh_baixo and not eh_alto:
                    print(f"--> [LIDAR] Confirmado: Cubo.")
                    self.state = "FINE_ALIGN" 
                elif eh_baixo and eh_alto:
                    print("--> [LIDAR] Parede. Fugindo.")
                    self.state = "AVOID" 
                    self.avoid_timer = 0
                else:
                    self.state = "FINE_ALIGN"

            # ---------------------------------------------------------
            # 4. FINE_ALIGN
            # ---------------------------------------------------------
            elif self.state == "FINE_ALIGN":
                alvo = self.encontrar_melhor_alvo(detections, center_cam)
                
                if alvo:
                    self.last_target_center = alvo['center'] 
                    
                    erro = center_cam - alvo['center'][0]
                    
                    if abs(erro) < 10:
                        print("--> [MIRA] Travada. AVANÇAR!")
                        self.base.reset()
                        self.state = "APPROACH"
                    else:
                        kp = -0.004 
                        rot = kp * erro
                        
                        if rot > 0.3: rot = 0.3
                        if rot < -0.3: rot = -0.3
                        if rot > 0 and rot < 0.05: rot = 0.05
                        if rot < 0 and rot > -0.05: rot = -0.05
                        
                        self.base.move(0.0, 0.0, rot)
                else:
                    self.state = "SEARCH"

            # ---------------------------------------------------------
            # 5. APPROACH
            # ---------------------------------------------------------
            elif self.state == "APPROACH":
                alvo = self.encontrar_melhor_alvo(detections, center_cam)
                
                if alvo:
                    self.last_target_center = alvo['center'] 
                    
                    erro = center_cam - alvo['center'][0]
                    if abs(erro) > 40:
                        print("--> [DESVIO] Realinhando...")
                        self.base.reset()
                        self.state = "FINE_ALIGN"
                        continue 
                
                rotacao = 0.0
                vel_frente = self.calcular_velocidade_fuzzy(dist_baixo)
                
                if dist_baixo <= (self.distancia_ideal_pegar):
                    print("--> [NAV] Cheguei.")
                    self.base.reset()
                    self.state = "GRAB"
                    self.grab_timer = 0
                    vel_frente = 0.0
                
                if not alvo and dist_baixo < 0.5:
                     if vel_frente > 0.3: vel_frente = 0.3
                elif not alvo and dist_baixo >= 0.5:
                     print("Perdi visual longe. Reiniciando.")
                     self.state = "SEARCH"
                     vel_frente = 0.0

                self.base.move(vel_frente, 0, rotacao)

            # ---------------------------------------------------------
            # 6. GRAB (AJUSTADO PARA SÓ FECHAR DEPOIS QUE DESCER)
            # ---------------------------------------------------------
            elif self.state == "GRAB":
                self.base.reset()
                self.grab_timer += 1
                
                # Passo 1: Começa a descer
                if self.grab_timer == 20: 
                    print("--> [BRAÇO] Baixando (Garra Aberta)...")
                    self.gripper.release() # Garante que desce aberta
                    self.arm.set_height(Arm.FRONT_FLOOR)
                
                # Passo 2: ESPERA MAIS TEMPO (até 100) para garantir que chegou no chão
                elif self.grab_timer == 100: 
                    print("--> [GARRA] Agora sim, fechando...")
                    self.gripper.grip()
                
                # Passo 3: Espera fechar bem
                elif self.grab_timer == 150: 
                    print("--> [BRAÇO] Levantando...")
                    self.arm.set_height(Arm.FRONT_PLATE)
                
                # Passo 4: Fim
                elif self.grab_timer > 220:
                    print("--> [SUCESSO] Peguei! Voltando.")
                    self.state = "SEARCH"

            # ---------------------------------------------------------
            # AVOID
            # ---------------------------------------------------------
            elif self.state == "AVOID":
                self.base.move(0.0, 0.0, -self.turn_speed)
                self.avoid_timer += 1
                if self.avoid_timer > 40:
                    self.state = "SEARCH"

if __name__ == "__main__":
    controller = YouBotController()
    controller.run()