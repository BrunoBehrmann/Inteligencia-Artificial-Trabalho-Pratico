import sys
from controller import Robot
from base import Base
from arm import Arm
from gripper import Gripper

# Verificação de segurança
try:
    import numpy as np
    import cv2
except ImportError:
    print("\n[ERRO] Bibliotecas nativas não encontradas!")
    sys.exit(1)

import lidar_processing as lp
import fuzzy_logic as fl
import image_processing as ip
import estados


class YouBotFSM(Robot):
    def __init__(self):
        super().__init__()
        self.time_step = int(self.getBasicTimeStep())

        self.base = Base(self)
        self.arm = Arm(self)
        self.gripper = Gripper(self)

        self.camera = self.getDevice("camera")
        self.camera.enable(self.time_step)
        self.lidar = self.getDevice("lidar")
        self.lidar.enable(self.time_step)

        self.estado = "BUSCA_CUBO"
        self.dados_visao = None
        self.cor_alvo = None

        print(f">>> Sistema Iniciado: Estado = {self.estado}")

    def mudar_estado(self, novo_estado):
        if self.estado != novo_estado:
            print(f">>> MUDANÇA DE ESTADO: {self.estado} -> {novo_estado}")
            self.estado = novo_estado

    def run(self):
        while self.step(self.time_step) != -1:
            # Percepção Global
            self.dados_visao = ip.processar_imagem(self.camera)

            # MÁQUINA DE ESTADOS
            if self.estado == "BUSCA_CUBO":
                proximo = estados.executar_busca(self.base, self.camera)
                self.mudar_estado(proximo)

            elif self.estado == "APROXIMACAO":
                if self.dados_visao["detected"]:
                    self.cor_alvo = self.dados_visao["class"]
                proximo = estados.executar_aproximacao(
                    self.base, self.camera, self.lidar)
                self.mudar_estado(proximo)

            elif self.estado == "COLETA":
                # PASSA 'self' PARA USAR O WAIT DO SIMULADOR
                proximo = estados.executar_coleta(self, self.arm, self.gripper)
                self.mudar_estado(proximo)

            elif self.estado == "NAVEGACAO_CAIXA":
                proximo = estados.executar_navegacao_caixa(
                    self.base, self.camera, self.lidar, self.cor_alvo)
                self.mudar_estado(proximo)

            elif self.estado == "DEPOSITO":
                # PASSA 'self' PARA USAR O WAIT DO SIMULADOR
                proximo = estados.executar_deposito(
                    self, self.arm, self.gripper)
                if proximo == "BUSCA_CUBO":
                    self.cor_alvo = None
                self.mudar_estado(proximo)


if __name__ == "__main__":
    robot = YouBotFSM()
    robot.run()
