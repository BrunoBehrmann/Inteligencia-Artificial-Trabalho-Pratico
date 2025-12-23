import numpy as np

# =========================================================
# PARÂMETROS DO VFH (LIDAR FRONTAL)
# =========================================================
MAX_RANGE = 4.0
SECTOR_DEG = 5
FOV_DEG = 180                      # LiDAR frontal (π rad)
NUM_SECTORS = FOV_DEG // SECTOR_DEG
HIST_THRESHOLD = 0.25


def compute_vfh_direction(range_image):
    """
    VFH simplificado para LiDAR FRONTAL (180°)

    Retorno:
        None  -> nenhum caminho livre
        angle -> ângulo em graus (-90 a +90)
                 0 = frente
                 >0 = esquerda
                 <0 = direita
    """

    histogram = np.zeros(NUM_SECTORS)

    num_readings = len(range_image)

    # Usa apenas a região frontal do LiDAR
    start = num_readings // 4
    end = 3 * num_readings // 4
    frontal_ranges = range_image[start:end]

    # -------------------------
    # Construção do histograma
    # -------------------------
    for i, dist in enumerate(frontal_ranges):
        if dist >= MAX_RANGE:
            continue

        angle_deg = (i / len(frontal_ranges)) * FOV_DEG - 90
        sector = int((angle_deg + 90) // SECTOR_DEG)

        weight = (MAX_RANGE - dist) / MAX_RANGE
        histogram[sector] += weight

    # -------------------------
    # Suavização
    # -------------------------
    smooth = np.copy(histogram)
    for i in range(NUM_SECTORS):
        left = histogram[i - 1] if i > 0 else histogram[i]
        right = histogram[i + 1] if i < NUM_SECTORS - 1 else histogram[i]
        smooth[i] = (left + histogram[i] + right) / 3.0

    # -------------------------
    # Binarização
    # -------------------------
    free = smooth < HIST_THRESHOLD

    # -------------------------
    # Detecção de vales
    # -------------------------
    valleys = []
    start_idx = None

    for i in range(NUM_SECTORS):
        if free[i]:
            if start_idx is None:
                start_idx = i
        else:
            if start_idx is not None:
                valleys.append((start_idx, i - 1))
                start_idx = None

    if start_idx is not None:
        valleys.append((start_idx, NUM_SECTORS - 1))

    if not valleys:
        return None

    # -------------------------
    # Escolher vale mais frontal
    # -------------------------
    best_angle = None
    min_error = float("inf")

    for start, end in valleys:
        center = (start + end) // 2
        angle = center * SECTOR_DEG - 90
        error = abs(angle)

        if error < min_error:
            min_error = error
            best_angle = angle

    return best_angle
