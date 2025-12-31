import numpy as np
import skfuzzy as fuzzy
from skfuzzy import control as ctrl

# Variável global
simulador = None


def setup_fuzzy():
    global simulador

    # --- 1. Antecedentes (Entradas) ---
    # Risco: Mantém 0 a 1 (normalizado via cálculo do inverso da distância)
    risco = ctrl.Antecedent(np.arange(0, 1.01, 0.01), 'risco')

    # Direção: AGORA EM RADIANOS [-1.6 a 1.6] (aprox -90 a +90 graus)
    direcao = ctrl.Antecedent(np.arange(-1.6, 1.61, 0.01), 'direcao')

    # --- 2. Consequentes (Saídas) ---
    # Saídas mantidas iguais (o robô reage com as mesmas velocidades)
    v = ctrl.Consequent(np.arange(0, 0.61, 0.01), 'v')
    w = ctrl.Consequent(np.arange(-1.5, 1.51, 0.01), 'w')

    # --- 3. Pertinência: Risco (Mantido) ---
    risco['baixo'] = fuzzy.trapmf(risco.universe, [0, 0, 0.2, 0.45])
    risco['medio'] = fuzzy.trimf(risco.universe, [0.3, 0.5, 0.7])
    risco['alto'] = fuzzy.trapmf(risco.universe, [0.55, 0.8, 1, 1])

    # --- 4. Pertinência: Direção (ADAPTADO AO LIDAR) ---
    # Esquerda: valores negativos (ex: -1.57 rad)
    direcao['esquerda'] = fuzzy.trimf(direcao.universe, [-2.0, -1.6, -0.3])
    # Centro: faixa segura ao redor do zero
    direcao['centro'] = fuzzy.trimf(direcao.universe, [-0.6, 0, 0.6])
    # Direita: valores positivos (ex: 1.57 rad)
    direcao['direita'] = fuzzy.trimf(direcao.universe, [0.3, 1.6, 2.0])

    # --- 5. Pertinência: Saídas (Mantidas) ---
    w['esq_brusco'] = fuzzy.trapmf(w.universe, [-1.5, -1.5, -1.1, -0.8])
    w['esq_medio'] = fuzzy.trimf(w.universe, [-1.0, -0.7, -0.4])
    w['esq_suave'] = fuzzy.trimf(w.universe, [-0.6, -0.3, 0.1])
    w['zero'] = fuzzy.trimf(w.universe, [-0.2, 0, 0.2])
    w['dir_suave'] = fuzzy.trimf(w.universe, [-0.1, 0.3, 0.6])
    w['dir_medio'] = fuzzy.trimf(w.universe, [0.4, 0.7, 1.0])
    w['dir_brusco'] = fuzzy.trapmf(w.universe, [0.8, 1.1, 1.5, 1.5])

    v['baixa'] = fuzzy.trapmf(v.universe, [0, 0, 0.1, 0.25])
    v['media'] = fuzzy.trimf(v.universe, [0.15, 0.35, 0.55])
    v['alta'] = fuzzy.trapmf(v.universe, [0.45, 0.55, 0.6, 0.6])

    # --- 6. Regras (Lógica Mantida) ---
    regras = [
        ctrl.Rule(risco['baixo'] & direcao['esquerda'],
                  (v['alta'], w['esq_suave'])),
        ctrl.Rule(risco['baixo'] & direcao['centro'],
                  (v['alta'], w['zero'])),
        ctrl.Rule(risco['baixo'] & direcao['direita'],
                  (v['alta'], w['dir_suave'])),

        ctrl.Rule(risco['medio'] & direcao['esquerda'],
                  (v['media'], w['esq_medio'])),
        ctrl.Rule(risco['medio'] & direcao['centro'],
                  (v['media'], w['zero'])),
        ctrl.Rule(risco['medio'] & direcao['direita'],
                  (v['media'], w['dir_medio'])),

        ctrl.Rule(risco['alto'] & direcao['esquerda'],
                  (v['baixa'], w['esq_brusco'])),
        ctrl.Rule(risco['alto'] & direcao['centro'],
                  (v['baixa'], w['zero'])),
        ctrl.Rule(risco['alto'] & direcao['direita'],
                  (v['baixa'], w['dir_brusco']))
    ]

    simulador = ctrl.ControlSystemSimulation(ctrl.ControlSystem(regras))


setup_fuzzy()


def compute(direcao_val, risco_val):
    global simulador
    try:
        # Passamos o valor em RADIANOS diretamente
        simulador.input['direcao'] = direcao_val
        simulador.input['risco'] = risco_val
        simulador.compute()
        return simulador.output.get('v', 0.0), simulador.output.get('w', 0.0)
    except Exception as e:
        # Se o valor sair muito do range (ex: 3.14), retornamos 0 para segurança
        # print(f"[Fuzzy Warning] Input fora do range: {direcao_val}")
        return 0.0, 0.0
