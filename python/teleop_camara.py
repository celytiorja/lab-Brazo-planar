"""TELEOPERACIÓN CON CÁMARA — el robot copia tu brazo (Entrega 2, opción 1).

Requisitos:
  - Teléfono ARRIBA de la mesa, mirando hacia abajo, con la app DroidCam.
  - 3 marcadores en tu brazo: HOMBRO, CODO y MUÑECA. Por defecto son cuadros ArUco
    impresos (python python/generar_marcadores.py -> docs/marcadores_aruco.pdf).
    Con  --modo color  se usan papeles de color (respaldo).
  - ESP32 con firmware/adquisicion (para mover el robot) y el Monitor Serie CERRADO.

    python python/teleop_camara.py --video http://192.168.1.23:4747/video --puerto COM3
    python python/teleop_camara.py --video 0                    (webcam, sin robot)
    python python/teleop_camara.py --video 0 --modo color       (papeles de color)

Teclas (con la ventana de video activa):
  D  diagnóstico (solo ArUco): dibuja en rojo los cuadros que ve pero NO logra leer
  L  (solo modo color) aprender colores: clic en hombro, codo y muñeca, en ese orden
  C  pose de referencia: tu brazo ESTIRADO hacia adelante = robot en (90°, 0°)
  N  medir el ruido de la cámara: brazo QUIETO 10 s -> R del Kalman
  F  cambiar la fuente que mueve el robot: crudo (cámara) <-> Kalman
  1 2 3  Q_baja / Q_media / Q_alta
  R  ENVIAR al robot: activar / pausar (arranca en pausa, por seguridad)
  G  grabar la sesión: iniciar / detener (datos/teleop/, se sube a GitHub sola)
  Q o Esc  salir (si grabaste sesiones, se analizan y se suben solas)

Qué se guarda en cada sesión (datos/teleop/sesion_XX.csv, un renglón por cuadro):
  ángulos crudos y de Kalman, si se vieron los marcadores, la orden al robot, y los
  TIEMPOS medidos: cómputo de Kalman, detección + Kalman, espera del cuadro.
  Con robot, además  sesion_XX_robot.csv: el giroscopio del robot a 100 Hz (las IMU de
  la Entrega 1) -> se mide cuánto tarda el robot en moverse y cuánto vibra.
"""
import argparse
import csv
import json
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
from servos import modelo_a_servo
from tiempo_real import valores_a_fisico
from video_rapido import LectorVideo
from vision import angulos_brazo, crear_detector

CARPETA = Rp.RAIZ / "datos" / "teleop"
ARCHIVO_RUIDO = CARPETA / "ruido_camara.json"
CUADROS_RUIDO = 300                      # ~10 s a 30 cuadros/s
COLOR_DIBUJO = {"hombro": (255, 120, 0), "codo": (0, 200, 0), "muneca": (0, 0, 255)}


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
        self.reiniciar_kalman(np.array([90.0, 0.0]))
        return True

    def empezar_medir_ruido(self):
        self._ruido = []

    @property
    def midiendo_ruido(self):
        return self._ruido is not None

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
        if self.kalman is None:
            if medido is None:
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


def dibujar(img, proc, estado):
    det = proc.detector
    if det.modo == "aruco":
        if estado.get("diagnostico") and len(det.rechazados):
            # Cuadros que "parecen" marcador pero no se pudieron leer: muy pequeños,
            # borrosos, doblados o sin margen blanco alrededor.
            cv2.polylines(img, [np.int32(c).reshape(-1, 1, 2) for c in det.rechazados],
                          True, (0, 0, 255), 1)
        for n, c in det.esquinas.items():
            cv2.polylines(img, [np.int32(c).reshape(-1, 1, 2)], True, COLOR_DIBUJO[n], 2)
    for n in CC.MARCADORES:
        p = proc.pos.get(n)
        if p is not None:
            recordado = n == "hombro" and proc.hombro_recordado
            cv2.circle(img, (int(p[0]), int(p[1])), 9, COLOR_DIBUJO[n], 1 if recordado else 2)
            cv2.putText(img, n + (" (memoria)" if recordado else ""), (int(p[0]) + 12, int(p[1]) - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, COLOR_DIBUJO[n], 1)
    p = [proc.pos.get(n) for n in CC.MARCADORES]
    if all(x is not None for x in p):
        pts = [(int(x), int(y)) for x, y in p]
        cv2.polylines(img, [np.array(pts)], False, (0, 255, 255), 2)
    vistos = "  ".join(f"{n}:{'si' if proc.pos.get(n) is not None else 'NO'}" for n in CC.MARCADORES)
    lineas = [
        f"crudo:  t1={_g(proc.theta_crudo, 0)}  t2={_g(proc.theta_crudo, 1)}   "
        f"{'VISTO' if proc.visto else ('SOLO t1 (t2 predicho)' if proc.solo_theta1 else 'NO VISTO (Kalman predice)')}",
        f"kalman: t1={_g(proc.theta_kf, 0)}  t2={_g(proc.theta_kf, 1)}   "
        f"{proc.config['nombre']} (f_n={proc.config['f_n_hz']} Hz)",
        f"robot <- {proc.fuente.upper()}   {'ENVIANDO' if estado['enviando'] else 'PAUSA (R)'}   "
        f"{estado['fps']:.0f} fps   proceso {proc.t_proc_ms:.1f} ms   kalman {proc.t_calc_us:.0f} us",
        f"R camara: sigma = {np.sqrt(proc.r_camara[0]):.2f}, {np.sqrt(proc.r_camara[1]):.2f} deg "
        f"({proc.origen_r})",
        f"{det.modo}: {vistos}",
    ]
    if estado["msg"]:
        lineas.append(estado["msg"])
    if estado["grabando"]:
        lineas.append("REC  " + estado["grabando"])
    for i, texto in enumerate(lineas):
        _texto(img, texto, (8, 20 + 20 * i), 0.5)
    teclas = "L colores" if det.modo == "color" else "D diagnostico"
    _texto(img, f"{teclas}  C pose  N ruido  F fuente  1/2/3 Q  R robot  G grabar  Q salir",
           (8, img.shape[0] - 10), 0.45)


def _texto(img, texto, org, escala, color=(255, 255, 255)):
    """Texto con un rectángulo oscuro detrás: se lee sobre cualquier fondo."""
    (ancho, alto), base = cv2.getTextSize(texto, cv2.FONT_HERSHEY_SIMPLEX, escala, 1)
    x, y = org
    cv2.rectangle(img, (x - 3, y - alto - 3), (x + ancho + 3, y + base + 1), (0, 0, 0), -1)
    cv2.putText(img, texto, org, cv2.FONT_HERSHEY_SIMPLEX, escala, color, 1)


def _g(v, i):
    return "  --  " if v is None else f"{v[i]:6.1f}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--video", default=str(CC.FUENTE_VIDEO),
                    help="número de cámara (0, 1...) o URL de DroidCam (http://IP:4747/video)")
    ap.add_argument("--puerto", default="", help="puerto del ESP32 (p. ej. COM3); vacío = sin robot")
    ap.add_argument("--modo", default=CC.MODO_DETECCION, choices=["aruco", "color"],
                    help="marcadores: cuadros ArUco impresos (por defecto) o papeles de color")
    args = ap.parse_args()
    fuente = int(args.video) if args.video.isdigit() else args.video
    CC.FUENTE_VIDEO = fuente

    cam = LectorVideo(fuente)
    if not cam.abierto():
        pista = ""
        if isinstance(fuente, str) and fuente.startswith("http") and fuente.count(":") < 2:
            pista = ("\n  -> Falta el PUERTO. DroidCam usa el 4747: "
                     f"{fuente.split('/video')[0]}:4747/video")
        raise SystemExit(f"No se pudo abrir el video {fuente!r}. ¿DroidCam abierto en el teléfono, "
                         f"los dos en la misma WiFi y el navegador CERRADO?{pista}")

    conexion = None
    if args.puerto:
        from conexion import ConexionESP32
        conexion = ConexionESP32()
        conexion.conectar(args.puerto, C.BAUDIOS_ADQUISICION)
        print(f"Conectado a {args.puerto}. El robot arranca en PAUSA: tecla R para enviar.")

    print(f"Video abierto con: {cam.metodo}")
    proc = ProcesadorCamara(args.modo)
    estado = {"enviando": False, "fps": 0.0, "msg": "", "grabando": "", "diagnostico": False}
    sesion = None
    sesiones_grabadas = []
    subidas = []
    transmision_pedida = False
    ultimo_cmd, t_ultimo_envio = None, 0.0
    clics = {"pendientes": [] if proc.detector_listo() else list(CC.MARCADORES)}
    ultima_imagen = {"img": None}

    def al_clic(evento, x, y, *_):
        if evento == cv2.EVENT_LBUTTONDOWN and clics["pendientes"] and ultima_imagen["img"] is not None:
            nombre = clics["pendientes"].pop(0)
            marcador = proc.detector.marcadores[nombre]
            marcador.aprender(ultima_imagen["img"], x, y)
            print(f"Color de {nombre} aprendido: HSV = {marcador.hsv}")

    cv2.namedWindow("Teleoperacion")
    cv2.setMouseCallback("Teleoperacion", al_clic)
    t_fps = time.perf_counter()
    n_fps = 0
    while True:
        t_pedido = time.perf_counter()
        ok, img, t = cam.leer()
        t_espera_ms = (time.perf_counter() - t_pedido) * 1e3
        if not ok:
            if cam.es_archivo:
                print("Fin del video.")
                break
            # Aún no llega un cuadro nuevo: atender la ventana y el robot igual (no congelar).
            if cam.segundos_sin_cuadro() > 2.0:
                estado["msg"] = "Sin video hace >2 s: ¿DroidCam abierto? ¿navegador cerrado?"
                if ultima_imagen["img"] is not None:
                    img_aviso = ultima_imagen["img"].copy()
                    dibujar(img_aviso, proc, estado)
                    cv2.imshow("Teleoperacion", img_aviso)
            if conexion is not None:
                conexion.leer_lineas()
            if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
                break
            continue
        if estado["msg"].startswith("Sin video"):
            estado["msg"] = ""                          # volvió el video
        if img.shape[1] != CC.ANCHO or img.shape[0] != CC.ALTO:
            img = cv2.resize(img, (CC.ANCHO, CC.ALTO))
        if CC.ESPEJO:
            img = cv2.flip(img, 1)
        ultima_imagen["img"] = img.copy()
        proc.procesar(img, t)

        # FPS medidos (no supuestos)
        n_fps += 1
        if t - t_fps >= 1.0:
            estado["fps"] = n_fps / (t - t_fps)
            t_fps, n_fps = t, 0

        if clics["pendientes"]:
            estado["msg"] = f"Haz clic en el marcador del {clics['pendientes'][0].upper()}"
        elif proc.midiendo_ruido:
            estado["msg"] = "Midiendo ruido de la camara: brazo QUIETO..."
        elif estado["msg"].startswith("Haz clic"):
            estado["msg"] = "Colores listos. Brazo estirado al frente y tecla C."
        elif proc.detector.modo == "aruco" and proc.theta_crudo is None:
            estado["msg"] = "Muestra los 3 cuadros: 0 hombro, 1 codo, 2 muneca"
        elif estado["msg"].startswith("Muestra"):
            estado["msg"] = "Te veo. Brazo estirado al frente y tecla C."

        # Enviar al robot
        cmd = None
        enviado = False
        theta = proc.theta_para_robot()
        if theta is not None:
            cmd = modelo_a_servo(*theta)
        if conexion is not None and conexion.listo:
            if not transmision_pedida:
                conexion.enviar("s 1")       # que el ESP32 mande su giroscopio (100 Hz)
                transmision_pedida = True
            if estado["enviando"] and cmd is not None:
                ahora = time.perf_counter()
                if decidir_envio(cmd, ultimo_cmd, ahora, t_ultimo_envio):
                    conexion.enviar_servos(*cmd)
                    ultimo_cmd, t_ultimo_envio = cmd, ahora
                    enviado = True
        if conexion is not None:
            t_rx = time.perf_counter()
            for linea in conexion.leer_lineas():
                v = parsear_linea_datos(linea)
                if v is not None and sesion is not None:
                    sesion.agregar_robot(t_rx, v)

        if sesion is not None:
            sesion.agregar(proc, t, estado["enviando"], cmd, enviado, t_espera_ms)
            dur = sesion.duracion_s(t)
            estado["grabando"] = f"{sesion.ruta.name}  {dur:4.1f} s   {guia_grabacion(dur)}"

        dibujar(img, proc, estado)
        cv2.imshow("Teleoperacion", img)
        tecla = cv2.waitKey(1) & 0xFF
        if tecla in (ord("q"), 27):
            break
        elif tecla == ord("l") and proc.detector.modo == "color":
            clics["pendientes"] = list(CC.MARCADORES)
        elif tecla == ord("d"):
            estado["diagnostico"] = not estado["diagnostico"]
        elif tecla == ord("c"):
            estado["msg"] = ("Pose de referencia guardada: ahora vale (90, 0)" if proc.calibrar_pose()
                             else "No veo los 3 marcadores")
        elif tecla == ord("n"):
            proc.empezar_medir_ruido()
        elif tecla == ord("f"):
            proc.fuente = "crudo" if proc.fuente == "kalman" else "kalman"
        elif tecla in (ord("1"), ord("2"), ord("3")):
            proc.elegir_q(tecla - ord("1"))
        elif tecla == ord("r"):
            estado["enviando"] = not estado["enviando"] and conexion is not None
        elif tecla == ord("g"):
            if sesion is None:
                sesion = Sesion(proc, t0=t)
            else:
                ruta = sesion.cerrar()
                sesiones_grabadas.append(ruta)
                sesion, estado["grabando"] = None, ""
                estado["msg"] = f"Guardado {ruta.name}"
                import sincronizar
                subidas.append(sincronizar.subir_en_segundo_plano(
                    f"Teleoperación: {ruta.stem}", lambda m: print("[git]", m),
                    rutas=("datos/teleop",)))

    if sesion is not None:
        sesiones_grabadas.append(sesion.cerrar())
    print(f"Video: {cam.metodo}. Cuadros recibidos {cam.recibidos}, descartados por viejos "
          f"{cam.descartados} (si son muchos, el PC no alcanza: es normal que bote algunos).")
    cam.cerrar()
    cv2.destroyAllWindows()
    if conexion is not None:
        try:
            conexion.enviar("s 0")
        except Exception:
            pass
        conexion.desconectar()
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
        print(f"Resultados en {carpeta.relative_to(Rp.RAIZ)}")
    except Exception as e:                      # el análisis nunca debe impedir subir los datos
        print(f"El análisis falló ({e}); los datos quedan guardados igual.")
    import sincronizar
    sincronizar.subir_capturas("Teleoperación: sesiones y resultados",
                               lambda m: print("[git]", m),
                               rutas=("datos/teleop", "resultados/reales/teleop"))


if __name__ == "__main__":
    main()
