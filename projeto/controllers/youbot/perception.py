import cv2
import numpy as np
import time
from ultralytics import YOLO


class Perception:
    def __init__(self, camera, model_path="best.pt"):
        self.camera = camera
        print(f"[PERCEPTION] Carregando modelo de: {model_path}")

        # Tenta carregar o modelo. Se falhar, avisa o erro.
        try:
            self.model = YOLO(model_path, task='detect')
            print("[PERCEPTION] Modelo carregado com sucesso!")
        except Exception as e:
            print(f"[ERRO] Falha ao carregar best.pt: {e}")
            self.model = None

        self.last_time = 0.0
        # Vamos testar mais lento (0.5s) para garantir processamento
        self.interval = 0.2
        self.last_detections = []

        # IMPORTANTE: Definimos os nomes manualmente caso o ONNX tenha perdido essa info
        # A ordem deve ser EXATAMENTE a do seu data.yaml
        self.class_names = {
            0: 'obstaculo',
            1: 'cubo_azul',
            2: 'cubo_vermelho',
            3: 'cubo_verde',
            4: 'caixa_azul',
            5: 'caixa_vermelha',
            6: 'caixa_verde'
        }

        # Variável para salvar apenas a primeira foto (diagnóstico)
        self.debug_image_saved = False

    def get_detections(self):
        # Se o modelo não carregou, retorna vazio
        if self.model is None:
            return None, []

        now = time.time()
        if now - self.last_time < self.interval:
            return None, self.last_detections

        self.last_time = now

        # 1. Pega imagem bruta do Webots
        raw = self.camera.getImage()
        if raw is None:
            print(
                "[ALERTA] Câmera retornou vazio (None). Verifique se enable() foi chamado.")
            return None, []

        w = self.camera.getWidth()
        h = self.camera.getHeight()

        # 2. Converte para formato OpenCV (BGR)
        # Webots: BGRA -> Removemos o Alpha -> BGR
        frame = np.frombuffer(raw, np.uint8).reshape((h, w, 4))
        frame = frame[:, :, :3]

        # 3. DEBUG: Salva a primeira imagem que o robô ver para você conferir
        if not self.debug_image_saved:
            cv2.imwrite("visao_robo_debug.jpg", frame)
            print("[DEBUG] Foto 'visao_robo_debug.jpg' salva na pasta do projeto.")
            print(
                "[DEBUG] Verifique se essa foto está com as cores certas e não está preta!")
            self.debug_image_saved = True

        # 4. Inferência
        # Baixamos a confiança para 0.1 (10%) para ver se ele detecta ALGO
        results = self.model(frame, conf=0.8, verbose=False)[0]

        detections = []

        # Verifica se achou alguma coisa
        if len(results.boxes) > 0:
            print(f"[DETECÇÃO] Encontrei {len(results.boxes)} objetos!")

        for box in results.boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            x1, y1, x2, y2 = map(int, box.xyxy[0])

            # Pega o nome da nossa lista manual ou do modelo se disponível
            if hasattr(self.model, 'names') and cls_id in self.model.names:
                label = self.model.names[cls_id]
            else:
                label = self.class_names.get(cls_id, f"Desconhecido_{cls_id}")

            print(f"   -> Objeto: {label} | Confiança: {conf:.2f}")

            detections.append({
                "label": label,
                "conf": conf,
                "bbox": (x1, y1, x2, y2),
                "center": ((x1 + x2) / 2, (y1 + y2) / 2),
                "size": (x2 - x1, y2 - y1)
            })

        self.last_detections = detections
        return frame, detections
