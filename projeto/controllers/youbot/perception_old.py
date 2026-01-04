import cv2
import numpy as np
import time
from ultralytics import YOLO


class Perception:
    # Certifique-se que o arquivo está na pasta com este nome
    def __init__(self, camera, model_path="best.onnx"):
        self.camera = camera
        # Adicionei task='detect' para garantir que o ONNX carregue corretamente,
        # embora a biblioteca geralmente detecte sozinha.
        self.model = YOLO(model_path, task='detect')
        self.last_time = 0.0
        self.interval = 0.3
        self.last_detections = []

    def get_detections(self):
        now = time.time()

        if now - self.last_time < self.interval:
            return None, self.last_detections

        self.last_time = now

        w = self.camera.getWidth()
        h = self.camera.getHeight()
        raw = self.camera.getImage()

        if raw is None:
            return None, []

        # Processamento da imagem do Webots
        # Webots entrega BGRA (Blue, Green, Red, Alpha)
        frame = np.frombuffer(raw, np.uint8).reshape((h, w, 4))

        # Remove o canal Alpha -> Fica BGR
        frame = frame[:, :, :3]

        # --- ATENÇÃO AQUI ---
        # O YOLO v8 espera BGR. Como o Webots já entregou BGR acima,
        # a conversão abaixo pode INVERTER as cores (Vermelho vira Azul).
        # Teste: Se o robô confundir as cores, REMOVA a linha abaixo.
        # frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        # --------------------

        # Inference
        # verbose=False limpa o console
        results = self.model(frame, conf=0.40, verbose=False)[0]

        detections = []
        # O results.names carrega automaticamente as classes do seu treino
        # (cubo verde, cubo azul, etc)
        class_names = results.names

        for box in results.boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            x1, y1, x2, y2 = map(int, box.xyxy[0])

            label = class_names[cls]

            detections.append({
                "label": label,
                "conf": conf,
                "bbox": (x1, y1, x2, y2),
                "center": ((x1 + x2) / 2, (y1 + y2) / 2),
                "size": (x2 - x1, y2 - y1)
            })

        self.last_detections = detections
        return frame, detections
