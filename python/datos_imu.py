"""Cargar una captura (CSV crudo + JSON de configuración) y pasarla a unidades físicas.

Uso:
    reg = cargar("datos/crudos/escalones_01.csv")
    reg.t        tiempo [s] desde la primera muestra (de los timestamps del ESP32)
    reg.dt       Δt_k real entre muestras [s]  (dt[0] = 0)
    reg.w        velocidad angular en el plano, bias SIN quitar [°/s], forma (n, 2)
    reg.phi_cmd  ángulo absoluto de cada eslabón según la CONSIGNA [°], forma (n, 2)
    reg.phi_acc  ángulo por inclinación (solo si plano vertical) [°], forma (n, 2)
"""
import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

import config_imu as C
import parametros as P


@dataclass
class Registro:
    nombre: str
    crudo: pd.DataFrame          # columnas tal como llegaron del ESP32 (cuentas)
    meta: dict
    t: np.ndarray
    dt: np.ndarray
    fase: np.ndarray
    perfil: np.ndarray
    w: np.ndarray
    acc: dict                    # {1: (n,3) en g, 2: (n,3) en g}
    gyro: dict                   # {1: (n,3) en °/s, 2: (n,3) en °/s}
    theta_cmd: np.ndarray        # (n, 2) θ1, θ2 de la consigna
    phi_cmd: np.ndarray          # (n, 2) φ1 = θ1, φ2 = θ1 + θ2
    phi_acc: np.ndarray = None
    perdidas: int = 0
    sintetico: bool = False
    t2_menos_t1_us: np.ndarray = field(default=None)

    @property
    def n(self):
        return len(self.t)

    def mascara_fase(self, f):
        return self.fase == f


def _desenrollar_us(t_us):
    """micros() del ESP32 vuelve a 0 cada 2^32 µs (~71 min). Se 'desenrolla'."""
    t = np.array(t_us, dtype=np.int64)   # copia: no modificar el DataFrame
    saltos = np.diff(t) < 0
    t[1:] += np.cumsum(saltos) * (2**32)
    return t


def _servo_a_theta(meta, cmd_h, cmd_c):
    """Consigna de servo -> θ del modelo, con la calibración GUARDADA en la captura
    (si existe) para que el resultado no cambie si luego se recalibra."""
    cal = meta.get("calibracion", {})
    ho = cal.get("hombro_offset", P.HOMBRO_OFFSET)
    hs = cal.get("hombro_signo", P.HOMBRO_SIGNO)
    co = cal.get("codo_offset", P.CODO_OFFSET)
    cs = cal.get("codo_signo", P.CODO_SIGNO)
    return np.column_stack([(cmd_h - ho) * hs, (cmd_c - co) * cs])


def _config(meta, clave, por_defecto):
    return meta.get("config_imu", {}).get(clave, por_defecto)


def cargar(ruta_csv):
    ruta_csv = Path(ruta_csv)
    crudo = pd.read_csv(ruta_csv)
    ruta_json = ruta_csv.with_suffix(".json")
    meta = json.loads(ruta_json.read_text(encoding="utf-8")) if ruta_json.exists() else {}

    g_lsb = _config(meta, "gyro_lsb_por_dps", C.GYRO_LSB_POR_DPS)
    a_lsb = _config(meta, "acc_lsb_por_g", C.ACC_LSB_POR_G)
    eje_giro = {int(k): tuple(v) for k, v in
                _config(meta, "eje_giro", {str(k): v for k, v in C.EJE_GIRO.items()}).items()}

    t_us = _desenrollar_us(crudo["t1_us"].to_numpy())
    t = (t_us - t_us[0]) / 1e6
    dt = np.concatenate([[0.0], np.diff(t)])
    seq = crudo["seq"].to_numpy()
    perdidas = int(np.sum(np.diff(seq) - 1)) if len(seq) > 1 else 0
    t2 = _desenrollar_us(crudo["t2_us"].to_numpy())

    acc = {i: crudo[[f"ax{i}", f"ay{i}", f"az{i}"]].to_numpy(float) / a_lsb for i in (1, 2)}
    gyro = {i: crudo[[f"gx{i}", f"gy{i}", f"gz{i}"]].to_numpy(float) / g_lsb for i in (1, 2)}

    # Velocidad angular EN EL PLANO de cada eslabón (canal y signo de EJE_GIRO).
    eje = {"gx": 0, "gy": 1, "gz": 2}
    w = np.column_stack([eje_giro[i][1] * gyro[i][:, eje[eje_giro[i][0]]] for i in (1, 2)])

    theta_cmd = _servo_a_theta(meta, crudo["cmd_h"].to_numpy(float), crudo["cmd_c"].to_numpy(float))
    phi_cmd = np.column_stack([theta_cmd[:, 0], theta_cmd[:, 0] + theta_cmd[:, 1]])

    phi_acc = None
    if _config(meta, "plano_vertical", C.PLANO_VERTICAL):
        ejes = {int(k): v for k, v in _config(
            meta, "ejes_inclinacion",
            {str(k): [list(e) for e in v] for k, v in C.EJES_INCLINACION.items()}).items()}
        offs = {int(k): v for k, v in _config(
            meta, "offset_inclinacion_deg",
            {str(k): v for k, v in C.OFFSET_INCLINACION_DEG.items()}).items()}
        ia = {"ax": 0, "ay": 1, "az": 2}
        cols = []
        for i in (1, 2):
            (ea, sa), (eb, sb) = ejes[i]
            a = sa * acc[i][:, ia[ea]]
            b = sb * acc[i][:, ia[eb]]
            cols.append(np.degrees(np.arctan2(a, b)) + offs[i])
        phi_acc = np.column_stack(cols)

    return Registro(
        nombre=ruta_csv.stem, crudo=crudo, meta=meta, t=t, dt=dt,
        fase=crudo["fase"].to_numpy(), perfil=crudo["perfil"].to_numpy(),
        w=w, acc=acc, gyro=gyro, theta_cmd=theta_cmd, phi_cmd=phi_cmd,
        phi_acc=phi_acc, perdidas=perdidas, sintetico=bool(meta.get("sintetico", False)),
        t2_menos_t1_us=(t2 - t_us).astype(float),
    )


def bias_reposo(reg, mascara=None):
    """Sesgo del giroscopio = media de w en reposo [°/s]. Por defecto, la fase 0
    (reposo inicial) del mismo archivo; si no hay fases, todo el archivo."""
    if mascara is None:
        mascara = reg.fase == 0
        if not mascara.any():
            mascara = np.ones(reg.n, bool)
    return reg.w[mascara].mean(axis=0)


def theta_de_phi(phi):
    """(φ1, φ2) absolutos -> (θ1, θ2) del modelo:  θ1 = φ1,  θ2 = φ2 − φ1."""
    phi = np.asarray(phi)
    return np.stack([phi[..., 0], phi[..., 1] - phi[..., 0]], axis=-1)
