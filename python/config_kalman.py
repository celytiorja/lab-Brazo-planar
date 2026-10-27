"""Parámetros del filtro de Kalman y de la comparación (Entrega 2).

Cambiar algo aquí y volver a ejecutar `python python/analisis_e2.py` regenera
TODAS las salidas: nada se edita a mano.
"""
import numpy as np

# ---------- Configuraciones razonadas de Q ----------
# Lo que decide el comportamiento NO es q solo, sino la relación q·Δt / r, donde
# r es la varianza del giroscopio medida en la Entrega 1 (matriz R).
# Para ω con solo giroscopio, el Kalman en régimen estacionario equivale a un
# filtro paso bajo de primer orden  ω̂_k = ω̂_{k−1} + K (z_k − ω̂_{k−1}).
# Por eso cada configuración se razona por su FRECUENCIA DE CORTE f_c:
#   K = 1 − exp(−2π f_c Δt)          (ganancia que da esa f_c)
#   λ = q·Δt / r = K² / (1 − K)       (solución de la Riccati escalar estacionaria)
#   q = λ · r / Δt                    [°²/s³]
# Contenido en frecuencia de los movimientos: seno lento 0.2–0.3 Hz, seno rápido
# 0.6–0.9 Hz, escalones del servo: armónicos hasta ~5–10 Hz.
# Retraso aproximado de un paso bajo de 1.er orden: 1 / (2π f_c).
CONFIGS_Q = [
    {"nombre": "Q_baja", "f_corte_hz": 1.5,
     "razon": "f_c = 1.5 Hz: deja pasar el seno lento con margen; máxima suavidad; "
              "retraso ≈ 106 ms; atenúa el seno rápido y deforma los escalones."},
    {"nombre": "Q_media", "f_corte_hz": 5.0,
     "razon": "f_c = 5 Hz ≈ 5× la frecuencia del seno rápido: lo sigue sin atenuarlo; "
              "retraso ≈ 32 ms; compromiso ruido/retraso."},
    {"nombre": "Q_alta", "f_corte_hz": 15.0,
     "razon": "f_c = 15 Hz: sigue incluso los escalones del servo; retraso ≈ 11 ms; "
              "casi no filtra (se acerca a la integración directa)."},
]

# Barrido fino para la curva de compromiso Q/R (gráfica, no para seleccionar).
BARRIDO_F_CORTE_HZ = list(np.round(np.logspace(np.log10(0.3), np.log10(40), 15), 3))

# ---------- Regla de selección (se aplica SOLO con los registros de ajuste) ----------
# En teleoperación, retrasos de más de ~50 ms se notan. Se reserva parte para el
# servo y la comunicación: el estimador puede aportar como máximo RETRASO_MAX_MS.
# Entre las configuraciones que cumplen, se elige la de MENOR ruido en reposo.
RETRASO_MAX_MS = 40.0

# ---------- Inicialización ----------
# P0 diagonal: incertidumbre inicial de φ (pose inicial conocida ±2°), ω (arranca
# en reposo, ±5 °/s) y b (sesgo medido en reposo, ±0.5 °/s).
P0_DIAG = {"phi": 2.0**2, "omega": 5.0**2, "bias": 0.5**2}

# ---------- Variantes del modelo ----------
# Estimar el sesgo como estado SOLO tiene sentido si hay una medida absoluta del
# ángulo (inclinación con acelerómetro en plano vertical). Con solo giroscopio el
# sesgo no es observable y se usa el medido en el reposo inicial.
ESTIMAR_BIAS_SI_HAY_INCLINACION = True
Q_BIAS = 1.0e-4               # paseo aleatorio del sesgo [(°/s)²/s]

# ---------- Métodos base (Entrega 1) que se comparan con Kalman ----------
VENTANAS_MEDIA_MOVIL = [5, 21]   # muestras (a 100 Hz: 50 ms y 210 ms)


def q_desde_f_corte(f_corte_hz, r, dt):
    """q que hace que el Kalman (solo giroscopio) tenga frecuencia de corte f_c."""
    K = 1 - np.exp(-2 * np.pi * f_corte_hz * dt)
    lam = K**2 / (1 - K)
    return lam * r / dt


def resolver_q(config, R, dt):
    """Devuelve una copia de la configuración con su q calculada a partir de R."""
    c = dict(config)
    if "q" not in c:
        r = float(np.mean(np.diag(R)[:2]))       # varianza media de los giroscopios
        c["q"] = float(q_desde_f_corte(c["f_corte_hz"], r, dt))
        c["r_usada"] = r
        c["dt_usado"] = dt
    return c
