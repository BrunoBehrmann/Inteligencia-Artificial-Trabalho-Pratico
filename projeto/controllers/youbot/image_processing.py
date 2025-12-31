import cv2
import numpy as np


def processar_imagem(camera):
    """
    Responsável por: Receber imagem da câmera e detectar objetos por cor.
    Interface compatível para futura integração com YOLO/RNA.
    """
    raw_image = camera.getImage()
    if raw_image is None:
        return {"detected": False, "class": None, "theta": 0.0}

    width, height = camera.getWidth(), camera.getHeight()

    # 1. Pré-processamento: Conversão para OpenCV
    frame = np.frombuffer(raw_image, np.uint8).reshape((height, width, 4))
    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

    # 2. Conversão para HSV (mais estável para detecção de cores)
    hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)

    # 3. Definição das faixas de cores (Cores primárias para Cubos e Caixas)
    cores = {
        "red":   ([0, 150, 50], [10, 255, 255]),
        "green": ([40, 100, 50], [80, 255, 255]),
        "blue":  ([100, 150, 50], [130, 255, 255])
    }

    resultado = {
        "detected": False,
        "class": None,
        "theta": 0.0
    }

    # 4. Lógica de detecção simplificada (Substituta da YOLO)
    for cor_nome, (low, high) in cores.items():
        mask = cv2.inRange(hsv, np.array(low), np.array(high))

        # Remove ruídos pequenos (Erosão e Dilatação)
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)

        # Encontra contornos do objeto colorido
        cnts, _ = cv2.findContours(
            mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if len(cnts) > 0:
            # Pega o maior contorno encontrado (objeto mais próximo)
            c = max(cnts, key=cv2.contourArea)
            area = cv2.contourArea(c)

            if area > 500:  # Filtro de tamanho mínimo para evitar falso positivo
                M = cv2.moments(c)
                if M["m00"] != 0:
                    # Centro do objeto na imagem
                    cX = int(M["m10"] / M["m00"])

                    # Calcula o erro angular (theta) em relação ao centro da câmera
                    # Se theta > 0: objeto à direita | theta < 0: objeto à esquerda
                    centro_camera = width / 2
                    resultado["theta"] = (cX - centro_camera) / centro_camera
                    resultado["detected"] = True
                    resultado["class"] = cor_nome

                    # O robô foca no primeiro objeto relevante que encontrar
                    break

    return resultado
