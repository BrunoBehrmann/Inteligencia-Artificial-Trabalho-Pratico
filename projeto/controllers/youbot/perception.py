import cv2
import numpy as np
import time
from ultralytics import YOLO


class Perception:
    def __init__(self, camera, model_path="yolov8n.pt"):
        self.camera = camera
        self.model = YOLO(model_path)
        self.last_time = 0.0
        self.interval = 0.3  # segundos entre inferências (reduz peso)
        self.last_detections = []

    def get_detections(self):
        now = time.time()

        # Só roda YOLO a cada "interval" segundos
        if now - self.last_time < self.interval:
            return None, self.last_detections

        self.last_time = now

        w = self.camera.getWidth()
        h = self.camera.getHeight()
        raw = self.camera.getImage()

        if raw is None:
            return None, []

        frame = np.frombuffer(raw, np.uint8).reshape((h, w, 4))
        frame = frame[:, :, :3]  # remove alpha
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        results = self.model(frame, conf=0.25, verbose=False)[0]

        detections = []
        for box in results.boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            label = self.model.names[cls]

            detections.append({
                "label": label,
                "conf": conf,
                "bbox": (x1, y1, x2, y2),
                "center": ((x1 + x2) / 2, (y1 + y2) / 2),
                "size": (x2 - x1, y2 - y1)
            })

        self.last_detections = detections
        return frame, detections
