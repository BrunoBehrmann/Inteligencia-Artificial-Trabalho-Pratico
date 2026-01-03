import numpy as np


class FuzzyController:
    def __init__(self):
        # --- DEFINIÇÃO DOS UNIVERSOS ---
        # Resolução para o cálculo do centroide (quanto maior, mais preciso e mais lento)
        self.res = 100

        # Ranges das saídas (Consequentes)
        self.v_range = np.linspace(0, 0.6, self.res)      # Velocidade Linear
        self.w_range = np.linspace(-1.5, 1.5, self.res)   # Velocidade Angular

    # --- FUNÇÕES DE PERTINÊNCIA (Shapes) ---
    def trimf(self, x, abc):
        """Triangular membership function"""
        a, b, c = abc
        return np.maximum(0, np.minimum((x - a) / (b - a + 1e-9), (c - x) / (c - b + 1e-9)))

    def trapmf(self, x, abcd):
        """Trapezoidal membership function"""
        a, b, c, d = abcd
        return np.maximum(0, np.minimum(np.minimum((x - a) / (b - a + 1e-9), 1), (d - x) / (d - c + 1e-9)))

    def compute(self, direcao_val, risco_val):
        """
        Entradas: 
            direcao_val: radianos [-1.6 a 1.6]
            risco_val:   normalizado [0 a 1]
        Saídas:
            v (linear), w (angular)
        """

        # --- 1. FUZZIFICAÇÃO (Calcula o grau de cada termo) ---

        # Risco [0..1]
        risco_baixo = self.trapmf(risco_val, [0, 0, 0.2, 0.45])
        risco_medio = self.trimf(risco_val,  [0.3, 0.5, 0.7])
        risco_alto = self.trapmf(risco_val, [0.55, 0.8, 1.0, 1.0])

        # Direção [-1.6..1.6]
        # Ajustei levemente os ranges para cobrir buracos
        dir_esq = self.trimf(direcao_val, [-2.0, -1.6, -0.3])
        dir_centro = self.trimf(direcao_val, [-0.6, 0.0, 0.6])
        dir_dir = self.trimf(direcao_val, [0.3, 1.6, 2.0])

        # --- 2. INFERÊNCIA (Aplicar Regras) ---
        # O "grau de ativação" da regra é o MÍNIMO entre as entradas (E lógico)

        # R1: Risco Baixo + Esq -> V Alta, W Esq Suave
        r1 = min(risco_baixo, dir_esq)
        # R2: Risco Baixo + Centro -> V Alta, W Zero
        r2 = min(risco_baixo, dir_centro)
        # R3: Risco Baixo + Dir -> V Alta, W Dir Suave
        r3 = min(risco_baixo, dir_dir)

        # R4: Risco Medio + Esq -> V Media, W Esq Medio
        r4 = min(risco_medio, dir_esq)
        # R5: Risco Medio + Centro -> V Media, W Zero
        r5 = min(risco_medio, dir_centro)
        # R6: Risco Medio + Dir -> V Media, W Dir Medio
        r6 = min(risco_medio, dir_dir)

        # R7: Risco Alto + Esq -> V Baixa, W Esq Brusco
        r7 = min(risco_alto, dir_esq)
        # R8: Risco Alto + Centro -> V Baixa, W Zero
        r8 = min(risco_alto, dir_centro)
        # R9: Risco Alto + Dir -> V Baixa, W Dir Brusco
        r9 = min(risco_alto, dir_dir)

        # --- 3. AGREGAÇÃO E DEFUZZIFICAÇÃO (V - Linear) ---
        # Define os shapes de saída para V
        v_baixa_shape = self.trapmf(self.v_range, [0, 0, 0.1, 0.25])
        v_media_shape = self.trimf(self.v_range,  [0.15, 0.35, 0.55])
        v_alta_shape = self.trapmf(self.v_range, [0.45, 0.55, 0.6, 0.6])

        # Corta os shapes pelo grau de ativação (Corte Mamdani)
        # Regras que ativam Baixa: R7, R8, R9
        out_v_baixa = np.minimum(max(r7, r8, r9), v_baixa_shape)
        # Regras que ativam Media: R4, R5, R6
        out_v_media = np.minimum(max(r4, r5, r6), v_media_shape)
        # Regras que ativam Alta: R1, R2, R3
        out_v_alta = np.minimum(max(r1, r2, r3), v_alta_shape)

        # Une tudo (Máximo da agregação)
        agg_v = np.maximum(out_v_baixa, np.maximum(out_v_media, out_v_alta))

        # Centroide V
        denom_v = np.sum(agg_v)
        if denom_v == 0:
            final_v = 0.0
        else:
            final_v = np.sum(agg_v * self.v_range) / denom_v

        # --- 4. AGREGAÇÃO E DEFUZZIFICAÇÃO (W - Angular) ---
        # Define os shapes de saída para W
        w_esq_brusco = self.trapmf(self.w_range, [-1.5, -1.5, -1.1, -0.8])
        w_esq_medio = self.trimf(self.w_range,  [-1.0, -0.7, -0.4])
        w_esq_suave = self.trimf(self.w_range,  [-0.6, -0.3, 0.1])
        w_zero = self.trimf(self.w_range,  [-0.2, 0.0, 0.2])
        w_dir_suave = self.trimf(self.w_range,  [-0.1, 0.3, 0.6])
        w_dir_medio = self.trimf(self.w_range,  [0.4, 0.7, 1.0])
        w_dir_brusco = self.trapmf(self.w_range, [0.8, 1.1, 1.5, 1.5])

        # Corta e Agrega
        out_w_eb = np.minimum(r7, w_esq_brusco)
        out_w_em = np.minimum(r4, w_esq_medio)
        out_w_es = np.minimum(r1, w_esq_suave)
        out_w_ze = np.minimum(max(r2, r5, r8), w_zero)
        out_w_ds = np.minimum(r3, w_dir_suave)
        out_w_dm = np.minimum(r6, w_dir_medio)
        out_w_db = np.minimum(r9, w_dir_brusco)

        agg_w = np.maximum.reduce(
            [out_w_eb, out_w_em, out_w_es, out_w_ze, out_w_ds, out_w_dm, out_w_db])

        # Centroide W
        denom_w = np.sum(agg_w)
        if denom_w == 0:
            final_w = 0.0
        else:
            final_w = np.sum(agg_w * self.w_range) / denom_w

        return final_v, final_w
