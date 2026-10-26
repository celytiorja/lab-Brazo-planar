"""Traducción entre los ángulos del MODELO (θ1, θ2) y los del SERVO (0°..180°).

    ángulo_servo = OFFSET + SIGNO · θ        (ver parametros.py)
    θ            = (ángulo_servo − OFFSET) · SIGNO      (SIGNO = ±1, así que
                                                         dividir = multiplicar)
"""
import parametros as P


def _a_servo(theta, offset, signo):
    angulo = round(offset + signo * theta)   # el servo recibe grados enteros
    return max(P.SERVO_MIN, min(P.SERVO_MAX, angulo))


def modelo_a_servo(theta1, theta2):
    """(θ1, θ2) del modelo -> (servo_hombro, servo_codo) enteros en 0..180."""
    return (_a_servo(theta1, P.HOMBRO_OFFSET, P.HOMBRO_SIGNO),
            _a_servo(theta2, P.CODO_OFFSET, P.CODO_SIGNO))


def servo_a_modelo(servo_hombro, servo_codo):
    """(servo_hombro, servo_codo) -> (θ1, θ2) del modelo."""
    return ((servo_hombro - P.HOMBRO_OFFSET) * P.HOMBRO_SIGNO,
            (servo_codo - P.CODO_OFFSET) * P.CODO_SIGNO)
