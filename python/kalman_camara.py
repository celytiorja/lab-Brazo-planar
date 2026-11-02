"""Kalman para los ángulos que mide la CÁMARA (teleoperación, opción 1).

Mismo filtro (kalman.py) y mismo modelo de proceso que el de las IMU
(velocidad casi constante, Δt_k real), pero ahora la medición es el ÁNGULO:

    x = [θ1, ω1, θ2, ω2]      z = [θ1_cam, θ2_cam]      H = | 1 0 0 0 |
                                                            | 0 0 1 0 |

Diferencias con el Kalman de los giroscopios:
  - La cámara mide θ directamente: NO hay deriva (θ es observable).
  - Llega a ~30 cuadros/s con Δt irregular: se usa el Δt real de cada cuadro.
  - Si en un cuadro no se ve un marcador, se hace SOLO la predicción: el filtro
    sigue estimando con su modelo en vez de congelarse.

Para integrar las IMU después (opción 2): se agregan las filas de los
giroscopios a H ([0 1 0 0] y [0 0 0 1]) y sus varianzas (Entrega 1) a R.
"""
import math

import numpy as np

import config_camara as CC
import modelo_kalman as M
from kalman import FiltroKalman

H_CAMARA = np.array([[1.0, 0.0, 0.0, 0.0],
                     [0.0, 0.0, 1.0, 0.0]])


def q_desde_f_n(f_n_hz, r):
    """q que da una frecuencia natural f_n al Kalman en régimen permanente."""
    return r * (2 * math.pi * f_n_hz) ** 4


class KalmanCamara:
    def __init__(self, theta0, r_camara, f_n_hz):
        self.r = np.atleast_1d(np.asarray(r_camara, float))
        if self.r.size == 1:
            self.r = np.repeat(self.r, 2)
        self.R = np.diag(self.r)
        self.f_n_hz = f_n_hz
        # Un q por articulación (cada una con su propio ruido de cámara).
        self.q = [q_desde_f_n(f_n_hz, ri) for ri in self.r]
        p0 = [CC.P0_DIAG["theta"], CC.P0_DIAG["omega"]] * 2
        self.kf = FiltroKalman([theta0[0], 0.0, theta0[1], 0.0], np.diag(p0))
        self.ultima_innovacion = None

    def _FQ(self, dt):
        F = np.zeros((4, 4))
        Q = np.zeros((4, 4))
        for i, q in enumerate(self.q):
            s = slice(2 * i, 2 * i + 2)
            F[s, s] = M._bloque_F(dt, False)
            Q[s, s] = M._bloque_Q(dt, q, False, 0.0)
        return F, Q

    def paso(self, dt, theta_medido=None):
        """Un cuadro. theta_medido = (θ1, θ2) o None si no se vio el brazo."""
        F, Q = self._FQ(dt)
        self.kf.predecir(F, Q)
        if theta_medido is not None:
            z = np.asarray(theta_medido, float)
            # El ángulo es circular: la innovación se lleva a (−180, 180].
            pred = H_CAMARA @ self.kf.x
            z = pred + (z - pred + 180) % 360 - 180
            d = self.kf.actualizar(z, H_CAMARA, self.R)
            self.ultima_innovacion = d["innovacion"]
        x = self.kf.x
        return np.array([x[0], x[2]]), np.array([x[1], x[3]])
