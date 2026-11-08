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
# Respaldo contra el DESENFOQUE (brazo rápido): si el cuadro no se lee pero se ve un
# cuadrado del mismo tamaño muy cerca de donde estaba, se usa ese, hasta N cuadros seguidos.
ARUCO_SEGUIR_MAX_CUADROS = 8    # ~0.25 s a 30 fps; luego hay que volver a leer el número
ARUCO_SEGUIR_RADIO_LADOS = 1.5  # distancia máxima, en "lados" del cuadro

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
# En régimen permanente este Kalman es un filtro paso bajo de 2.º orden con
# frecuencia natural f_n:
#     ω_n = 2π f_n = (q / r_c)^(1/4),   r_c = r · Δt   ->   q = r · Δt · (2π f_n)^4
# (r = varianza POR CUADRO de la cámara, medida con la tecla N; r·Δt la convierte en
# densidad, que es lo que se compara con q, que es densidad por segundo.)
# Como q es proporcional a r, el comportamiento depende SOLO de f_n (no de cuánto
# tiemble la cámara): la R medida decide la consistencia (NIS), no la suavidad.
# Contenido del movimiento: voluntario < ~2 Hz; temblor fisiológico ~8–12 Hz.
# Números de cada configuración (simulación del filtro real a 30 cuadros/s,
# kalman_camara.caracterizar_q; se regeneran en resultados/<origen>/teleop/):
CONFIGS_Q_CAMARA = [
    {"nombre": "Q_baja", "f_n_hz": 1.5,
     "razon": "muy suave: ruido x0.53, temblor 8 Hz x0.27; retraso ~40-60 ms a 1-2 Hz"},
    {"nombre": "Q_media", "f_n_hz": 3.0,
     "razon": "equilibrio: ruido x0.70, temblor 8 Hz x0.49; retraso < 16 ms hasta 2 Hz"},
    {"nombre": "Q_alta", "f_n_hz": 6.0,
     "razon": "casi sin retraso (< 3 ms a 2 Hz); filtra poco: ruido x0.86"},
]
FPS_NOMINAL = 30.0              # Δt nominal para convertir r en densidad
R_CAMARA_POR_DEFECTO = 1.0      # [°²] hasta que midas el ruido real (tecla N)
P0_DIAG = {"theta": 10.0**2, "omega": 50.0**2}
# Oclusión (no se ve el brazo): Kalman predice con velocidad constante hasta
# PREDICCION_LIBRE_S; después la velocidad se apaga con constante de tiempo FRENADO_TAU_S.
PREDICCION_LIBRE_S = 0.20
FRENADO_TAU_S = 0.15

# ---------- Envío al robot ----------
PERIODO_ORDENES_S = 0.04        # máximo 25 órdenes por segundo
CAMBIO_MIN_GRADOS = 1           # no reenviar si el servo cambiaría menos de esto
