from controller import Robot
from base import Base
from arm import Arm
from gripper import Gripper
import math


def detect_obstacles_from_lidar(lidar,
                                min_range=0.05,
                                max_range=5.0,
                                min_cluster_size=3):
    """Detecta obstáculos simples a partir do Lidar do Webots.

    Retorna uma lista de dicionários com chaves: 'x','y','distance','angle','radius','size'.
    Coordenadas no referencial do robô: x = frente, y = esquerda (metros).
    """
    try:
        ranges = lidar.getRangeImage()
    except Exception:
        return []

    if ranges is None:
        return []

    n = len(ranges)
    # tenta ler FOV e resolução; usa fallback se não existir
    try:
        fov = lidar.getFov()  # em rad
    except Exception:
        fov = math.radians(180)

    try:
        res = lidar.getHorizontalResolution()
    except Exception:
        res = n if n > 0 else 1

    # ângulo do feixe i: começa em -fov/2 até +fov/2
    angles = [(-fov / 2.0) + (i * (fov / res)) for i in range(n)]

    # máscara de leituras válidas
    valid = []
    for r in ranges:
        if r is None or math.isinf(r) or math.isnan(r):
            valid.append(False)
        else:
            valid.append((r >= min_range) and (r <= max_range))

    clusters = []
    i = 0
    while i < n:
        if not valid[i]:
            i += 1
            continue

        # inicia cluster
        j = i
        acc = []
        while j < n and valid[j]:
            acc.append((angles[j], ranges[j]))
            j += 1

        # se cluster grande o suficiente, computa centro aproximado
        if len(acc) >= min_cluster_size:
            mean_r = sum(r for a, r in acc) / len(acc)
            mean_a = sum(a for a, r in acc) / len(acc)

            x = mean_r * math.cos(mean_a)
            y = mean_r * math.sin(mean_a)

            a0, r0 = acc[0]
            a1, r1 = acc[-1]
            x0, y0 = r0 * math.cos(a0), r0 * math.sin(a0)
            x1, y1 = r1 * math.cos(a1), r1 * math.sin(a1)
            width = math.hypot(x1 - x0, y1 - y0)
            radius = max(width / 2.0, 0.03)

            clusters.append({
                'x': x,
                'y': y,
                'distance': mean_r,
                'angle': mean_a,
                'radius': radius,
                'size': len(acc)
            })

        i = j

    return clusters


class YouBotController:
    def __init__(self):
        self.robot = Robot()
        self.time_step = int(self.robot.getBasicTimeStep())

        self.base = Base(self.robot)
        self.arm = Arm(self.robot)
        self.gripper = Gripper(self.robot)

        self.camera = self.robot.getDevice("camera")
        self.camera.enable(self.time_step)

        self.lidar = self.robot.getDevice("lidar")
        self.lidar.enable(self.time_step)
        # inicialização pronta; lógica de movimento ficará em run()

    def run(self):
        """Loop principal: anda em linha reta e para caso o LIDAR detecte obstáculo a <= 0.5 m.

        Lógica:
        - a cada passo lê o LIDAR e agrupa clusters simples
        - se houver um cluster com ângulo dentro de +/-20° e distância <= 0.5, para a base
        - caso contrário, mantém a base andando para frente
        """
        print("YouBotController: iniciando controle com LIDAR")

        while self.robot.step(self.time_step) != -1:
            obstacles = detect_obstacles_from_lidar(
                self.lidar, min_range=0.05, max_range=3.0)

            # imprime obstáculos detectados (útil para debug)
            for obs in obstacles:
                print(
                    f"obstáculo a {obs['distance']:.2f}m, ângulo {math.degrees(obs['angle']):.1f}°, pos ({obs['x']:.2f},{obs['y']:.2f}), raio {obs['radius']:.2f}")

            # verifica se existe obstáculo frontal próximo
            stop = False
            for obs in obstacles:
                if abs(obs['angle']) < math.radians(20) and obs['distance'] <= 0.5:
                    stop = True
                    break

            if stop:
                # para a base imediatamente
                self.base.reset()
            else:
                # anda em linha reta
                self.base.forwards()

        print("YouBotController: simulador finalizado ou parada solicitada")


if __name__ == "__main__":
    controller = YouBotController()
    controller.run()
