"""TELEOPERACIÓN CON CÁMARA — el robot copia tu brazo (Entrega 2, opción 1).

Requisitos:
  - Teléfono ARRIBA de la mesa, mirando hacia abajo, con la app DroidCam.
  - 3 marcadores de color en tu brazo: HOMBRO, CODO y MUÑECA (colores distintos).
  - ESP32 con firmware/adquisicion (para mover el robot) y el Monitor Serie CERRADO.

    python python/teleop_camara.py --video http://192.168.1.23:4747/video --puerto COM3
    python python/teleop_camara.py --video 0                    (webcam, sin robot)

Teclas (con la ventana de video activa):
  L  aprender colores: haz clic en hombro, codo y muñeca, en ese orden
  C  pose de referencia: tu brazo ESTIRADO hacia adelante = robot en (90°, 0°)
  N  medir el ruido de la cámara: brazo QUIETO 10 s -> R del Kalman
  F  cambiar la fuente que mueve el robot: crudo (cámara) <-> Kalman
  1 2 3  Q_baja / Q_media / Q_alta
  R  ENVIAR al robot: activar / pausar (arranca en pausa, por seguridad)
  G  grabar la sesión: iniciar / detener (datos/teleop/, se sube a GitHub sola)
  Q o Esc  salir
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
from kalman_camara import KalmanCamara
from servos import modelo_a_servo
from vision import Marcador, angulos_brazo

CARPETA = Rp.RAIZ / "datos" / "teleop"
ARCHIVO_RUIDO = CARPETA / "ruido_camara.json"
CUADROS_RUIDO = 300                      # ~10 s a 30 cuadros/s
COLOR_DIBUJO = {"hombro": (255, 120, 0), "codo": (0, 200, 0), "muneca": (0, 0, 255)}


class ProcesadorCamara:
    """Todo lo que pasa con cada cuadro, separado de la ventana (así se puede probar)."""

    def __init__(self):
        CARPETA.mkdir(parents=True, exist_ok=True)
        self.marcadores = {n: Marcador(n) for n in CC.MARCADORES}
        self.offset = np.zeros(2)
        self.r_camara = np.array([CC.R_CAMARA_POR_DEFECTO] * 2)
        self.origen_r = "valor por defecto (aún no medido: tecla N)"
        if ARCHIVO_RUIDO.exists():
            d = json.loads(ARCHIVO_RUIDO.read_text(encoding="utf-8"))
            self.r_camara = np.array(d["r_camara"])
            self.origen_r = f"medido {d['fecha']}"
        self.i_config = 1                                  # Q_media
        self.kalman = None
        self.fuente = "kalman"
        self.t_ant = None
        self.theta_crudo = None
        self.theta_kf = None
        self.visto = False
        self.t_calc_us = 0.0
        self._ruido = None

    @property
    def config(self):
        return CC.CONFIGS_Q_CAMARA[self.i_config]

    def colores_listos(self):
        return all(m.calibrado for m in self.marcadores.values())

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
        dt = 0.0 if self.t_ant is None else t - self.t_ant
        self.t_ant = t
        hsv = cv2.cvtColor(imagen_bgr, cv2.COLOR_BGR2HSV)
        pos = {n: m.buscar(hsv) for n, m in self.marcadores.items()}
        self.visto = all(p is not None for p in pos.values())
        medido = None
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
            self.theta_kf, _ = self.kalman.paso(dt, medido)
        else:
            self.theta_kf = np.array([self.kalman.kf.x[0], self.kalman.kf.x[2]])
        self.t_calc_us = (time.perf_counter() - t0) * 1e6
        return self.visto

    def _terminar_ruido(self):
        datos = np.array(self._ruido)
        self._ruido = None
        self.r_camara = np.var(datos, axis=0, ddof=1)
        fecha = datetime.now().isoformat(timespec="seconds")
        self.origen_r = f"medido {fecha}"
        ARCHIVO_RUIDO.write_text(json.dumps({
            "r_camara": self.r_camara.tolist(), "sigma_deg": np.sqrt(self.r_camara).tolist(),
            "media_deg": datos.mean(axis=0).tolist(), "cuadros": len(datos), "fecha": fecha},
            indent=2), encoding="utf-8")
        self.reiniciar_kalman(self.theta_kf if self.theta_kf is not None else datos[-1])

    def theta_para_robot(self):
        return self.theta_kf if self.fuente == "kalman" else self.theta_crudo


class Sesion:
    """Grabación de una sesión de teleoperación (para medir crudo vs Kalman)."""
    COLUMNAS = ["t_s", "visto", "theta1_crudo", "theta2_crudo", "theta1_kf", "theta2_kf",
                "fuente", "enviando", "cmd_h", "cmd_c", "t_calc_kf_us"]

    def __init__(self, proc):
        n = max([int(p.stem.split("_")[1]) for p in CARPETA.glob("sesion_*.csv")] + [0]) + 1
        self.ruta = CARPETA / f"sesion_{n:02d}.csv"
        self._f = open(self.ruta, "w", newline="", encoding="utf-8")
        self._w = csv.writer(self._f)
        self._w.writerow(self.COLUMNAS)
        self.t0 = time.perf_counter()
        self.meta = {"fecha": datetime.now().isoformat(timespec="seconds"),
                     "r_camara": proc.r_camara.tolist(), "origen_r": proc.origen_r,
                     "configs_q": CC.CONFIGS_Q_CAMARA, "offset": proc.offset.tolist(),
                     "fuente_video": str(CC.FUENTE_VIDEO), "commit": Rp.commit_actual()}
        self.filas = 0

    def agregar(self, proc, enviando, cmd):
        def f(v, i):
            return "" if v is None else f"{v[i]:.3f}"
        self._w.writerow([f"{time.perf_counter() - self.t0:.4f}", int(proc.visto),
                          f(proc.theta_crudo, 0), f(proc.theta_crudo, 1),
                          f(proc.theta_kf, 0), f(proc.theta_kf, 1),
                          f"{proc.fuente}:{proc.config['nombre']}", int(enviando),
                          "" if cmd is None else cmd[0], "" if cmd is None else cmd[1],
                          f"{proc.t_calc_us:.1f}"])
        self.filas += 1

    def cerrar(self):
        self._f.close()
        self.ruta.with_suffix(".json").write_text(json.dumps(self.meta, indent=2, ensure_ascii=False),
                                                  encoding="utf-8")
        return self.ruta


def dibujar(img, proc, estado):
    for n, m in proc.marcadores.items():
        if m.pos is not None:
            cv2.circle(img, (int(m.pos[0]), int(m.pos[1])), 9, COLOR_DIBUJO[n], 2)
    p = [proc.marcadores[n].pos for n in CC.MARCADORES]
    if all(x is not None for x in p):
        pts = [(int(x), int(y)) for x, y in p]
        cv2.polylines(img, [np.array(pts)], False, (0, 255, 255), 2)
    lineas = [
        f"crudo:  t1={_g(proc.theta_crudo, 0)}  t2={_g(proc.theta_crudo, 1)}   "
        f"{'VISTO' if proc.visto else 'NO VISTO (Kalman predice)'}",
        f"kalman: t1={_g(proc.theta_kf, 0)}  t2={_g(proc.theta_kf, 1)}   "
        f"{proc.config['nombre']} (f_n={proc.config['f_n_hz']} Hz)",
        f"robot <- {proc.fuente.upper()}   {'ENVIANDO' if estado['enviando'] else 'PAUSA (R)'}   "
        f"{estado['fps']:.0f} fps   kalman {proc.t_calc_us:.0f} us",
        f"R camara: sigma = {np.sqrt(proc.r_camara[0]):.2f}, {np.sqrt(proc.r_camara[1]):.2f} deg "
        f"({proc.origen_r})",
    ]
    if estado["msg"]:
        lineas.append(estado["msg"])
    if estado["grabando"]:
        lineas.append("REC  " + estado["grabando"])
    for i, texto in enumerate(lineas):
        cv2.putText(img, texto, (8, 20 + 20 * i), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 3)
        cv2.putText(img, texto, (8, 20 + 20 * i), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.putText(img, "L colores  C pose  N ruido  F fuente  1/2/3 Q  R robot  G grabar  Q salir",
                (8, img.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)


def _g(v, i):
    return "  --  " if v is None else f"{v[i]:6.1f}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--video", default=str(CC.FUENTE_VIDEO),
                    help="número de cámara (0, 1...) o URL de DroidCam (http://IP:4747/video)")
    ap.add_argument("--puerto", default="", help="puerto del ESP32 (p. ej. COM3); vacío = sin robot")
    args = ap.parse_args()
    fuente = int(args.video) if args.video.isdigit() else args.video
    CC.FUENTE_VIDEO = fuente

    cam = cv2.VideoCapture(fuente)
    if not cam.isOpened():
        pista = ""
        if isinstance(fuente, str) and fuente.startswith("http") and fuente.count(":") < 2:
            pista = ("\n  -> Falta el PUERTO. DroidCam usa el 4747: "
                     f"{fuente.split('/video')[0]}:4747/video")
        raise SystemExit(f"No se pudo abrir el video {fuente!r}. ¿DroidCam abierto en el teléfono "
                         f"y los dos en la misma WiFi?{pista}")

    conexion = None
    if args.puerto:
        from conexion import ConexionESP32
        conexion = ConexionESP32()
        conexion.conectar(args.puerto, C.BAUDIOS_ADQUISICION)
        print(f"Conectado a {args.puerto}. El robot arranca en PAUSA: tecla R para enviar.")

    proc = ProcesadorCamara()
    estado = {"enviando": False, "fps": 0.0, "msg": "", "grabando": ""}
    sesion = None
    ultimo_cmd, t_ultimo_envio = None, 0.0
    clics = {"pendientes": [] if proc.colores_listos() else list(CC.MARCADORES)}
    ultima_imagen = {"img": None}

    def al_clic(evento, x, y, *_):
        if evento == cv2.EVENT_LBUTTONDOWN and clics["pendientes"] and ultima_imagen["img"] is not None:
            nombre = clics["pendientes"].pop(0)
            proc.marcadores[nombre].aprender(ultima_imagen["img"], x, y)
            print(f"Color de {nombre} aprendido: HSV = {proc.marcadores[nombre].hsv}")

    cv2.namedWindow("Teleoperacion")
    cv2.setMouseCallback("Teleoperacion", al_clic)
    t_fps = time.perf_counter()
    n_fps = 0
    while True:
        ok, img = cam.read()
        if not ok:
            estado["msg"] = "Sin video (reintentando)..."
            if cv2.waitKey(30) & 0xFF in (ord("q"), 27):
                break
            continue
        img = cv2.resize(img, (CC.ANCHO, CC.ALTO))
        if CC.ESPEJO:
            img = cv2.flip(img, 1)
        ultima_imagen["img"] = img.copy()
        t = time.perf_counter()
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

        # Enviar al robot
        cmd = None
        theta = proc.theta_para_robot()
        if theta is not None:
            cmd = modelo_a_servo(*theta)
        if conexion is not None and conexion.listo and estado["enviando"] and cmd is not None:
            cambio = ultimo_cmd is None or max(abs(cmd[0] - ultimo_cmd[0]),
                                               abs(cmd[1] - ultimo_cmd[1])) >= CC.CAMBIO_MIN_GRADOS
            if cambio and t - t_ultimo_envio >= CC.PERIODO_ORDENES_S:
                conexion.enviar_servos(*cmd)
                ultimo_cmd, t_ultimo_envio = cmd, t
        if conexion is not None:
            conexion.leer_lineas()          # vaciar lo que mande el ESP32

        if sesion is not None:
            sesion.agregar(proc, estado["enviando"], cmd)
            estado["grabando"] = f"{sesion.ruta.name}  ({sesion.filas} cuadros)"

        dibujar(img, proc, estado)
        cv2.imshow("Teleoperacion", img)
        tecla = cv2.waitKey(1) & 0xFF
        if tecla in (ord("q"), 27):
            break
        elif tecla == ord("l"):
            clics["pendientes"] = list(CC.MARCADORES)
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
                sesion = Sesion(proc)
            else:
                ruta = sesion.cerrar()
                sesion, estado["grabando"] = None, ""
                estado["msg"] = f"Guardado {ruta.name}"
                import sincronizar
                sincronizar.subir_en_segundo_plano(f"Teleoperación: {ruta.stem}",
                                                   lambda m: print("[git]", m),
                                                   rutas=("datos/teleop",))

    if sesion is not None:
        sesion.cerrar()
    cam.release()
    cv2.destroyAllWindows()
    if conexion is not None:
        conexion.desconectar()


if __name__ == "__main__":
    main()
