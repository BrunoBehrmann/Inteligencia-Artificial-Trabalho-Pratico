import cv2
import numpy as np
import time
from ultralytics import YOLO


class Perception:
    def __init__(self, camera, model_path="best.pt"):
        self.camera = camera
        print(f"[PERCEPTION] Carregando modelo de: {model_path}")

        try:
            self.model = YOLO(model_path, task='detect')
            print("[PERCEPTION] Modelo carregado com sucesso!")
        except Exception as e:
            print(f"[ERRO] Falha ao carregar best.pt: {e}")
            self.model = None

        self.last_time = 0.0

        self.interval = 0.2
        self.last_detections = []

        self.class_names = {
            0: 'obstaculo',
            1: 'cubo_azul',
            2: 'cubo_vermelho',
            3: 'cubo_verde',
            4: 'caixa_azul',
            5: 'caixa_vermelha',
            6: 'caixa_verde'
        }

        self.debug_image_saved = False

    def get_detections(self):

        if self.model is None:
            return None, []

        now = time.time()
        if now - self.last_time < self.interval:
            return None, self.last_detections

        self.last_time = now

        raw = self.camera.getImage()
        if raw is None:
            print(
                "[ALERTA] Câmera retornou vazio (None). Verifique se enable() foi chamado.")
            return None, []

        w = self.camera.getWidth()
        h = self.camera.getHeight()

        frame = np.frombuffer(raw, np.uint8).reshape((h, w, 4))
        frame = frame[:, :, :3]

        if not self.debug_image_saved:
            cv2.imwrite("visao_robo_debug.jpg", frame)
            print("[DEBUG] Foto 'visao_robo_debug.jpg' salva na pasta do projeto.")
            print(
                "[DEBUG] Verifique se essa foto está com as cores certas e não está preta!")
            self.debug_image_saved = True

        results = self.model(frame, conf=0.7, verbose=False)[0]

        detections = []

        for box in results.boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            x1, y1, x2, y2 = map(int, box.xyxy[0])

            if hasattr(self.model, 'names') and cls_id in self.model.names:
                label = self.model.names[cls_id]
            else:
                label = self.class_names.get(cls_id, f"Desconhecido_{cls_id}")

            detections.append({
                "label": label,
                "conf": conf,
                "bbox": (x1, y1, x2, y2),
                "center": ((x1 + x2) / 2, (y1 + y2) / 2),
                "size": (x2 - x1, y2 - y1)
            })

        self.last_detections = detections
        return frame, detections
