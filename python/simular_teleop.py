"""Prueba COMPLETA de la teleoperación sin cámara ni robot (datos SINTÉTICOS).

    python python/simular_teleop.py            (crea sesiones y las analiza)
    python python/simular_teleop.py --video    (además guarda el video .mp4 para verlo con
                                                teleop_camara.py --video <archivo>)

Qué hace:
  1. Dibuja un video de 30 cuadros/s visto desde arriba: un brazo (color piel) con los
     3 cuadros ArUco en hombro, codo y muñeca, sobre una mesa con textura, luz desigual,
     ruido de sensor, compresión JPEG (como DroidCam), DESENFOQUE de movimiento, el
     TEMBLOR natural del brazo (~9 Hz, ±0.4°) y una mano que TAPA la muñeca dos veces.
     Los ángulos verdaderos (movimiento voluntario, sin temblor) se conocen: es la
     "verdad" que una cámara real no da.
  2. Pasa cada cuadro por el MISMO ProcesadorCamara de teleop_camara.py (detección
     ArUco + Kalman), mide R de la cámara con 10 s quieto (como la tecla N) y graba dos
     sesiones: una moviendo el "robot" con crudo y otra con Kalman.
  3. Simula el robot (servo con retraso y respuesta de 1.er orden) y su giroscopio a
     100 Hz, para probar el análisis de retrasos y vibración.
  4. Corre analisis_teleop.py --sinteticos.

TODO se guarda en datos/sinteticos/teleop y resultados/sinteticos/teleop, marcado como
sintético. Nunca presentarlo como medición.
"""
import argparse
import math

import cv2
import numpy as np

import config_camara as CC
import reporte as Rp
from generar_marcadores import imagen_marcador
from servos import servo_a_modelo

CARPETA = Rp.RAIZ / "datos" / "sinteticos" / "teleop"
FPS = 30.0
ANCHO, ALTO = CC.ANCHO, CC.ALTO
HOMBRO_PX = np.array([320.0, 430.0])
L1_PX, L2_PX = 170.0, 150.0          # brazo y antebrazo vistos desde arriba
LADO_PX = 34                          # cuadro de 6 cm a ~70 cm de la cámara
T_QUIETO = 10.0                       # para medir R (tecla N)
T_SESION = 30.0                       # protocolo: 10 s lento, 10 s rápido, 10 s oclusión
OCLUSIONES = [(22.5, 23.7), (26.0, 27.0)]       # en tiempo de sesión [s]
TEMBLOR_DEG, TEMBLOR_HZ = 0.4, 9.0   # temblor fisiológico (el robot NO debería copiarlo)
EXPOSICION_S = 0.010
CALIDAD_JPEG = 70
RETRASO_SERVO_S = 0.12
TAU_SERVO_S = 0.07
SEMILLA = 7


def trayectoria(ts):
    """Ángulos verdaderos (θ1, θ2) en el tiempo de sesión ts (antes de 0: quieto)."""
    if ts < 0:
        return 90.0, 30.0
    if ts < 10:                                         # lento, 0.25 Hz
        a = math.sin(2 * math.pi * 0.25 * ts)
        return 90 + 25 * a, 30 + 25 * math.sin(2 * math.pi * 0.25 * ts + 0.8)
    if ts < 20:                                         # rápido, 0.7 Hz (~0.8 m/s en la muñeca)
        u = ts - 10
        return 90 + 15 * math.sin(2 * math.pi * 0.7 * u), 30 + 18 * math.sin(2 * math.pi * 0.7 * u + 0.6)
    u = ts - 20                                         # lento con oclusiones
    return 90 + 20 * math.sin(2 * math.pi * 0.35 * u), 30 + 20 * math.sin(2 * math.pi * 0.35 * u + 1.0)


def posiciones(th1, th2):
    """Píxeles de hombro, codo y muñeca (y hacia abajo en la imagen)."""
    a1 = math.radians(th1)
    a2 = math.radians(th1 + th2)
    codo = HOMBRO_PX + L1_PX * np.array([math.cos(a1), -math.sin(a1)])
    muneca = codo + L2_PX * np.array([math.cos(a2), -math.sin(a2)])
    return HOMBRO_PX, codo, muneca, a1, a2


class Escena:
    def __init__(self, rng):
        mesa = rng.normal(0, 1, (ALTO // 8, ANCHO // 8))
        mesa = cv2.resize(mesa, (ANCHO, ALTO), interpolation=cv2.INTER_CUBIC)
        base = np.stack([95 + 12 * mesa, 125 + 14 * mesa, 160 + 16 * mesa], axis=-1)   # madera
        gx = np.linspace(0.75, 1.15, ANCHO)[None, :, None]                            # luz desigual
        self.fondo = np.clip(base * gx, 0, 255).astype(np.float32)
        self.rng = rng
        self.cuadros = {}
        for n, i in CC.ARUCO_IDS.items():
            m = cv2.resize(imagen_marcador(i), (LADO_PX, LADO_PX), interpolation=cv2.INTER_NEAREST)
            b = LADO_PX // 6
            self.cuadros[n] = cv2.copyMakeBorder(m, b, b, b, b, cv2.BORDER_CONSTANT, value=255)

    def _pegar(self, img, parche, centro, angulo_rad):
        """Pega el cuadro girado SOLO en un recorte alrededor de su centro (rápido)."""
        h, w = parche.shape
        r = int(math.ceil(math.hypot(w, h) / 2)) + 2
        cx, cy = int(round(centro[0])), int(round(centro[1]))
        x0, y0 = max(cx - r, 0), max(cy - r, 0)
        x1, y1 = min(cx + r, ANCHO), min(cy + r, ALTO)
        if x1 <= x0 or y1 <= y0:
            return
        M = cv2.getRotationMatrix2D((w / 2, h / 2), math.degrees(angulo_rad), 1.0)
        M[:, 2] += np.array([centro[0] - x0, centro[1] - y0]) - np.array([w / 2, h / 2])
        tam = (x1 - x0, y1 - y0)
        rot = cv2.warpAffine(parche.astype(np.float32), M, tam, flags=cv2.INTER_LINEAR)
        mascara = cv2.warpAffine(np.ones_like(parche, np.float32), M, tam, flags=cv2.INTER_LINEAR)
        roi = img[y0:y1, x0:x1]
        roi[:] = roi * (1 - mascara[..., None]) + rot[..., None]

    def dibujar(self, th1, th2, tapar_muneca):
        img = self.fondo.copy()
        h, c, m, a1, a2 = posiciones(th1, th2)
        piel = (120, 160, 210)
        cv2.line(img, tuple(np.int32(h)), tuple(np.int32(c)), piel, 46, cv2.LINE_AA)
        cv2.line(img, tuple(np.int32(c)), tuple(np.int32(m)), piel, 38, cv2.LINE_AA)
        cv2.circle(img, tuple(np.int32(h)), 34, (90, 70, 60), -1, cv2.LINE_AA)     # camiseta
        for nombre, p, a in (("hombro", h, a1), ("codo", c, a1), ("muneca", m, a2)):
            self._pegar(img, self.cuadros[nombre], p, a)
        if tapar_muneca:
            cv2.ellipse(img, tuple(np.int32(m + [10, -6])), (44, 32), 30, 0, 360, (110, 150, 205), -1)
        return img

    def temblor(self, t):
        """Temblor fisiológico: pequeño, rápido, distinto en cada articulación."""
        return (TEMBLOR_DEG * math.sin(2 * math.pi * TEMBLOR_HZ * t),
                TEMBLOR_DEG * math.sin(2 * math.pi * (TEMBLOR_HZ * 1.13) * t + 1.0))

    def cuadro(self, t_sesion, n_sub=6):
        """Promedio de n_sub poses durante la exposición -> desenfoque de movimiento."""
        tapar = any(a <= t_sesion < b for a, b in OCLUSIONES)
        acum = np.zeros((ALTO, ANCHO, 3), np.float32)
        for k in range(n_sub):
            tk = t_sesion - EXPOSICION_S * k / (n_sub - 1)
            th1, th2 = trayectoria(tk)
            d1, d2 = self.temblor(tk)
            acum += self.dibujar(th1 + d1, th2 + d2, tapar)
        img = acum / n_sub + self.rng.normal(0, 4, acum.shape)                     # ruido
        img = np.clip(img, 0, 255).astype(np.uint8)
        jpg = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, CALIDAD_JPEG])[1]  # como DroidCam
        return cv2.imdecode(jpg, cv2.IMREAD_COLOR)


def correr_sesiones(guardar_video=False, rng=None, t_sesion=T_SESION):
    """El MISMO video se procesa dos veces a la vez: robot movido con crudo y con Kalman."""
    from servos import modelo_a_servo
    from teleop_camara import ProcesadorCamara, Sesion, decidir_envio
    rng = rng or np.random.default_rng(SEMILLA)
    CARPETA.mkdir(parents=True, exist_ok=True)
    for viejo in CARPETA.glob("sesion_*"):
        viejo.unlink()
    escena = Escena(rng)
    video = None
    if guardar_video:
        video = cv2.VideoWriter(str(CARPETA / "video_sintetico.mp4"), cv2.VideoWriter_fourcc(*"mp4v"),
                                FPS, (ANCHO, ALTO))
    fuentes = ("crudo", "kalman")
    procs, sesiones, envio = {}, {}, {}
    for f in fuentes:
        procs[f] = ProcesadorCamara("aruco", archivo_ruido=CARPETA / "ruido_camara.json")
        procs[f].fuente = f
        procs[f].empezar_medir_ruido()               # 10 s quieto = tecla N
        envio[f] = (None, -1e9)
    n_total = int((T_QUIETO + t_sesion) * FPS)
    jitter = rng.normal(0, 0.004, n_total)           # Δt irregular de la WiFi
    for k in range(n_total):
        t = k / FPS + jitter[k]
        ts = t - T_QUIETO
        img = escena.cuadro(ts)
        if video is not None:
            video.write(img)
        for f in fuentes:
            proc = procs[f]
            proc.procesar(img, t)
            if ts < 0:
                continue
            if f not in sesiones:
                sesiones[f] = Sesion(proc, carpeta=CARPETA, t0=t)
                sesiones[f].verdad = []
            theta = proc.theta_para_robot()
            enviado, cmd = False, None
            if theta is not None:
                cmd = modelo_a_servo(*theta)
                ultimo, t_ult = envio[f]
                if decidir_envio(cmd, ultimo, t, t_ult):
                    envio[f] = (cmd, t)
                    enviado = True
            sesiones[f].agregar(proc, t, True, cmd, enviado, 0.0)
            sesiones[f].verdad.append(trayectoria(ts))
    for f in fuentes:
        sesiones[f].cerrar()
        _agregar_verdad(sesiones[f])
        _simular_robot(sesiones[f], rng)
    if video is not None:
        video.release()
    return [sesiones[f].ruta for f in fuentes]


def _agregar_verdad(sesion):
    import pandas as pd
    df = pd.read_csv(sesion.ruta)
    v = np.array(sesion.verdad)
    df["theta1_verdad"], df["theta2_verdad"] = v[:, 0], v[:, 1]
    df.to_csv(sesion.ruta, index=False, float_format="%.4f")
    import json
    meta = json.loads(sesion.ruta.with_suffix(".json").read_text(encoding="utf-8"))
    meta["SINTETICO"] = "Video generado por simular_teleop.py: NO es una medición."
    sesion.ruta.with_suffix(".json").write_text(json.dumps(meta, indent=2, ensure_ascii=False),
                                                encoding="utf-8")


def _simular_robot(sesion, rng):
    """Servo: retraso + 1.er orden hacia la última orden; giroscopio a 100 Hz con ruido y sesgo."""
    import pandas as pd
    df = pd.read_csv(sesion.ruta)
    env = df[df["enviado"] == 1]
    t_cmd = env["t_s"].to_numpy()
    th_cmd = np.array([servo_a_modelo(h, c) for h, c in zip(env["cmd_h"], env["cmd_c"])])
    dt = 0.01
    tr = np.arange(0, df["t_s"].iloc[-1], dt)
    th = np.zeros((len(tr), 2))
    th[0] = th_cmd[0]
    for k in range(1, len(tr)):
        i = np.searchsorted(t_cmd, tr[k] - RETRASO_SERVO_S, side="right") - 1
        objetivo = th_cmd[max(i, 0)]
        th[k] = th[k - 1] + (objetivo - th[k - 1]) * (dt / TAU_SERVO_S)
    phi = np.column_stack([th[:, 0], th[:, 0] + th[:, 1]])         # ángulos absolutos (IMU)
    w = np.gradient(phi, dt, axis=0) + rng.normal(0, 0.03, phi.shape) + np.array([0.26, -0.50])
    t_pc = tr + rng.uniform(0.0, 0.004, len(tr))                    # llegada al PC
    out = pd.DataFrame({"t_s": t_pc, "seq": np.arange(len(tr)), "t1_us": (tr * 1e6).astype(int),
                        "w1_dps": w[:, 0], "w2_dps": w[:, 1]})
    out.to_csv(sesion.ruta_robot, index=False, float_format="%.4f")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--video", action="store_true", help="guardar también el video .mp4")
    args = ap.parse_args()
    rutas = correr_sesiones(args.video)
    print("Sesiones sintéticas:", ", ".join(r.name for r in rutas))
    import analisis_teleop
    carpeta = analisis_teleop.analizar("sinteticos")
    print((carpeta / "resumen_teleop.md").read_text(encoding="utf-8"))
    if args.video:
        print(f"Video: {(CARPETA / 'video_sintetico.mp4').relative_to(Rp.RAIZ)}")


if __name__ == "__main__":
    main()
