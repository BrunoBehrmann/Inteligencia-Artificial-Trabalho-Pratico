import image_processing as ip
import lidar_processing as lp
import fuzzy_logic as fl
import numpy as np


def executar(base, camera, lidar):
    # 1. Percepção
    dados_visao = ip.processar_imagem(camera)
    range_image = lidar.getRangeImage()

    if not dados_visao["detected"]:
        return "BUSCA_CUBO"

    # 2. Dados do LiDAR com FILTRO DE RUÍDO
    # Ignora leituras < 5cm (chassi do robô) e infinitas
    leituras_validas = [d for d in range_image if d >
                        0.05 and d != float('inf')]

    if not leituras_validas:
        dist_min = 10.0
    else:
        dist_min = min(leituras_validas)

    # Risco normalizado
    risco_val = np.clip(1.0 / max(dist_min, 0.1), 0, 1)

    # 3. Cálculo do VFH (Radianos)
    vfh_angle = lp.compute_vfh_direction(range_image)

    # Fallback: Se VFH falhar, usa visão
    if vfh_angle is None:
        direcao_alvo = dados_visao["theta"]
    else:
        direcao_alvo = vfh_angle

    # 4. Fusão de Direção
    peso_obstaculo = risco_val
    direcao_final = (direcao_alvo * peso_obstaculo) + \
        (dados_visao["theta"] * (1 - peso_obstaculo))

    # Trava no range do Fuzzy [-1.6, 1.6]
    direcao_final = np.clip(direcao_final, -1.6, 1.6)

    # 5. Controle Fuzzy
    v, w = fl.compute(direcao_final, risco_val)
    base.move(v, 0.0, w)

    # 6. Condição de Parada (Aumentada levemente para garantir detecção)
    if dist_min < 0.28:
        base.reset()
        return "COLETA"

    return "APROXIMACAO"
