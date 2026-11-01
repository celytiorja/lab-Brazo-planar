"""Procesamiento EN VIVO de las muestras que llegan del ESP32.

Usa EXACTAMENTE los mismos estimadores que el análisis offline (estimadores.py),
muestra por muestra. Así lo que se ve en pantalla es lo mismo que se analiza.
"""
import json
import time
from collections import deque

import numpy as np

import config_imu as C
import config_kalman as CK
import reporte as Rp
from estimadores import IntegracionDirecta, KalmanBrazo, MediaMovilIntegracion
from servos import servo_a_modelo

HISTORIA_S = 10.0          # segundos que se ven en las gráficas
MUESTRAS_CALIBRACION = 300 # 3 s a 100 Hz
_EJE = {"gx": 3, "gy": 4, "gz": 5}   # posición dentro de los 6 valores de cada IMU
_ACC = {"ax": 0, "ay": 1, "az": 2}


def cargar_R():
    """R de la Entrega 1 (datos reales si existen; si no, sintéticos; si no, típica)."""
    for origen in ("reales", "sinteticos"):
        ruta = Rp.RAIZ / "resultados" / origen / "e1" / "R.json"
        if ruta.exists():
            d = json.loads(ruta.read_text(encoding="utf-8"))
            return np.array(d["R"]), f"E1 {origen} ({d['archivo']})"
    return np.diag([0.06**2, 0.06**2]), "valor típico (aún no hay Entrega 1)"


def valores_a_fisico(v):
    """19 enteros de una línea D -> (t_us, cmd_h, cmd_c, w[2] °/s, phi_acc[2] ° o None)."""
    imu = {1: v[7:13], 2: v[13:19]}
    # Orden dentro de cada IMU: ax ay az gx gy gz.
    w = np.array([C.EJE_GIRO[i][1] * imu[i][_EJE[C.EJE_GIRO[i][0]]] / C.GYRO_LSB_POR_DPS
                  for i in (1, 2)])
    phi_acc = None
    if C.PLANO_VERTICAL:
        phi_acc = []
        for i in (1, 2):
            (ea, sa), (eb, sb) = C.EJES_INCLINACION[i]
            a = sa * imu[i][_ACC[ea]] / C.ACC_LSB_POR_G
            b = sb * imu[i][_ACC[eb]] / C.ACC_LSB_POR_G
            phi_acc.append(np.degrees(np.arctan2(a, b)) + C.OFFSET_INCLINACION_DEG[i])
        phi_acc = np.array(phi_acc)
    return v[1], v[5], v[6], w, phi_acc


class ProcesadorTiempoReal:
    def __init__(self, config_q_nombre=None):
        self.R, self.origen_R = cargar_R()
        self.usar_incl = self.R.shape[0] == 4 and C.PLANO_VERTICAL
        if self.R.shape[0] == 4 and not self.usar_incl:
            self.R = self.R[:2, :2]
        self.est_bias = self.usar_incl and CK.ESTIMAR_BIAS_SI_HAY_INCLINACION
        self.configs = [CK.resolver_q(c, self.R, 1 / C.FS_HZ) for c in CK.CONFIGS_Q]
        self.config_q = next((c for c in self.configs if c["nombre"] == config_q_nombre),
                             self.configs[1])
        self.bias = np.zeros(2)
        self.calibrado = False
        self._calib = None
        self._t_us_ant = None
        self._seq_ant = None
        self.perdidas = 0
        self.t = 0.0
        self.t_calc_kalman = deque(maxlen=200)
        self.dts = deque(maxlen=200)
        n = int(HISTORIA_S * C.FS_HZ)
        self.hist = {k: deque(maxlen=n) for k in
                     ("t", "w1", "w2", "wk1", "wk2", "cmd1", "cmd2",
                      "dir1", "dir2", "mm1", "mm2", "kf1", "kf2")}
        self.ultimo = None
        self.reiniciar(np.zeros(2))

    # ---------- Estimadores ----------
    def reiniciar(self, phi0):
        """Mismas condiciones iniciales (φ0, sesgo) para los tres métodos."""
        self.directa = IntegracionDirecta(phi0, self.bias)
        self.media = MediaMovilIntegracion(phi0, self.bias, CK.VENTANAS_MEDIA_MOVIL[0])
        self.kalman = KalmanBrazo(phi0, self.bias, self.R, self.config_q["q"],
                                  self.usar_incl, self.est_bias,
                                  nombre=f"Kalman {self.config_q['nombre']}")

    def cambiar_q(self, nombre):
        self.config_q = next(c for c in self.configs if c["nombre"] == nombre)
        phi = self.kalman.kf.x[self.kalman.idx["phi"]].copy()
        self.kalman = KalmanBrazo(phi, self.bias, self.R, self.config_q["q"],
                                  self.usar_incl, self.est_bias,
                                  nombre=f"Kalman {self.config_q['nombre']}")

    def empezar_calibracion(self):
        self._calib = []

    @property
    def calibrando(self):
        return self._calib is not None

    # ---------- Una muestra ----------
    def procesar(self, v):
        t_us, cmd_h, cmd_c, w, phi_acc = valores_a_fisico(v)
        seq = v[0]
        if self._seq_ant is not None and seq > self._seq_ant + 1:
            self.perdidas += seq - self._seq_ant - 1
        self._seq_ant = seq
        theta_cmd = np.array(servo_a_modelo(cmd_h, cmd_c))
        phi_cmd = np.array([theta_cmd[0], theta_cmd[0] + theta_cmd[1]])

        if self._t_us_ant is None:
            dt = 0.0
        else:
            dt = ((t_us - self._t_us_ant) % 2**32) / 1e6   # micros() se desborda a los 71 min
        self._t_us_ant = t_us
        if dt > 0.5:            # hueco grande (reconexión): no integrar a ciegas
            dt = 0.0
        self.t += dt
        if dt > 0:
            self.dts.append(dt)

        if self._calib is not None:
            self._calib.append(w)
            if len(self._calib) >= MUESTRAS_CALIBRACION:
                self.bias = np.mean(self._calib, axis=0)
                self._calib = None
                self.calibrado = True
                self.reiniciar(phi_cmd)   # pose de partida = la que tiene el brazo ahora

        if dt > 0:
            phi_d, _ = self.directa.paso(dt, w, phi_acc)
            phi_m, _ = self.media.paso(dt, w, phi_acc)
            t0 = time.perf_counter()
            phi_k, w_k = self.kalman.paso(dt, w, phi_acc)
            self.t_calc_kalman.append((time.perf_counter() - t0) * 1e6)
        else:
            phi_d = self.directa.phi
            phi_m = self.media.phi
            phi_k = self.kalman.kf.x[self.kalman.idx["phi"]]
            w_k = self.kalman.kf.x[self.kalman.idx["omega"]]

        th = {k: np.array([p[0], p[1] - p[0]]) for k, p in
              (("dir", phi_d), ("mm", phi_m), ("kf", phi_k))}
        h = self.hist
        h["t"].append(self.t)
        for i in (0, 1):
            h[f"w{i+1}"].append(w[i] - self.bias[i])
            h[f"wk{i+1}"].append(w_k[i])
            h[f"cmd{i+1}"].append(theta_cmd[i])
            for k in ("dir", "mm", "kf"):
                h[f"{k}{i+1}"].append(th[k][i])
        self.ultimo = {"theta_cmd": theta_cmd, **{k: th[k] for k in th}, "perfil": v[3],
                       "fase": v[4]}
        return self.ultimo

    # ---------- Para mostrar ----------
    def estadisticas(self):
        dts = np.array(self.dts) if self.dts else np.array([np.nan])
        tk = np.array(self.t_calc_kalman) if self.t_calc_kalman else np.array([np.nan])
        return {"fs": 1 / np.mean(dts), "jitter_us": np.std(dts) * 1e6,
                "perdidas": self.perdidas, "t_kalman_us": np.mean(tk),
                "t_kalman_max_us": np.max(tk)}
