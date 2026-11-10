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
    # ω_n = 1 rad/s, r = 2 °², Δt = 0.5 s  ->  q = r·Δt·ω_n⁴ = 1
    assert q_desde_f_n(1 / (2 * math.pi), 2.0, dt=0.5) == pytest.approx(1.0)


def test_q_camara_da_la_f_n_pedida():
    """Con la q corregida, f_n baja = más suave y más lento (compromiso real)."""
    from kalman_camara import caracterizar_q
    baja, media, alta = (caracterizar_q(f) for f in (1.5, 3.0, 6.0))
    assert baja["factor_ruido"] < media["factor_ruido"] < alta["factor_ruido"] < 1
    assert baja["ganancia_8Hz"] < 0.4 and media["ganancia_8Hz"] < 0.6   # atenúan el temblor
    assert media["retraso_ms_2Hz"] < 20 and alta["retraso_ms_2Hz"] < 5


# ---------------- ArUco ----------------
def _escena_aruco(posiciones, lado=40, fondo=170):
    """Imagen gris con un cuadro ArUco (con margen blanco) centrado en cada posición."""
    import config_camara as CC
    from generar_marcadores import imagen_marcador
    img = np.full((480, 640, 3), fondo, np.uint8)
    for nombre, (cx, cy) in posiciones.items():
        m = cv2.resize(imagen_marcador(CC.ARUCO_IDS[nombre]), (lado, lado),
                       interpolation=cv2.INTER_NEAREST)
        borde = lado // 4
        m = cv2.copyMakeBorder(m, borde, borde, borde, borde, cv2.BORDER_CONSTANT, value=255)
        x0, y0 = cx - m.shape[1] // 2, cy - m.shape[0] // 2
        img[y0:y0 + m.shape[0], x0:x0 + m.shape[1]] = m[..., None]
    return img


def test_aruco_encuentra_los_tres_aunque_haya_poca_luz():
    from vision import DetectorAruco
    pos = {"hombro": (320, 400), "codo": (320, 260), "muneca": (200, 260)}
    img = _escena_aruco(pos)
    oscura = (img * 0.35 + 15).astype(np.uint8)              # poca luz y poco contraste
    for imagen in (img, oscura):
        hallado = DetectorAruco().buscar(imagen)
        for n, p in pos.items():
            assert hallado[n] == pytest.approx(p, abs=1.5)
    # Y los ángulos salen igual que con los colores: brazo arriba, antebrazo a la izq.
    assert angulos_brazo(hallado["hombro"], hallado["codo"], hallado["muneca"]) == \
        pytest.approx((90, 90), abs=1)


def test_procesador_recuerda_el_hombro_si_se_tapa():
    from teleop_camara import ProcesadorCamara
    proc = ProcesadorCamara("aruco")
    completo = _escena_aruco({"hombro": (320, 400), "codo": (320, 260), "muneca": (200, 260)})
    sin_hombro = _escena_aruco({"codo": (320, 260), "muneca": (200, 260)})
    assert proc.procesar(completo, 0.0)
    assert proc.procesar(sin_hombro, 1 / 30)            # sigue viendo el brazo...
    assert proc.hombro_recordado                         # ...con el hombro de memoria
    assert proc.theta_crudo == pytest.approx((90, 90), abs=1)


def test_lector_video_no_acumula_retraso():
    """Con un programa MÁS LENTO que la cámara, el cuadro usado sigue siendo reciente."""
    import prueba_latencia_video as PL
    from video_rapido import LectorVideo
    srv, url = PL.iniciar_servidor(8799)
    lector = LectorVideo(url)
    try:
        assert lector.metodo.startswith("MJPEG")

        def leer():
            ok, img, _ = lector.leer(0.3)
            return ok, img
        edades = PL.medir_edades(leer, trabajo_s=0.05, duracion_s=2.0)
    finally:
        lector.cerrar()
        srv.shutdown()
    assert len(edades) > 20
    assert edades[-10:].mean() < 80            # con OpenCV aquí ya serían cientos de ms
    assert lector.descartados > 0               # botó los viejos


def test_kalman_camara_medicion_parcial_corrige_solo_theta1():
    """Muñeca tapada: θ1 se sigue midiendo (H con una sola fila), θ2 solo se predice."""
    kf = KalmanCamara([90, 30], r_camara=0.5, f_n_hz=3.0)
    dt = 1 / 30
    for _ in range(30):
        kf.paso(dt, (90.0, 30.0))
    for _ in range(30):                         # 1 s: θ1 salta a 100, la muñeca no se ve
        th, _ = kf.paso(dt, (100.0, np.nan))
    assert th[0] == pytest.approx(100, abs=0.5)  # θ1 corregido por la cámara
    assert th[1] == pytest.approx(30, abs=1.0)   # θ2 se quedó donde estaba


class _ConexionFalsa:
    """Hace de ESP32: guarda lo que se le manda y entrega líneas preparadas."""
    listo = True

    def __init__(self, lineas=()):
        self.enviado, self._lineas = [], list(lineas)

    def enviar(self, texto):
        self.enviado.append(texto)

    def enviar_servos(self, h, c):
        self.enviado.append((h, c))

    def leer_lineas(self):
        lineas, self._lineas = self._lineas, []
        return lineas


def _robot_falso(lineas=()):
    from teleop_camara import Robot
    robot = Robot.__new__(Robot)                 # sin abrir un puerto de verdad
    robot.puerto, robot.conexion = "COMx", _ConexionFalsa(lineas)
    robot.cfg, robot.imu_ok, robot.version, robot.error = "", None, "", ""
    robot.ultimo_cmd, robot._t_ultimo_envio = None, 0.0
    robot._transmision_pedida, robot._t_inicio_envio, robot.muestras = False, None, 0
    return robot


def test_robot_lee_la_configuracion_del_firmware_y_pide_el_giroscopio():
    robot = _robot_falso(["# cfg version=adquisicion-1.2 fs_hz=100 imu1_ok=1 imu2_ok=1",
                          "D," + ",".join(["0"] * 19)])
    robot.atender(None)
    assert robot.conexion.enviado[:2] == ["?", "s 1"]
    assert robot.version == "1.2" and robot.imu_ok is True and robot.muestras == 1
    assert "IMU ok" in robot.estado()[0]


def test_robot_arranque_suave_no_salta_de_golpe():
    robot = _robot_falso()
    robot.empezar_a_enviar()
    assert robot.enviar((150, 20))                       # pide ir lejos de (90, 90)...
    assert robot.ultimo_cmd == (94, 86)                  # ...pero avanza solo 4° por orden
    robot._t_inicio_envio -= 10                          # ya pasó el arranque suave
    robot._t_ultimo_envio -= 1
    assert robot.enviar((150, 20)) and robot.ultimo_cmd == (150, 20)


def test_normalizar_video():
    from teleop_camara import normalizar_video
    assert normalizar_video("0") == 0
    assert normalizar_video("192.168.1.38") == "http://192.168.1.38:4747/video"
    assert normalizar_video("192.168.43.1:4747") == "http://192.168.43.1:4747/video"
    assert normalizar_video("http://x:4747/video") == "http://x:4747/video"


def test_analisis_detecta_imu_del_robot_sin_senal():
    """Un giroscopio real siempre tiene ruido: 0.000 exacto muchas veces seguidas = IMU caída."""
    import pandas as pd
    from analisis_teleop import primera_falla_imu
    rng = np.random.default_rng(0)
    w = rng.normal(0, 0.03, 500)
    sana = pd.DataFrame({"w1_dps": w, "w2_dps": w})
    assert primera_falla_imu(sana) == 500
    w1 = w.copy()
    w1[300:] = 0.0                       # la IMU del hombro deja de responder en la muestra 300
    assert primera_falla_imu(pd.DataFrame({"w1_dps": w1, "w2_dps": w})) == 300
