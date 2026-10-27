"""Los tres métodos que se comparan, con la MISMA interfaz:

    est = Metodo(phi0, bias, ...)
    phi, omega = est.paso(dt, w, phi_acc)     # una muestra a la vez

  - IntegracionDirecta:     φ_k = φ_{k−1} + Δt_k · (w_k − b)               (Euler)
  - MediaMovilIntegracion:  primero promedia las últimas N muestras de w, luego Euler
  - KalmanBrazo:            predicción + actualización (modelo_kalman.py)

Trabajan muestra a muestra (causales) porque así funcionan en tiempo real: el
MISMO código se usa en el análisis offline y en la teleoperación.
Condiciones comparables: misma φ0, mismo sesgo b, mismos Δt_k, mismas unidades.
"""
import time
from collections import deque

import numpy as np

import config_kalman as CK
import modelo_kalman as M
from kalman import FiltroKalman


class IntegracionDirecta:
    def __init__(self, phi0, bias):
        self.nombre = "Integración directa"
        self.phi = np.array(phi0, dtype=float)
        self.bias = np.array(bias, dtype=float)

    def paso(self, dt, w, phi_acc=None):
        w_c = np.asarray(w) - self.bias
        # Euler: se usa la velocidad de la muestra actual como constante en el intervalo.
        self.phi = self.phi + dt * w_c
        return self.phi.copy(), w_c


class MediaMovilIntegracion:
    def __init__(self, phi0, bias, ventana):
        self.nombre = f"Media móvil N={ventana} + Euler"
        self.ventana = ventana
        self.phi = np.array(phi0, dtype=float)
        self.bias = np.array(bias, dtype=float)
        self.buffer = deque(maxlen=ventana)

    def paso(self, dt, w, phi_acc=None):
        self.buffer.append(np.asarray(w) - self.bias)
        # Al arrancar hay menos de N muestras: se promedian las que haya (sin
        # rellenar con ceros, que sesgaría el inicio). Retraso ≈ (N−1)/2 muestras.
        w_f = np.mean(self.buffer, axis=0)
        self.phi = self.phi + dt * w_f
        return self.phi.copy(), w_f


class KalmanBrazo:
    def __init__(self, phi0, bias, R, q, usar_inclinacion=False, estimar_bias=False,
                 q_bias=CK.Q_BIAS, nombre=None, guardar_diagnostico=False):
        self.nombre = nombre or f"Kalman q={q:g}"
        self.q = q
        self.q_bias = q_bias
        self.usar_inclinacion = usar_inclinacion
        self.con_bias = estimar_bias
        self.bias = np.array(bias, dtype=float)
        self.H = M.matriz_H(self.con_bias, usar_inclinacion)
        self.R = np.atleast_2d(np.array(R, dtype=float))
        if self.R.shape != (self.H.shape[0], self.H.shape[0]):
            raise ValueError(f"R debe ser {self.H.shape[0]}x{self.H.shape[0]} y es {self.R.shape}")
        self.idx = M.indices(self.con_bias)

        x0, p0 = [], []
        for i in range(2):
            x0 += [phi0[i], 0.0] + ([bias[i]] if self.con_bias else [])
            p0 += [CK.P0_DIAG["phi"], CK.P0_DIAG["omega"]] + ([CK.P0_DIAG["bias"]] if self.con_bias else [])
        self.kf = FiltroKalman(x0, np.diag(p0))

        self.guardar = guardar_diagnostico
        self.diag = {"innovacion": [], "nis": [], "K": [], "P_diag": [], "asimetria": [],
                     "min_autovalor": []}

    def paso(self, dt, w, phi_acc=None):
        F, Q = M.matrices_FQ(dt, self.q, self.con_bias, self.q_bias)
        self.kf.predecir(F, Q)
        # Con sesgo en el estado se entrega el giro crudo; si no, ya corregido.
        z = np.asarray(w, dtype=float) if self.con_bias else np.asarray(w) - self.bias
        if self.usar_inclinacion:
            z = np.concatenate([z, phi_acc])
        d = self.kf.actualizar(z, self.H, self.R)
        if self.guardar:
            asim, min_ev = self.kf.chequeo_P()
            self.diag["innovacion"].append(d["innovacion"])
            self.diag["nis"].append(d["nis"])
            self.diag["K"].append(d["K"].copy())
            self.diag["P_diag"].append(np.diag(self.kf.P).copy())
            self.diag["asimetria"].append(asim)
            self.diag["min_autovalor"].append(min_ev)
        x = self.kf.x
        return x[self.idx["phi"]].copy(), x[self.idx["omega"]].copy()


def ejecutar(estimador, reg):
    """Recorre un Registro completo. Devuelve φ (n,2), ω (n,2) y el tiempo de
    cómputo de cada paso [µs]. La muestra 0 es la condición inicial."""
    n = reg.n
    phi = np.zeros((n, 2))
    omega = np.zeros((n, 2))
    t_calc = np.zeros(n)
    phi[0] = estimador.phi if hasattr(estimador, "phi") else estimador.kf.x[estimador.idx["phi"]]
    for k in range(1, n):
        acc = reg.phi_acc[k] if reg.phi_acc is not None else None
        t0 = time.perf_counter()
        phi[k], omega[k] = estimador.paso(reg.dt[k], reg.w[k], acc)
        t_calc[k] = (time.perf_counter() - t0) * 1e6
    return phi, omega, t_calc
