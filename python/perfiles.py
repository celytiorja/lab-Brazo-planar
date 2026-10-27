"""Copia en Python de los perfiles de firmware/adquisicion (función consignaPerfil).
Se usa para generar datos sintéticos con EXACTAMENTE la misma consigna.
⚠️ Si se cambia un perfil en el firmware, hay que cambiarlo también aquí."""
import math

REPOSO_S = 3.0
ESCALONES = [(90, 90), (60, 90), (120, 90), (60, 90),
             (90, 90), (90, 60), (90, 120), (90, 60),
             (60, 120), (90, 90)]
DURACION = {1: 20.0, 2: 20.0, 3: 10.0}


def duracion_total(p):
    return 2 * REPOSO_S + DURACION[p]


def _redondear(x):
    """Igual que lroundf() del firmware (round() de Python redondea 0.5 al par)."""
    return int(math.floor(x + 0.5)) if x >= 0 else -int(math.floor(-x + 0.5))


def consigna(p, t):
    """(cmd_h, cmd_c, fase) del perfil p en el instante t [s], o None al terminar."""
    dur = DURACION[p]
    if t < REPOSO_S:
        return 90, 90, 0
    if t >= 2 * REPOSO_S + dur:
        return None
    if t >= REPOSO_S + dur:
        return 90, 90, 2
    tau = t - REPOSO_S
    if p == 1:
        h, c = ESCALONES[min(max(int(tau / 2.0), 0), 9)]
    elif p == 2:
        h = _redondear(90 + 30 * math.sin(2 * math.pi * 0.2 * tau))
        c = _redondear(90 + 30 * math.sin(2 * math.pi * 0.3 * tau))
    else:
        h = _redondear(90 + 25 * math.sin(2 * math.pi * 0.6 * tau))
        c = _redondear(90 + 25 * math.sin(2 * math.pi * 0.9 * tau))
    return h, c, 1
