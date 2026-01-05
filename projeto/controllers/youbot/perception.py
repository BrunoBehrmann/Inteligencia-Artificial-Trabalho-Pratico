import numpy as np
import time
from ultralytics import YOLO


class Perception:
    def __init__(self, camera, lidar=None, model_path="best.pt"):
        self.camera = camera
        self.lidar = lidar

        print(f"[PERCEPTION] Carregando modelo {model_path}")
        try:
            self.model = YOLO(model_path)
            print("[PERCEPTION] Modelo carregado.")
        except Exception as e:
            print(f"[ERRO] {e}")
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

    def get_lidar_dist(self):
        if not self.lidar:
            return 2.0

        scan = self.lidar.getRangeImage()
        if not scan:
            return 2.0

        center = len(scan) // 2
        window = scan[center - 10:center + 10]
        valid = [r for r in window if 0.05 < r < 3.0]

        return sum(valid) / len(valid) if valid else 2.0

    def get_detections(self):
        if self.model is None:
            return None, []

        now = time.time()
        if now - self.last_time < self.interval:
            return None, self.last_detections

        self.last_time = now

        raw = self.camera.getImage()
        if raw is None:
            return None, []

        w, h = self.camera.getWidth(), self.camera.getHeight()
        frame = np.frombuffer(raw, np.uint8).reshape((h, w, 4))[:, :, :3]

        results = self.model(frame, conf=0.6, verbose=False)[0]

        detections = []
        for box in results.boxes:
            cls_id = int(box.cls[0])
            label = self.model.names.get(cls_id, self.class_names.get(cls_id))
            x1, y1, x2, y2 = map(int, box.xyxy[0])

            detections.append({
                "label": label,
                "conf": float(box.conf[0]),
                "bbox": (x1, y1, x2, y2),
            })

        self.last_detections = detections
        return frame, detections
