import fuzzy_logic as fl
import image_processing as ip
import lidar_processing as lp
import numpy as np


def executar(base, camera, lidar, cor_alvo):
    """
    Navegação até a caixa de depósito com Fusão de Sensores e Filtro de Ruído.
    """
    # 1. Percepção
    range_image = lidar.getRangeImage()
    dados_visao = ip.processar_imagem(camera)

    # 2. Cálculo do Risco com FILTRO DE RUÍDO
    leituras_validas = [d for d in range_image if d >
                        0.05 and d != float('inf')]

    if not leituras_validas:
        dist_min = 10.0
    else:
        dist_min = min(leituras_validas)

    risco_val = np.clip(1.0 / max(dist_min, 0.1), 0, 1)

    # VFH
    vfh_angle = lp.compute_vfh_direction(range_image)
    if vfh_angle is None:
        vfh_angle = 0.0

    # 3. Lógica do Alvo
    theta_visual = vfh_angle
    alvo_na_mira = False

    if dados_visao["detected"] and dados_visao["class"] == cor_alvo:
        theta_visual = dados_visao["theta"]
        alvo_na_mira = True

    # 4. Fusão de Direção
    peso_obstaculo = risco_val
    direcao_final = (vfh_angle * peso_obstaculo) + \
        (theta_visual * (1 - peso_obstaculo))
    direcao_final = np.clip(direcao_final, -1.6, 1.6)

    # 5. Decisão Fuzzy
    v_fuzzy, w_fuzzy = fl.compute(direcao_final, risco_val)

    # 6. Condição de Chegada
    if alvo_na_mira and dist_min < 0.35:
        base.reset()
        print(f">>> Chegada na caixa {cor_alvo}. Iniciando DEPÓSITO.")
        return "DEPOSITO"

    # 7. Movimentação
    base.move(v_fuzzy, 0.0, w_fuzzy)

    return "NAVEGACAO_CAIXA"
