"""Modelo en espacio de estados del brazo 2 GDL para el filtro de Kalman.

ESTADO (por eslabón i = 1, 2), en ángulos ABSOLUTOS del eslabón:
    φ_i  ángulo [°]          ω_i  velocidad angular [°/s]      (b_i sesgo del giro [°/s], opcional)

    x = [φ1, ω1, (b1), φ2, ω2, (b2)]ᵀ

¿Por qué ángulos absolutos y no θ1, θ2? Porque cada IMU mide el giro de SU
eslabón respecto al mundo: IMU1 ve ω1 = θ̇1 e IMU2 ve ω2 = θ̇1 + θ̇2. Con estado
absoluto, H es simple y el acoplamiento articular aparece solo al final:
θ1 = φ1, θ2 = φ2 − φ1.

MODELO DE PROCESO: velocidad casi constante ("white-noise acceleration").
Entre dos muestras separadas Δt_k:
    φ_k = φ_{k−1} + Δt_k · ω_{k−1}          (cinemática discreta: Euler exacto si ω es constante)
    ω_k = ω_{k−1} + (aceleración desconocida)
    b_k = b_{k−1} + (paseo aleatorio muy lento)
La aceleración angular desconocida es el RUIDO DE PROCESO, de densidad q
[(°/s²)²/Hz = °²/s³]. Integrándola exactamente sobre Δt_k se obtiene:
    Q_bloque = q · | Δt³/3  Δt²/2 |
                   | Δt²/2  Δt    |
Cada paso usa su Δt_k REAL (de los timestamps del ESP32), no el nominal.

MEDICIONES:
    giroscopio:   z = ω_i (+ b_i si se estima el sesgo) + ruido        -> fila de H con 1 en ω (y en b)
    inclinación:  z = φ_i + ruido   (solo si el brazo está en un plano vertical)
"""
import numpy as np


def _bloque_F(dt, con_bias):
    if con_bias:
        return np.array([[1.0, dt, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
    return np.array([[1.0, dt], [0.0, 1.0]])


def _bloque_Q(dt, q, con_bias, q_bias):
    Qb = q * np.array([[dt**3 / 3, dt**2 / 2], [dt**2 / 2, dt]])
    if con_bias:
        Qb = np.pad(Qb, ((0, 1), (0, 1)))
        Qb[2, 2] = q_bias * dt
    return Qb


def _diag_bloques(A, B):
    n, m = A.shape[0], B.shape[0]
    M = np.zeros((n + m, n + m))
    M[:n, :n] = A
    M[n:, n:] = B
    return M


def matrices_FQ(dt, q, con_bias=False, q_bias=0.0):
    """F y Q del brazo completo (dos eslabones independientes en dinámica)."""
    F = _diag_bloques(_bloque_F(dt, con_bias), _bloque_F(dt, con_bias))
    Q = _diag_bloques(_bloque_Q(dt, q, con_bias, q_bias), _bloque_Q(dt, q, con_bias, q_bias))
    return F, Q


def matriz_H(con_bias=False, usar_inclinacion=False):
    """Filas: [giro1, giro2] y, si hay plano vertical, [inclinación1, inclinación2]."""
    n = 3 if con_bias else 2
    filas = []
    for i in range(2):                       # giroscopios
        f = np.zeros(2 * n)
        f[i * n + 1] = 1.0                   # ω_i
        if con_bias:
            f[i * n + 2] = 1.0               # + b_i
        filas.append(f)
    if usar_inclinacion:
        for i in range(2):
            f = np.zeros(2 * n)
            f[i * n] = 1.0                   # φ_i
            filas.append(f)
    return np.array(filas)


def indices(con_bias=False):
    """Posiciones de φ, ω y b de cada eslabón dentro del vector de estado."""
    n = 3 if con_bias else 2
    return {"phi": [0, n], "omega": [1, n + 1], "bias": [2, n + 2] if con_bias else None}
