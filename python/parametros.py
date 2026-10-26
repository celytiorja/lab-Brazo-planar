"""Parámetros físicos del brazo. Todo el código lee de aquí, así un cambio
de medida se hace en UN solo lugar."""

# Longitud de cada eslabón, de centro de rotación a centro de rotación [mm].
# ⚠️ PROVISIONALES: reemplazar con las medidas del modelo / del brazo real.
L1_MM = 100.0   # hombro -> codo
L2_MM = 80.0    # codo -> punta

# ---------- Calibración servo <-> modelo ----------
# El servo solo entiende 0°..180°. El modelo usa θ1 y θ2 (docs/01_cinematica.md).
# Se relacionan con una recta:     ángulo_servo = OFFSET + SIGNO · θ
#   OFFSET: ángulo del servo cuando θ = 0 (dónde quedó el "cero" al montarlo).
#   SIGNO : +1 si al subir el ángulo del servo el eslabón gira antihorario; −1 si no.
# ⚠️ PROVISIONALES hasta calibrar con el brazo montado.
HOMBRO_OFFSET, HOMBRO_SIGNO = 0.0, +1   # servo 0° -> θ1 = 0° (eslabón hacia +x)
CODO_OFFSET, CODO_SIGNO = 90.0, +1      # servo 90° -> θ2 = 0° (brazo estirado)

SERVO_MIN, SERVO_MAX = 0, 180


def _limites_theta(offset, signo):
    """Rango de θ que el servo puede alcanzar (despejando θ de la recta)."""
    a = (SERVO_MIN - offset) * signo
    b = (SERVO_MAX - offset) * signo
    return min(a, b), max(a, b)


# Rango permitido de cada articulación [grados], deducido de la calibración.
THETA1_MIN, THETA1_MAX = _limites_theta(HOMBRO_OFFSET, HOMBRO_SIGNO)
THETA2_MIN, THETA2_MAX = _limites_theta(CODO_OFFSET, CODO_SIGNO)
