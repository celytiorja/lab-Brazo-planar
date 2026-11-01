"""Pruebas de la cadena de las Entregas 1 y 2 (Kalman, media móvil, datos)."""
import numpy as np
import pandas as pd
import pytest

import config_imu as C
import config_kalman as CK
from estimadores import IntegracionDirecta, KalmanBrazo, MediaMovilIntegracion
from grabador import parsear_linea_datos
from kalman import FiltroKalman
from metricas import correlacion_cruzada
from tiempo_real import valores_a_fisico


def test_kalman_escalar_converge_al_valor_medido():
    kf = FiltroKalman([0.0], [[100.0]])
    for _ in range(200):
        kf.predecir(np.eye(1), np.eye(1) * 1e-4)
        kf.actualizar(np.array([5.0]), np.eye(1), np.eye(1) * 0.1)
    assert kf.x[0] == pytest.approx(5.0, abs=1e-2)
    asim, min_ev = kf.chequeo_P()
    assert asim < 1e-12 and min_ev > 0


def test_brazo_quieto_sin_ruido_no_se_mueve():
    R = np.diag([0.0036, 0.0036])
    kf = KalmanBrazo([30, 75], [0.5, -0.2], R, q=0.05)
    for _ in range(500):
        phi, omega = kf.paso(0.01, np.array([0.5, -0.2]))   # solo el sesgo
    assert phi == pytest.approx([30, 75], abs=1e-6)
    assert omega == pytest.approx([0, 0], abs=1e-6)


def test_giro_constante_se_integra_igual_en_los_tres_metodos():
    metodos = [IntegracionDirecta([0, 0], [0, 0]), MediaMovilIntegracion([0, 0], [0, 0], 5),
               KalmanBrazo([0, 0], [0, 0], np.diag([0.0036] * 2), q=0.05)]
    for m in metodos:
        for _ in range(1000):                 # 10 s a 20 °/s -> 200°
            phi, _ = m.paso(0.01, np.array([20.0, -10.0]))
        assert phi == pytest.approx([200, -100], abs=1.5), m.nombre


def test_retraso_media_movil_es_n_menos_1_medios():
    fs, N = 100.0, 21
    t = np.arange(0, 20, 1 / fs)
    w = 30 * np.sin(2 * np.pi * 0.5 * t)
    mm = MediaMovilIntegracion([0, 0], [0, 0], N)
    salida = np.array([mm.paso(1 / fs, np.array([x, x]))[1][0] for x in w])
    retraso = correlacion_cruzada(w, salida, fs)[2]
    assert retraso * 1e3 == pytest.approx((N - 1) / 2 * 10, abs=2)


def test_q_desde_frecuencia_de_corte():
    r, dt = 0.0036, 0.01
    for fc in (1.5, 5, 15):
        q = CK.q_desde_f_corte(fc, r, dt)
        p = 1.0                                # Riccati escalar hasta converger
        for _ in range(20000):
            pp = p + q * dt
            k = pp / (pp + r)
            p = (1 - k) * pp
        assert -np.log(1 - k) / (2 * np.pi * dt) == pytest.approx(fc, rel=1e-3)


def test_linea_del_firmware_y_conversion_iguales_al_analisis():
    linea = "D,7,1000,1410,1,0,90,90,10,20,16384,1,2,655,30,40,16300,3,4,-1310"
    v = parsear_linea_datos(linea)
    assert len(v) == len(C.COLUMNAS_CRUDAS)
    _, cmd_h, cmd_c, w, _ = valores_a_fisico(v)
    assert (cmd_h, cmd_c) == (90, 90)
    esperado = [C.EJE_GIRO[1][1] * 655 / 65.5, C.EJE_GIRO[2][1] * -1310 / 65.5]
    assert w == pytest.approx(esperado)
    assert parsear_linea_datos("# cfg algo") is None
    assert parsear_linea_datos("D,1,2,3") is None
