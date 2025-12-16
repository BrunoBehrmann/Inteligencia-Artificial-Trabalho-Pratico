"""
Controlador YouBot para Coleta de Dataset
"""
from controller import Robot, Keyboard
from base import Base
from arm import Arm
from gripper import Gripper
import cv2
import numpy as np
import os
from datetime import datetime

class YouBotController:
    def __init__(self):
        # Inicialização do Robô
        self.robot = Robot()
        self.time_step = int(self.robot.getBasicTimeStep())
        
        # Inicializa as partes do corpo
        self.base = Base(self.robot)
        self.arm = Arm(self.robot)
        self.gripper = Gripper(self.robot)

        # Inicializa Câmera
        self.camera = self.robot.getDevice("camera")
        self.camera.enable(self.time_step)

        # Inicializa Lidar
        self.lidar = self.robot.getDevice("lidar")
        self.lidar.enable(self.time_step)
        self.lidar.enablePointCloud()

        # Inicializa Teclado
        self.keyboard = self.robot.getKeyboard()
        self.keyboard.enable(self.time_step)

        # Pasta para salvar imagens
        self.save_dir = "dataset_coleta"
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
            print(f"Pasta '{self.save_dir}' criada.")

    def save_image(self):
        """Captura e salva a imagem da câmera"""
        # Pega a imagem crua do Webots (BGRA)
        raw_image = self.camera.getImage()
        
        if raw_image:
            # Converte bytes para array numpy
            img = np.frombuffer(raw_image, np.uint8).reshape((self.camera.getHeight(), self.camera.getWidth(), 4))
            
            # Remove o canal Alpha (transparência), deixando apenas BGR para o OpenCV
            img = img[:, :, :3]
            
            # Gera um nome único com timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = os.path.join(self.save_dir, f"img_{timestamp}.jpg")
            
            # Salva
            cv2.imwrite(filename, img)
            print(f"Imagem salva: {filename}")

    def run(self):
        print("=== CONTROLE MANUAL INICIADO ===")
        print("[Seta Cima/Baixo] : Mover Frente/Trás")
        print("[Seta Esq/Dir]    : Girar")
        print("[A / D]           : Strafe (Andar de lado)")
        print("[W / S]           : Braço Cima/Baixo")
        print("[P]               : TIRAR FOTO (Salvar no Dataset)")
        
        # Loop principal da simulação
        while self.robot.step(self.time_step) != -1:
            key = self.keyboard.getKey()
            
            # -- Lógica de Movimentação --
            # Se nenhuma tecla for apertada, o robô para (reset)
            # Isso impede que ele continue andando sozinho
            
            if key == Keyboard.UP:
                self.base.forwards()
            elif key == Keyboard.DOWN:
                self.base.backwards()
            elif key == Keyboard.RIGHT:
                self.base.turn_left()
            elif key == Keyboard.LEFT:
                self.base.turn_right()
            elif key == ord('A'):
                self.base.strafe_left()
            elif key == ord('D'):
                self.base.strafe_right()
            else:
                self.base.reset() # Para o robô se soltar a tecla

            # -- Controle Básico do Braço (Para tirar o braço da frente da câmera se precisar) --
            if key == ord('W'):
                self.arm.increase_height()
            elif key == ord('S'):
                self.arm.decrease_height()

            # -- Captura de Imagem --
            if key == ord('P'):
                self.save_image()
                # Pequeno delay lógico para não tirar 50 fotos se segurar o P
                # (O ideal é apertar e soltar rápido)

if __name__ == "__main__":
    controller = YouBotController()
    controller.run()