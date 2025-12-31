from . import utils  # Importação relativa (procura na mesma pasta 'estados')


def executar(robot, arm, gripper):
    """
    Sequência de Coleta Física (Com espera real do simulador).
    """
    print(">>> Iniciando sequência de coleta...")

    gripper.release()

    # 1. Baixar Braço
    arm.set_height(arm.FRONT_FLOOR)
    utils.esperar(robot, 1.5)  # O simulador avança por 1.5s

    # 2. Pegar
    gripper.grip()
    utils.esperar(robot, 1.0)

    # 3. Subir para posição de transporte (RESET)
    arm.set_height(arm.RESET)
    utils.esperar(robot, 1.0)

    print(">>> Cubo coletado.")
    return "NAVEGACAO_CAIXA"
