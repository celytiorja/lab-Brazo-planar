"""TELEOPERACIÓN CON CÁMARA — el robot copia tu brazo (Entrega 2, opción 1).

Requisitos:
  - Teléfono ARRIBA de la mesa, mirando hacia abajo, con la app DroidCam.
  - 3 marcadores en tu brazo: HOMBRO, CODO y MUÑECA. Por defecto son cuadros ArUco
    impresos (python python/generar_marcadores.py -> docs/marcadores_aruco.pdf).
    Con  --modo color  se usan papeles de color (respaldo).
  - ESP32 con firmware/adquisicion (para mover el robot) y el Monitor Serie CERRADO.

    python python/teleop_camara.py --video 192.168.1.38 --puerto auto
    python python/teleop_camara.py --video http://192.168.1.38:4747/video --puerto COM5
    python python/teleop_camara.py --video 0                    (webcam, sin robot)
    python python/teleop_camara.py --video 0 --modo color       (papeles de color)

  --video acepta la IP sola (se completa a http://IP:4747/video).
  --puerto auto busca el ESP32 solo.

Teclas (con la ventana activa; mayúscula o minúscula da igual):
  C  pose de referencia: tu brazo ESTIRADO hacia adelante = robot en (90°, 0°)
  N  medir el ruido de la cámara: brazo QUIETO 10 s -> R del Kalman
  R  ENVIAR al robot: activar / pausar (arranca en pausa; al activar, arranque suave)
  F  cambiar la fuente que mueve el robot: crudo (cámara) <-> Kalman
  G  grabar la sesión: iniciar / detener (datos/teleop/, se sube a GitHub sola)
  1 2 3  Q_baja / Q_media / Q_alta
  M  espejo: si al mover el brazo a la izquierda el robot va a la derecha
  D  diagnóstico (solo ArUco): dibuja en rojo los cuadros que ve pero NO logra leer
  L  (solo modo color) aprender colores: clic en hombro, codo y muñeca, en ese orden
  Q o Esc (o cerrar la ventana)  salir: si grabaste sesiones, se analizan y se suben

Qué se guarda en cada sesión (datos/teleop/sesion_XX.csv, un renglón por cuadro):
  ángulos crudos y de Kalman, si se vieron los marcadores, la orden al robot, y los
  TIEMPOS medidos: cómputo de Kalman, detección + Kalman, espera del cuadro.
  Con robot, además  sesion_XX_robot.csv: el giroscopio del robot a 100 Hz (las IMU de
  la Entrega 1) -> se mide cuánto tarda el robot en moverse y cuánto vibra.
"""
import argparse
import csv
import json
import re
import time
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

import config_camara as CC
import config_imu as C
import reporte as Rp
from grabador import parsear_linea_datos
from kalman_camara import KalmanCamara
from panel_teleop import AMARILLO, ROJO, VERDE, Panel
from servos import modelo_a_servo
from tiempo_real import valores_a_fisico
from video_rapido import LectorVideo
from vision import angulos_brazo, crear_detector

CARPETA = Rp.RAIZ / "datos" / "teleop"
ARCHIVO_RUIDO = CARPETA / "ruido_camara.json"
CUADROS_RUIDO = 300                      # ~10 s a 30 cuadros/s
VENTANA = "Teleoperacion"
DT_REINICIO_S = 0.7          # si pasan más de esto sin cuadros, Kalman reinicia en la medición
ARRANQUE_SUAVE_S = 1.5       # al pulsar R: durante este tiempo el robot va despacio a tu pose
PASO_ARRANQUE_GRADOS = 4     # máximo cambio por orden durante el arranque suave


class ProcesadorCamara:
    """Todo lo que pasa con cada cuadro, separado de la ventana (así se puede probar)."""

    def __init__(self, modo=None, archivo_ruido=ARCHIVO_RUIDO):
        self.archivo_ruido = Path(archivo_ruido)
        self.archivo_ruido.parent.mkdir(parents=True, exist_ok=True)
        self.detector = crear_detector(modo)
        self.pos = {n: None for n in CC.MARCADORES}      # posiciones del último cuadro
        self.hombro_recordado = False                     # True: se usó la última posición
        self._hombro_ultimo = None
        self.offset = np.zeros(2)
        self.pose_calibrada = False
        self.r_camara = np.array([CC.R_CAMARA_POR_DEFECTO] * 2)
        self.origen_r = "valor por defecto (aún no medido: tecla N)"
        if self.archivo_ruido.exists():
            d = json.loads(self.archivo_ruido.read_text(encoding="utf-8"))
            self.r_camara = np.array(d["r_camara"])
            self.origen_r = f"medido {d['fecha']}"
        self.i_config = 1                                  # Q_media
        self.kalman = None
        self.fuente = "kalman"
        self.t_ant = None
        self.theta_crudo = None
        self.theta_kf = None
        self.omega_kf = None
        self.visto = False
        self.solo_theta1 = False
        self.t_calc_us = 0.0           # solo el paso de Kalman
        self.t_proc_ms = 0.0           # detección + ángulos + Kalman (todo el cuadro)
        self._ruido = None

    @property
    def config(self):
        return CC.CONFIGS_Q_CAMARA[self.i_config]

    def detector_listo(self):
        return self.detector.listo

    def reiniciar_kalman(self, theta0):
        self.kalman = KalmanCamara(theta0, self.r_camara, self.config["f_n_hz"])

    def elegir_q(self, i):
        self.i_config = i
        if self.theta_kf is not None:
            self.reiniciar_kalman(self.theta_kf)

    def calibrar_pose(self):
        """Tu pose actual pasa a valer (90°, 0°): brazo estirado hacia adelante."""
        if self.theta_crudo is None:
            return False
        self.offset = np.array([90.0, 0.0]) - (self.theta_crudo - self.offset)
        self.theta_crudo = np.array([90.0, 0.0])
        self.reiniciar_kalman(np.array([90.0, 0.0]))
        self.pose_calibrada = True
        return True

    def empezar_medir_ruido(self):
        self._ruido = []

    @property
    def midiendo_ruido(self):
        return self._ruido is not None

    @property
    def progreso_ruido(self):
        return 0.0 if self._ruido is None else len(self._ruido) / CUADROS_RUIDO

    def procesar(self, imagen_bgr, t):
        """Un cuadro de video. Devuelve True si se vieron los 3 marcadores."""
        t_inicio = time.perf_counter()
        visto = self._procesar(imagen_bgr, t)
        self.t_proc_ms = (time.perf_counter() - t_inicio) * 1e3
        return visto

    def _procesar(self, imagen_bgr, t):
        dt = 0.0 if self.t_ant is None else t - self.t_ant
        self.t_ant = t
        pos = self.detector.buscar(imagen_bgr)
        # El hombro casi no se mueve: si no se ve en este cuadro, se usa el último visto.
        self.hombro_recordado = False
        if pos["hombro"] is not None:
            self._hombro_ultimo = pos["hombro"]
        elif CC.RECORDAR_HOMBRO and self._hombro_ultimo is not None:
            pos["hombro"] = self._hombro_ultimo
            self.hombro_recordado = True
        self.pos = pos
        self.visto = all(p is not None for p in pos.values())
        # Medición PARCIAL: sin muñeca pero con hombro y codo, θ1 sí se puede medir.
        self.solo_theta1 = (not self.visto and pos["hombro"] is not None
                            and pos["codo"] is not None)
        medido = None
        if self.solo_theta1 and self.kalman is not None:
            th1 = angulos_brazo(pos["hombro"], pos["codo"],
                                (2 * pos["codo"][0] - pos["hombro"][0],
                                 2 * pos["codo"][1] - pos["hombro"][1]))[0]
            medido = np.array([th1 + self.offset[0], np.nan])
        if self.visto:
            crudo = np.array(angulos_brazo(pos["hombro"], pos["codo"], pos["muneca"]))
            self.theta_crudo = crudo + self.offset
            medido = self.theta_crudo
            if self._ruido is not None:
                self._ruido.append(self.theta_crudo.copy())
                if len(self._ruido) >= CUADROS_RUIDO:
                    self._terminar_ruido()
        if self.kalman is not None and dt > DT_REINICIO_S and self.visto:
            # Se cortó el video un buen rato: predecir tanto tiempo no tiene sentido.
            self.reiniciar_kalman(medido)
            dt = 0.0
        if self.kalman is None:
            if medido is None or not self.visto:
                return False
            self.reiniciar_kalman(medido)
        t0 = time.perf_counter()
        if dt > 0:
            self.theta_kf, self.omega_kf = self.kalman.paso(dt, medido)
        else:
            x = self.kalman.kf.x
            self.theta_kf, self.omega_kf = np.array([x[0], x[2]]), np.array([x[1], x[3]])
        self.t_calc_us = (time.perf_counter() - t0) * 1e6
        return self.visto

    def _terminar_ruido(self):
        datos = np.array(self._ruido)
        self._ruido = None
        self.r_camara = np.var(datos, axis=0, ddof=1)
        fecha = datetime.now().isoformat(timespec="seconds")
        self.origen_r = f"medido {fecha}"
        self.archivo_ruido.write_text(json.dumps({
            "r_camara": self.r_camara.tolist(), "sigma_deg": np.sqrt(self.r_camara).tolist(),
            "media_deg": datos.mean(axis=0).tolist(), "cuadros": len(datos), "fecha": fecha},
            indent=2), encoding="utf-8")
        self.reiniciar_kalman(self.theta_kf if self.theta_kf is not None else datos[-1])

    def theta_para_robot(self):
        return self.theta_kf if self.fuente == "kalman" else self.theta_crudo


class Sesion:
    """Grabación de una sesión de teleoperación (para medir crudo vs Kalman)."""
    COLUMNAS = ["t_s", "visto", "solo_theta1", "hombro_memoria", "theta1_crudo", "theta2_crudo",
                "theta1_kf", "theta2_kf", "w1_kf", "w2_kf", "fuente", "enviando",
                "cmd_h", "cmd_c", "enviado", "t_calc_kf_us", "t_proc_ms", "t_espera_ms"]
    COLUMNAS_ROBOT = ["t_s", "seq", "t1_us", "w1_dps", "w2_dps"]

    def __init__(self, proc, carpeta=CARPETA, t0=None):
        carpeta = Path(carpeta)
        carpeta.mkdir(parents=True, exist_ok=True)
        n = max([int(p.stem.split("_")[1]) for p in carpeta.glob("sesion_??.csv")] + [0]) + 1
        self.ruta = carpeta / f"sesion_{n:02d}.csv"
        self.ruta_robot = carpeta / f"sesion_{n:02d}_robot.csv"
        self._f = open(self.ruta, "w", newline="", encoding="utf-8")
        self._w = csv.writer(self._f)
        self._w.writerow(self.COLUMNAS)
        self._fr = None                  # el archivo del robot se crea con el 1.er dato
        self.t0 = time.perf_counter() if t0 is None else t0
        self.meta = {"fecha": datetime.now().isoformat(timespec="seconds"),
                     "r_camara": proc.r_camara.tolist(), "origen_r": proc.origen_r,
                     "configs_q": CC.CONFIGS_Q_CAMARA, "offset": proc.offset.tolist(),
                     "fuente_video": str(CC.FUENTE_VIDEO),
                     "modo_deteccion": proc.detector.modo,
                     "periodo_ordenes_s": CC.PERIODO_ORDENES_S,
                     "cambio_min_grados": CC.CAMBIO_MIN_GRADOS,
                     "commit": Rp.commit_actual()}
        self.filas = 0
        self.filas_robot = 0

    def duracion_s(self, t):
        return t - self.t0

    def agregar(self, proc, t, enviando, cmd, enviado, t_espera_ms):
        def f(v, i):
            return "" if v is None else f"{v[i]:.3f}"
        self._w.writerow([f"{t - self.t0:.4f}", int(proc.visto), int(proc.solo_theta1),
                          int(proc.hombro_recordado),
                          f(proc.theta_crudo, 0), f(proc.theta_crudo, 1),
                          f(proc.theta_kf, 0), f(proc.theta_kf, 1),
                          f(proc.omega_kf, 0), f(proc.omega_kf, 1),
                          f"{proc.fuente}:{proc.config['nombre']}", int(enviando),
                          "" if cmd is None else cmd[0], "" if cmd is None else cmd[1],
                          int(enviado), f"{proc.t_calc_us:.1f}", f"{proc.t_proc_ms:.2f}",
                          f"{t_espera_ms:.2f}"])
        self.filas += 1

    def agregar_robot(self, t, v):
        """Una muestra "D,..." del ESP32 -> giroscopio del robot en °/s (como en la E1)."""
        if self._fr is None:
            self._fr = open(self.ruta_robot, "w", newline="", encoding="utf-8")
            self._wr = csv.writer(self._fr)
            self._wr.writerow(self.COLUMNAS_ROBOT)
        _, _, _, w, _ = valores_a_fisico(v)
        self._wr.writerow([f"{t - self.t0:.4f}", v[0], v[1], f"{w[0]:.3f}", f"{w[1]:.3f}"])
        self.filas_robot += 1

    def cerrar(self):
        self._f.close()
        if self._fr is not None:
            self._fr.close()
        self.meta["cuadros"] = self.filas
        self.meta["muestras_robot"] = self.filas_robot
        self.ruta.with_suffix(".json").write_text(json.dumps(self.meta, indent=2, ensure_ascii=False),
                                                  encoding="utf-8")
        return self.ruta


def decidir_envio(cmd, ultimo_cmd, ahora, t_ultimo_envio):
    """¿Mandar esta orden al ESP32? Solo si cambió ≥ CAMBIO_MIN_GRADOS y pasó el periodo
    mínimo (máx. 25 órdenes/s: el servo no acepta más de una cada 20 ms)."""
    if ultimo_cmd is None:
        return True
    cambio = max(abs(cmd[0] - ultimo_cmd[0]), abs(cmd[1] - ultimo_cmd[1]))
    return cambio >= CC.CAMBIO_MIN_GRADOS and ahora - t_ultimo_envio >= CC.PERIODO_ORDENES_S


def guia_grabacion(segundos):
    """Qué hacer durante la grabación (protocolo de docs/PRUEBA_FINAL.md)."""
    if segundos < 10:
        return "0-10 s: mueve el brazo LENTO"
    if segundos < 20:
        return "10-20 s: mueve el brazo RAPIDO"
    if segundos < 30:
        return "20-30 s: tapa la MUNECA con la otra mano 2 veces"
    return "listo: tecla G para terminar"


class Robot:
    """El ESP32 (firmware/adquisicion): conexión, estado, órdenes y giroscopio."""

    def __init__(self, puerto):
        from conexion import ConexionESP32
        self.puerto = puerto
        self.conexion = ConexionESP32()
        self.conexion.conectar(puerto, C.BAUDIOS_ADQUISICION)   # puede lanzar SerialException
        self.cfg = ""                     # línea "# cfg ..." del firmware
        self.imu_ok = None
        self.version = ""
        self.ultimo_cmd = None
        self._t_ultimo_envio = 0.0
        self._transmision_pedida = False
        self._t_inicio_envio = None
        self.muestras = 0
        self.error = ""

    def estado(self):
        if self.error:
            return f"ERROR: {self.error[:28]}", ROJO
        if not self.conexion.listo:
            return f"{self.puerto}: conectando...", AMARILLO
        if self.imu_ok is False:
            return f"{self.puerto}: revisa las IMU", ROJO
        fw = f" fw {self.version}" if self.version else ""
        return f"{self.puerto}{fw}  " + ("IMU ok" if self.imu_ok else "listo"), VERDE

    def empezar_a_enviar(self):
        self._t_inicio_envio = time.perf_counter()

    def atender(self, sesion):
        """Lee lo que mandó el ESP32: config, avisos y muestras del giroscopio."""
        if not self.conexion.listo:
            return
        if not self._transmision_pedida:
            self.conexion.enviar("s 1")       # que mande su giroscopio (100 Hz)
            self._transmision_pedida = True
        try:
            lineas = self.conexion.leer_lineas()
        except Exception as e:                  # cable desconectado, etc.
            self.error = str(e)
            return
        t_rx = time.perf_counter()
        for linea in lineas:
            if linea.startswith("# cfg"):
                self.cfg = linea
                m = re.search(r"version=(\S+)", linea)
                self.version = m.group(1).replace("adquisicion-", "") if m else ""
                self.imu_ok = "imu1_ok=1" in linea and "imu2_ok=1" in linea
                continue
            v = parsear_linea_datos(linea)
            if v is not None:
                self.muestras += 1
                if sesion is not None:
                    sesion.agregar_robot(t_rx, v)

    def enviar(self, cmd):
        """Manda la orden si toca (regla de decidir_envio). Devuelve True si se envió."""
        if cmd is None or not self.conexion.listo or self.error:
            return False
        ahora = time.perf_counter()
        objetivo = cmd
        if self._t_inicio_envio is not None and ahora - self._t_inicio_envio < ARRANQUE_SUAVE_S:
            # Arranque suave: el robot venía de otra pose; se acerca a pasos cortos.
            desde = self.ultimo_cmd or (90, 90)          # el firmware arranca en 90/90
            objetivo = tuple(int(d + max(-PASO_ARRANQUE_GRADOS, min(PASO_ARRANQUE_GRADOS, c - d)))
                             for d, c in zip(desde, cmd))
        if not decidir_envio(objetivo, self.ultimo_cmd, ahora, self._t_ultimo_envio):
            return False
        try:
            self.conexion.enviar_servos(*objetivo)
        except Exception as e:
            self.error = str(e)
            return False
        self.ultimo_cmd, self._t_ultimo_envio = objetivo, ahora
        return True

    def cerrar(self):
        try:
            self.conexion.enviar("s 0")
        except Exception:
            pass
        self.conexion.desconectar()


def normalizar_video(arg):
    """'0' -> 0 (webcam);  '192.168.1.38' o '192.168.1.38:4747' -> URL de DroidCam."""
    if arg.isdigit():
        return int(arg)
    if re.fullmatch(r"\d{1,3}(\.\d{1,3}){3}(:\d+)?", arg):
        return f"http://{arg if ':' in arg else arg + ':4747'}/video"
    return arg


def abrir_robot(puerto):
    """Abre el ESP32 o explica qué pasa (sin errores largos de Python)."""
    from serial import SerialException
    from conexion import detectar_puerto, puertos_disponibles
    if puerto.lower() == "auto":
        puerto = detectar_puerto() or ""
        if not puerto:
            disp = ", ".join(f"{p} ({d})" for p, d in puertos_disponibles()) or "ninguno"
            raise SystemExit(f"No encontré el ESP32. Puertos disponibles: {disp}\n"
                             "Usa --puerto COMx con el de la placa.")
    try:
        robot = Robot(puerto)
    except SerialException as e:
        disp = ", ".join(p for p, _ in puertos_disponibles()) or "ninguno"
        raise SystemExit(f"No se pudo abrir {puerto}: {e}\n"
                         f"  - ¿El Monitor Serie de Arduino está CERRADO?\n"
                         f"  - Puertos disponibles: {disp}")
    print(f"Robot en {puerto}. Arranca en PAUSA: tecla R para que te copie.")
    return robot


def pista(proc, robot, enviando):
    """El siguiente paso, en una línea (abajo del video, en amarillo)."""
    if proc.midiendo_ruido:
        return ""
    if proc.theta_crudo is None:
        return ("Muestra los 3 cuadros: 0 hombro, 1 codo, 2 muneca" if proc.detector.modo == "aruco"
                else "Muestra los 3 marcadores de color")
    if not proc.pose_calibrada:
        return "Brazo estirado al frente y tecla C"
    if not proc.origen_r.startswith("medido"):
        return "Brazo quieto y tecla N (mide R, 10 s)"
    if robot is not None and not enviando:
        return "Tecla R: el robot empieza a copiarte"
    return ""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--video", default=str(CC.FUENTE_VIDEO),
                    help="IP del teléfono, URL de DroidCam o número de cámara (0, 1...)")
    ap.add_argument("--puerto", default="", help="COMx, 'auto', o vacío = sin robot")
    ap.add_argument("--modo", default=CC.MODO_DETECCION, choices=["aruco", "color"],
                    help="marcadores: cuadros ArUco impresos (por defecto) o papeles de color")
    args = ap.parse_args()
    fuente = normalizar_video(args.video)
    CC.FUENTE_VIDEO = fuente

    print(f"Abriendo video: {fuente} ...")
    cam = LectorVideo(fuente)
    if not cam.abierto():
        pista_url = ""
        if isinstance(fuente, str) and fuente.startswith("http") and fuente.count(":") < 2:
            pista_url = ("\n  -> Falta el PUERTO. DroidCam usa el 4747: "
                         f"{fuente.split('/video')[0]}:4747/video")
        raise SystemExit(f"No se pudo abrir el video {fuente!r}.\n"
                         f"  - ¿DroidCam abierto en el teléfono y la IP es la que muestra la app?\n"
                         f"  - ¿El PC y el teléfono en la misma red (o el PC en el hotspot del teléfono)?\n"
                         f"  - ¿El navegador está CERRADO? (DroidCam atiende a un solo programa){pista_url}")
    print(f"Video abierto con: {cam.metodo}")
    robot = abrir_robot(args.puerto) if args.puerto else None

    proc = ProcesadorCamara(args.modo)
    panel = Panel(CC.ALTO)
    estado = {"enviando": False, "fps": 0.0, "diagnostico": False, "robot": robot,
              "sesion": None, "pista": ""}
    espejo = CC.ESPEJO
    sesion = None
    sesiones_grabadas = []
    subidas = []
    clics = {"pendientes": [] if proc.detector_listo() else list(CC.MARCADORES)}
    ultima_imagen = {"img": None}
    if clics["pendientes"]:
        panel.mensaje("Modo color: clic en HOMBRO, CODO y MUNECA", 8)

    def al_clic(evento, x, y, *_):
        if (evento == cv2.EVENT_LBUTTONDOWN and clics["pendientes"] and x < CC.ANCHO
                and ultima_imagen["img"] is not None):
            nombre = clics["pendientes"].pop(0)
            marcador = proc.detector.marcadores[nombre]
            marcador.aprender(ultima_imagen["img"], x, y)
            siguiente = clics["pendientes"][0].upper() if clics["pendientes"] else ""
            panel.mensaje(f"{nombre} aprendido" + (f": ahora clic en {siguiente}" if siguiente else ""), 6)

    cv2.namedWindow(VENTANA, cv2.WINDOW_AUTOSIZE)
    cv2.setMouseCallback(VENTANA, al_clic)
    t_fps, n_fps = time.perf_counter(), 0
    ventana_mostrada = False
    while True:
        t_pedido = time.perf_counter()
        ok, img, t = cam.leer()
        t_espera_ms = (time.perf_counter() - t_pedido) * 1e3
        if robot is not None:
            robot.atender(sesion)
        if not ok:
            if cam.es_archivo:
                print("Fin del video.")
                break
            # Aún no llega un cuadro nuevo: atender la ventana igual (no congelar).
            if cam.segundos_sin_cuadro() > 2.0 and ultima_imagen["img"] is not None:
                panel.mensaje("Sin video: reconectando con DroidCam...", 1.0)
                cv2.imshow(VENTANA, panel.dibujar(ultima_imagen["img"].copy(), proc, estado))
            tecla = cv2.waitKey(1)
        else:
            if img.shape[1] != CC.ANCHO or img.shape[0] != CC.ALTO:
                img = cv2.resize(img, (CC.ANCHO, CC.ALTO))
            if espejo:
                img = cv2.flip(img, 1)
            ultima_imagen["img"] = img
            proc.procesar(img, t)
            panel.agregar(t, proc)

            n_fps += 1                            # FPS medidos (no supuestos)
            if t - t_fps >= 1.0:
                estado["fps"] = n_fps / (t - t_fps)
                t_fps, n_fps = t, 0

            # Enviar al robot
            theta = proc.theta_para_robot()
            cmd = modelo_a_servo(*theta) if theta is not None else None
            enviado = robot.enviar(cmd) if (robot is not None and estado["enviando"]) else False

            if sesion is not None:
                sesion.agregar(proc, t, estado["enviando"], cmd, enviado, t_espera_ms)
                dur = sesion.duracion_s(t)
                estado["sesion"] = (dur, guia_grabacion(dur), sesion.ruta.stem)
            if clics["pendientes"]:
                estado["pista"] = "Clic en " + clics["pendientes"][0].upper()
            else:
                estado["pista"] = "" if sesion is not None else pista(proc, robot, estado["enviando"])

            cv2.imshow(VENTANA, panel.dibujar(img.copy(), proc, estado))
            ventana_mostrada = True
            tecla = cv2.waitKey(1)

        # ¿Cerraron la ventana con la X?
        if ventana_mostrada and cv2.getWindowProperty(VENTANA, cv2.WND_PROP_VISIBLE) < 1:
            break
        if tecla < 0:
            continue
        tecla = chr(tecla & 0xFF).lower() if (tecla & 0xFF) < 128 else ""
        if tecla in ("q", "\x1b"):
            break
        elif tecla == "l" and proc.detector.modo == "color":
            clics["pendientes"] = list(CC.MARCADORES)
        elif tecla == "d":
            estado["diagnostico"] = not estado["diagnostico"]
            panel.mensaje("Diagnostico " + ("ON: rojo = cuadros que no se leen" if estado["diagnostico"]
                                            else "OFF"))
        elif tecla == "m":
            espejo = not espejo
            panel.mensaje(f"Espejo {'ON' if espejo else 'OFF'}: vuelve a pulsar C con el brazo al frente", 6)
        elif tecla == "c":
            panel.mensaje("Pose de referencia: ahora vale (90, 0)" if proc.calibrar_pose()
                          else "No veo los 3 marcadores: no se pudo calibrar")
        elif tecla == "n":
            proc.empezar_medir_ruido()
        elif tecla == "f":
            proc.fuente = "crudo" if proc.fuente == "kalman" else "kalman"
            panel.mensaje(f"El robot ahora se mueve con: {proc.fuente.upper()}")
        elif tecla in ("1", "2", "3"):
            proc.elegir_q(int(tecla) - 1)
            panel.mensaje(f"{proc.config['nombre']}: f_n = {proc.config['f_n_hz']:g} Hz "
                          f"({proc.config['razon']})", 5)
        elif tecla == "r":
            if robot is None:
                panel.mensaje("Sin robot: abre el programa con --puerto COMx (o auto)")
            else:
                estado["enviando"] = not estado["enviando"]
                if estado["enviando"]:
                    robot.empezar_a_enviar()
                panel.mensaje("Robot: COPIANDOTE (arranque suave)" if estado["enviando"] else "Robot en PAUSA")
        elif tecla == "g":
            if sesion is None:
                sesion = Sesion(proc, t0=time.perf_counter())
                panel.mensaje(f"Grabando {sesion.ruta.name}: sigue la guia de arriba", 3)
            else:
                ruta = sesion.cerrar()
                sesiones_grabadas.append(ruta)
                sesion, estado["sesion"] = None, None
                panel.mensaje(f"Guardado {ruta.name} ({len(sesiones_grabadas)} sesiones). Subiendo...", 5)
                import sincronizar
                subidas.append(sincronizar.subir_en_segundo_plano(
                    f"Teleoperación: {ruta.stem}", lambda m: print("[git]", m),
                    rutas=("datos/teleop",)))

    if sesion is not None:
        sesiones_grabadas.append(sesion.cerrar())
    print(f"Video: {cam.metodo}. Cuadros recibidos {cam.recibidos}, descartados por viejos "
          f"{cam.descartados}, reconexiones {cam.reconexiones}.")
    cam.cerrar()
    cv2.destroyAllWindows()
    if robot is not None:
        robot.cerrar()
    if sesiones_grabadas:
        _analizar_y_subir(subidas)


def _analizar_y_subir(subidas):
    """Al salir: analiza TODAS las sesiones reales y sube datos + resultados."""
    for hilo in subidas:
        hilo.join(timeout=60)                  # que termine la subida que iba en curso
    print("\nAnalizando las sesiones de teleoperación...")
    try:
        import analisis_teleop
        carpeta = analisis_teleop.analizar("reales")
        print(f"Resultados en {carpeta.relative_to(Rp.RAIZ)} (abre resumen_teleop.md)")
    except Exception as e:                      # el análisis nunca debe impedir subir los datos
        print(f"El análisis falló ({e}); los datos quedan guardados igual.")
    import sincronizar
    sincronizar.subir_capturas("Teleoperación: sesiones y resultados",
                               lambda m: print("[git]", m),
                               rutas=("datos/teleop", "resultados/reales/teleop"))


if __name__ == "__main__":
    main()
