"""Pruebas de la teleoperación con cámara (sin cámara real: imágenes dibujadas)."""
import math

import cv2
import numpy as np
import pytest

from kalman_camara import KalmanCamara, q_desde_f_n
from vision import Marcador, angulos_brazo


def test_angulos_brazo_convencion_del_robot():
    # Hombro abajo, brazo hacia ARRIBA en la imagen (y de la imagen crece hacia abajo).
    assert angulos_brazo((100, 300), (100, 200), (100, 100)) == pytest.approx((90, 0))
    # Antebrazo doblado hacia la izquierda: +90° relativo (antihorario).
    assert angulos_brazo((100, 300), (100, 200), (0, 200)) == pytest.approx((90, 90))


def test_marcador_encuentra_su_color():
    img = np.full((240, 320, 3), 180, np.uint8)
    cv2.circle(img, (200, 80), 10, (0, 200, 0), -1)        # verde
    cv2.circle(img, (60, 160), 10, (40, 40, 230), -1)      # rojo
    m = Marcador("codo")
    m.aprender(img, 200, 80)
    m.pos = None
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    assert m.buscar(hsv) == pytest.approx((200, 80), abs=1)


def test_kalman_camara_sigue_rampa_y_predice_si_falta_medicion():
    kf = KalmanCamara([0, 0], r_camara=0.5, f_n_hz=3.0)
    dt = 1 / 30
    for k in range(120):                       # θ1 sube a 30 °/s
        th, w = kf.paso(dt, (30 * k * dt, 0.0))
    assert w[0] == pytest.approx(30, abs=1)
    th_antes = th[0]
    th, _ = kf.paso(dt, None)                  # cuadro sin medición: solo predice
    assert th[0] == pytest.approx(th_antes + 30 * dt, abs=0.2)


def test_q_desde_f_n():
    assert q_desde_f_n(1 / (2 * math.pi), 2.0) == pytest.approx(2.0)
