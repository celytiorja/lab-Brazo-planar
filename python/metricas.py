"""Métricas para comparar métodos. Cada función dice QUÉ mide y en qué unidades."""
import numpy as np


def rmse(a, b, mascara=None):
    e = np.asarray(a) - np.asarray(b)
    if mascara is not None:
        e = e[mascara]
    return float(np.sqrt(np.mean(e**2)))


def quitar_tendencia(x):
    """Resta la recta de mejor ajuste: separa el RUIDO de la DERIVA lenta."""
    x = np.asarray(x, float)
    k = np.arange(len(x))
    return x - np.polyval(np.polyfit(k, x, 1), k)


def ruido(x, mascara=None, sin_tendencia=True):
    """Desviación estándar en un tramo (sin tendencia, para no contar la deriva)."""
    x = np.asarray(x, float)
    if mascara is not None:
        x = x[mascara]
    if len(x) < 3:
        return float("nan")
    return float(np.std(quitar_tendencia(x) if sin_tendencia else x, ddof=1))


def correlacion_cruzada(ref, sig, fs, max_retraso_s=0.5):
    """Correlación cruzada normalizada entre dos señales del mismo largo.

    Devuelve (retrasos [s], coeficientes, retraso_del_pico [s], coef_pico).
    Retraso POSITIVO = `sig` va DETRÁS de `ref` (llega más tarde).
    """
    a = quitar_tendencia(ref)
    b = quitar_tendencia(sig)
    a = (a - a.mean()) / (a.std() * len(a) + 1e-12)
    b = (b - b.mean()) / (b.std() + 1e-12)
    max_k = int(round(max_retraso_s * fs))
    retrasos = np.arange(-max_k, max_k + 1)
    c = np.array([np.sum(a[max(0, -k):len(a) - max(0, k)] * b[max(0, k):len(b) - max(0, -k)])
                  for k in retrasos])
    i = int(np.argmax(c))
    # Refinamiento sub-muestra con una parábola por los 3 puntos del pico.
    fino = 0.0
    if 0 < i < len(c) - 1:
        den = c[i - 1] - 2 * c[i] + c[i + 1]
        if den != 0:
            fino = 0.5 * (c[i - 1] - c[i + 1]) / den
    return retrasos / fs, c, (retrasos[i] + fino) / fs, float(c[i])


def ventanas_estacionarias(cmd, t, asentamiento_s=0.5):
    """True donde la consigna lleva al menos `asentamiento_s` sin cambiar: ahí el
    servo ya llegó y la consigna es una referencia razonable de la posición."""
    cmd = np.asarray(cmd)
    cambio = np.r_[True, np.any(np.diff(cmd, axis=0) != 0, axis=1)] if cmd.ndim == 2 \
        else np.r_[True, np.diff(cmd) != 0]
    t_ultimo_cambio = np.maximum.accumulate(np.where(cambio, t, -np.inf))
    return (t - t_ultimo_cambio) >= asentamiento_s


def deriva_final(phi, fase):
    """Error de volver al punto de partida [°]: el perfil termina en la MISMA pose
    en que empezó, así que media(φ en reposo final) − media(φ en reposo inicial)
    debería ser 0. Lo que no sea 0 es deriva acumulada."""
    ini, fin = fase == 0, fase == 2
    if not ini.any() or not fin.any():
        return np.full(np.shape(phi)[1], np.nan)
    return phi[fin].mean(axis=0) - phi[ini].mean(axis=0)


def derivada(w, dt, esquema="atras"):
    """Aceleración angular numérica α [°/s²] a partir de ω.

    atras:   α_k = (ω_k − ω_{k−1}) / Δt_k             -> ruido × √2/Δt
    central: α_k = (ω_{k+1} − ω_{k−1}) / (Δt_k+Δt_{k+1}) -> ruido × 1/(√2·Δt), pero no causal
    """
    w = np.asarray(w, float)
    alfa = np.zeros_like(w)
    if esquema == "atras":
        d = dt[1:, None] if w.ndim == 2 else dt[1:]
        alfa[1:] = np.diff(w, axis=0) / np.where(d > 0, d, np.nan)
    else:
        d = (dt[1:-1] + dt[2:])
        d = d[:, None] if w.ndim == 2 else d
        alfa[1:-1] = (w[2:] - w[:-2]) / d
    return alfa


def amplificacion_teorica(dt, esquema="atras"):
    """Factor por el que la derivada numérica multiplica la σ del ruido de ω
    (ruido blanco): σ_α = factor · σ_ω."""
    return np.sqrt(2) / dt if esquema == "atras" else 1 / (np.sqrt(2) * dt)
