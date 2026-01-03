from ultralytics import YOLO
import sys
import pathlib
import cv2
import numpy as np
import traceback

# --- CORREÇÃO DE COMPATIBILIDADE ---
sys.modules['pathlib._local'] = pathlib
pathlib.PosixPath = pathlib.WindowsPath
# -----------------------------------


class PerceptionSystem:
    def __init__(self, lidar, camera):
        self.lidar = lidar
        self.camera = camera
        self.img_width = camera.getWidth()
        self.img_height = camera.getHeight()

        # --- CARREGAMENTO DA YOLO ---
        try:
            self.model = YOLO('best.pt')
            self.conf_threshold = 0.5
            print("Modelo YOLO carregado com sucesso!")
        except Exception as e:
            print(f"ERRO CRÍTICO: Não foi possível carregar YOLO: {e}")
            self.model = None

    def _webots_to_cv2(self):
        """Converte imagem do Webots para OpenCV"""
        try:
            raw_image = self.camera.getImage()
            if raw_image is None:
                return None

            img_np = np.frombuffer(raw_image, np.uint8).reshape(
                (self.img_height, self.img_width, 4))
            img_bgr = img_np[:, :, :3]
            return img_bgr
        except Exception as e:
            print(f"Erro na conversão de imagem: {e}")
            return None

    def get_fuzzy_dist(self):
        """Lê LiDAR e normaliza para [0, 1]"""
        try:
            raw_data = self.lidar.getRangeImage()
            if not raw_data:
                return 1.0, 2.0

            center = len(raw_data) // 2
            scan = raw_data[center-20: center+20]

            # Filtra chão/ruído (< 0.15m) e infinito
            valid_scan = [d for d in scan if (d != float('inf') and d > 0.15)]
            min_dist = min(valid_scan) if valid_scan else 2.0

            return min(max((min_dist - 0.2) / 1.0, 0.0), 1.0), min_dist
        except:
            return 1.0, 2.0

    def detect_target(self, target_type, target_color=None):
        """
        Retorna SEMPRE uma tupla: (bool, float, str/None)
        """
        # Valor de retorno padrão em caso de falha
        default_return = (False, 0.0, None)

        if self.model is None:
            return default_return

        try:
            # 1. Obter imagem
            frame = self._webots_to_cv2()
            if frame is None:
                return default_return

            # 2. Inferência YOLO
            results = self.model(frame, verbose=False,
                                 conf=self.conf_threshold)

            best_target = None
            min_center_dist = float('inf')

            # 3. Processamento
            for result in results:
                for box in result.boxes:
                    cls_id = int(box.cls[0])
                    class_name = self.model.names[cls_id]

                    # Filtros de Tipo
                    target_ok = False
                    if target_type in ['cubo', 'cube'] and ('cube' in class_name or 'cubo' in class_name):
                        target_ok = True
                    elif target_type in ['caixa', 'box'] and ('box' in class_name or 'caixa' in class_name):
                        target_ok = True

                    if not target_ok:
                        continue

                    # Filtros de Cor
                    detected_color = None
                    if 'red' in class_name:
                        detected_color = 'red'
                    elif 'green' in class_name:
                        detected_color = 'green'
                    elif 'blue' in class_name:
                        detected_color = 'blue'

                    if target_color and target_color != detected_color:
                        continue

                    # Seleção do Melhor Alvo (Mais centralizado)
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    center_x = (x1 + x2) / 2
                    dist_to_center = abs(center_x - (self.img_width / 2))

                    if dist_to_center < min_center_dist:
                        min_center_dist = dist_to_center

                        # Cálculo do Erro
                        raw_error = (center_x - (self.img_width / 2)
                                     ) / (self.img_width / 2)
                        amplified_error = raw_error * 1.3
                        final_error = max(-1.6, min(1.6, amplified_error))

                        best_target = (True, final_error, detected_color)

            # Se encontrou algo, retorna. Se não, retorna padrão.
            if best_target:
                return best_target

            return default_return

        except Exception as e:
            # Em caso de qualquer erro interno (ex: reshape falhou), não quebra o robô
            print(f"DEBUG: Erro protegido no detect_target: {e}")
            traceback.print_exc()  # Imprime o erro real no console para debug
            return default_return
