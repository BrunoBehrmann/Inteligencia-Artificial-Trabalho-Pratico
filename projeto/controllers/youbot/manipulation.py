# Salve como: manipulation.py
from arm import ArmHeight

class ManipulationManager:
    def __init__(self, arm, gripper):
        self.arm = arm
        self.gripper = gripper
        self.timer = 0
        self.step = 0
        
    def reset_sequence(self):
        """Reinicia os contadores para começar uma nova animação"""
        self.timer = 0
        self.step = 0

    def run_pickup_sequence(self):
        """
        Executa a sequência de pegar. Retorna True quando termina.
        Deve ser chamada repetidamente no loop.
        """
        self.timer += 1
        
        if self.step == 0:
            # Baixar braço e abrir garra
            self.arm.set_height(ArmHeight.FRONT_FLOOR)
            self.gripper.release()
            if self.timer > 60: # Tempo para descer
                self.step = 1
                self.timer = 0
                
        elif self.step == 1:
            # Fechar garra
            self.gripper.grip()
            if self.timer > 40: # Tempo para fechar
                self.step = 2
                self.timer = 0
                
        elif self.step == 2:
            # Subir braço para transporte
            self.arm.set_height(ArmHeight.FRONT_PLATE)
            if self.timer > 50: # Tempo para subir
                return True # SEQUÊNCIA COMPLETA!
                
        return False # Ainda rodando

    def run_deposit_sequence(self):
        """Executa a sequência de depositar."""
        self.timer += 1
        
        if self.step == 0:
            # Posicionar sobre a caixa
            self.arm.set_height(ArmHeight.FRONT_CARDBOARD_BOX)
            if self.timer > 50:
                self.step = 1
                self.timer = 0
                
        elif self.step == 1:
            # Soltar
            self.gripper.release()
            if self.timer > 30:
                self.step = 2
                self.timer = 0
                
        elif self.step == 2:
            # Recolher braço
            self.arm.set_height(ArmHeight.RESET)
            if self.timer > 40:
                return True
                
        return False