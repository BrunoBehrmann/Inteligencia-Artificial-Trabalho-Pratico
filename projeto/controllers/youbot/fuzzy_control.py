import numpy as np


class FuzzyControl:
    def __init__(self):

        self.e_max = 320.0
        self.d_max = 1.5

    def tri(self, x, a, b, c):
        if x <= a or x >= c:
            return 0.0
        elif x == b:
            return 1.0
        elif x < b:
            return (x - a) / ((b - a) + 1e-6)
        else:
            return (c - x) / ((c - b) + 1e-6)

    def fuzzify_error(self, e):

        return {
            "NB": self.tri(e, -self.e_max, -self.e_max, -100),
            "NS": self.tri(e, -150, -80, 0),
            "Z":  self.tri(e, -50, 0, 50),
            "PS": self.tri(e, 0, 80, 150),
            "PB": self.tri(e, 100, self.e_max, self.e_max),
        }

    def fuzzify_dist(self, d):
        return {
            "MP": self.tri(d, 0.0, 0.0, 0.2),
            "P":  self.tri(d, 0.1, 0.3, 0.6),
            "M":  self.tri(d, 0.4, 0.8, 1.2),
            "L":  self.tri(d, 1.0, self.d_max, self.d_max),
        }

    def rules(self, mu_e, mu_d):

        virando = max(mu_e["NB"], mu_e["PB"])
        alinhado = mu_e["Z"]

        v_rules = {
            "Z": mu_d["MP"],

            "S": max(mu_d["P"], virando),

            "M": min(mu_d["M"], alinhado),

            "F": min(mu_d["L"], alinhado),
        }

        w_rules = {
            "LB": mu_e["PB"],
            "LS": mu_e["PS"],
            "Z":  mu_e["Z"],
            "RS": mu_e["NS"],
            "RB": mu_e["NB"],
        }

        return v_rules, w_rules

    def fuzzify_v(self, v):
        return {
            "Z": self.tri(v, 0.0, 0.0, 0.1),
            "S": self.tri(v, 0.05, 0.3, 0.5),
            "M": self.tri(v, 0.4, 0.7, 0.9),
            "F": self.tri(v, 0.8, 1.0, 1.0),
        }

    def fuzzify_w(self, w):
        return {
            "LB": self.tri(w, -1.0, -1.0, -0.5),
            "LS": self.tri(w, -0.6, -0.3, 0.0),
            "Z":  self.tri(w, -0.1, 0.0, 0.1),
            "RS": self.tri(w, 0.0, 0.3, 0.6),
            "RB": self.tri(w, 0.5, 1.0, 1.0),
        }

    def defuzzify_v(self, mu_out):
        xs = np.linspace(0.0, 1.0, 50)
        num, den = 0.0, 0.0
        for x in xs:
            mu_sets = self.fuzzify_v(x)

            mu = max(
                min(mu_out["Z"], mu_sets["Z"]),
                min(mu_out["S"], mu_sets["S"]),
                min(mu_out["M"], mu_sets["M"]),
                min(mu_out["F"], mu_sets["F"]),
            )
            num += x * mu
            den += mu
        return num / den if den > 0 else 0.0

    def defuzzify_w(self, mu_out):
        xs = np.linspace(-1.0, 1.0, 50)
        num, den = 0.0, 0.0
        for x in xs:
            mu_sets = self.fuzzify_w(x)
            mu = max(
                min(mu_out["LB"], mu_sets["LB"]),
                min(mu_out["LS"], mu_sets["LS"]),
                min(mu_out["Z"],  mu_sets["Z"]),
                min(mu_out["RS"], mu_sets["RS"]),
                min(mu_out["RB"], mu_sets["RB"]),
            )
            num += x * mu
            den += mu
        return num / den if den > 0 else 0.0

    def compute(self, erro_px, dist):
        mu_e = self.fuzzify_error(erro_px)
        mu_d = self.fuzzify_dist(dist)
        mu_v, mu_w = self.rules(mu_e, mu_d)
        v = self.defuzzify_v(mu_v)
        w = self.defuzzify_w(mu_w)
        return v, w
