"""Configuración de la teleoperación con cámara (Entrega 2, opción 1: solo cámara).

El teléfono, sostenido ARRIBA de la mesa y mirando hacia abajo, ve tu brazo moverse
en el plano de la mesa (el mismo plano horizontal del robot). Tres marcadores
—hombro, codo y muñeca— dan los ángulos θ1 y θ2 de TU brazo.
"""

# ---------- Fuente de video ----------
# DroidCam (teléfono): la app muestra una dirección como http://192.168.1.23:4747
# -> aquí va  "http://192.168.1.23:4747/video"
# Una cámara USB o DroidCam instalada como webcam: un número (0, 1, 2...).
FUENTE_VIDEO = 0
ANCHO, ALTO = 640, 480          # se reduce el video a esto: más rápido de procesar

# ---------- Marcadores ----------
MARCADORES = ("hombro", "codo", "muneca")

# Cómo se encuentran:  "aruco" (cuadros impresos blanco/negro, RECOMENDADO) o "color".
# Se puede cambiar sin tocar esto:  --modo color
MODO_DETECCION = "aruco"

# ArUco: diccionario 4×4 (casillas grandes -> se leen aunque el cuadro se vea pequeño).
# Cada articulación tiene su número. Los cuadros se generan con generar_marcadores.py.
ARUCO_DICCIONARIO = "DICT_4X4_50"
ARUCO_IDS = {"hombro": 0, "codo": 1, "muneca": 2}
ARUCO_LADO_CM = 6.0             # lado impreso (con la cámara a 60–80 cm se ve de ~35 px)

# El hombro casi no se mueve: si un cuadro no se ve un momento, se usa su última
# posición en vez de perder la medición completa.
RECORDAR_HOMBRO = True

# --- Solo modo "color" ---
# Tolerancias alrededor del color que aprendes con un clic (escala HSV de OpenCV).
TOL_TONO = 12                   # H va de 0 a 179
TOL_SAT = 70                    # S de 0 a 255
TOL_VAL = 70                    # V de 0 a 255
SAT_MIN = 70                    # por debajo, el color es "grisáceo": no confiable
AREA_MIN_PX = 40                # manchas más pequeñas se ignoran (ruido)
RADIO_BUSQUEDA_PX = 120         # se busca cerca de donde estaba en el cuadro anterior

# Si la cámara te ve "en espejo" (p. ej. la usas al revés), poner True.
ESPEJO = False

# ---------- Kalman de la cámara ----------
# Estado por articulación: [θ, ω]; medición: θ de la cámara (H = [1, 0]).
# En régimen permanente este Kalman es un filtro de 2.º orden con frecuencia natural
#     f_n = (q / r)^(1/4) / (2π)     ->     q = r · (2π f_n)^4
# y retraso aproximado a baja frecuencia ≈ √2 / (2π f_n).
# El movimiento voluntario del brazo humano está por debajo de ~2 Hz.
CONFIGS_Q_CAMARA = [
    {"nombre": "Q_baja", "f_n_hz": 1.5, "razon": "muy suave; retraso ≈ 150 ms"},
    {"nombre": "Q_media", "f_n_hz": 3.0, "razon": "sigue movimientos de hasta ~2 Hz; retraso ≈ 75 ms"},
    {"nombre": "Q_alta", "f_n_hz": 6.0, "razon": "casi sin retraso (≈ 37 ms); filtra poco"},
]
R_CAMARA_POR_DEFECTO = 1.0      # [°²] hasta que midas el ruido real (tecla N)
P0_DIAG = {"theta": 10.0**2, "omega": 50.0**2}

# ---------- Envío al robot ----------
PERIODO_ORDENES_S = 0.04        # máximo 25 órdenes por segundo
CAMBIO_MIN_GRADOS = 1           # no reenviar si el servo cambiaría menos de esto
