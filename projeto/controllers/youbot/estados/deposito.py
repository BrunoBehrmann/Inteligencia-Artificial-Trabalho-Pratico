from . import utils


def executar(robot, arm, gripper):
    """
    Sequência de Depósito (Com espera real do simulador).
    """
    print(">>> Iniciando sequência de depósito...")

    # 1. Posicionar
    arm.set_height(arm.FRONT_CARDBOARD_BOX)
    utils.esperar(robot, 2.0)

    # 2. Soltar
    gripper.release()
    utils.esperar(robot, 1.0)

    # 3. Resetar
    arm.reset()
    utils.esperar(robot, 1.5)

    print(">>> Entrega concluída.")
    return "BUSCA_CUBO"
