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
  - Si se ve solo PARTE del brazo (p. ej. la mano tapa la muñeca, pero hombro y codo se
    ven), se actualiza SOLO con lo que se ve: H se queda con la fila de θ1. θ1 sigue
    corregido por la cámara y θ2 lo predice el modelo. (Medición parcial = H parcial.)
  - Pero "velocidad constante" solo es creíble un rato: tu brazo frena. Si la oclusión
    dura más de PREDICCION_LIBRE_S, la velocidad estimada se va apagando (constante de
    tiempo FRENADO_TAU_S): el robot se detiene suavemente en vez de seguir de largo.

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
        self.t_sin_medir = np.zeros(2)          # por articulación

    def _FQ(self, dt):
        F = np.zeros((4, 4))
        Q = np.zeros((4, 4))
        for i, q in enumerate(self.q):
            s = slice(2 * i, 2 * i + 2)
            F[s, s] = M._bloque_F(dt, False)
            Q[s, s] = M._bloque_Q(dt, q, False, 0.0)
        return F, Q

    def paso(self, dt, theta_medido=None):
        """Un cuadro. theta_medido = (θ1, θ2), con NaN en lo que no se vio, o None."""
        F, Q = self._FQ(dt)
        self.kf.predecir(F, Q)
        z = np.full(2, np.nan) if theta_medido is None else np.asarray(theta_medido, float)
        visto = np.isfinite(z)
        # Oclusión larga de una articulación: su velocidad se va apagando.
        self.t_sin_medir = np.where(visto, 0.0, self.t_sin_medir + dt)
        frenar = math.exp(-dt / CC.FRENADO_TAU_S)
        for j in range(2):
            if self.t_sin_medir[j] > CC.PREDICCION_LIBRE_S:
                self.kf.x[2 * j + 1] *= frenar
        if visto.any():
            H = H_CAMARA[visto]                     # solo las filas de lo que se ve
            R = self.R[np.ix_(visto, visto)]
            pred = H @ self.kf.x
            # El ángulo es circular: la innovación se lleva a (−180, 180].
            zz = pred + (z[visto] - pred + 180) % 360 - 180
            d = self.kf.actualizar(zz, H, R)
            self.ultima_innovacion = d["innovacion"]
        x = self.kf.x
        return np.array([x[0], x[2]]), np.array([x[1], x[3]])
