"""Grabación de capturas reales: CSV crudo + JSON de configuración + manifiesto.

Cada captura queda en datos/crudos/ con nombre automático:
    estatico_01.csv, escalones_01.csv, seno_lento_01.csv, seno_rapido_01.csv, libre_01.csv ...
y junto a ella un .json con TODO lo necesario para reproducirla (fecha, firmware,
escalas, montaje de las IMU, calibración de los servos, commit de Git).

El manifiesto (datos/crudos/manifiesto.json) se rehace solo después de cada
grabación, siguiendo una regla fija:
    estático     -> el primer estatico_XX
    dinámico E1  -> el primer escalones_XX
    AJUSTE       -> la repetición 01 de cada perfil
    VALIDACIÓN   -> la repetición 02 de cada perfil
Así ajuste y validación SIEMPRE son registros distintos.
"""
import csv
import json
import re
import time
from datetime import datetime
from pathlib import Path

import config_imu as C
import parametros as P
import reporte as Rp

CARPETA = Rp.RAIZ / "datos" / "crudos"


def siguiente_nombre(base, carpeta=None):
    carpeta = carpeta or CARPETA
    carpeta.mkdir(parents=True, exist_ok=True)
    usados = [int(m.group(1)) for f in carpeta.glob(f"{base}_*.csv")
              if (m := re.fullmatch(rf"{base}_(\d+)", f.stem))]
    return f"{base}_{(max(usados) + 1 if usados else 1):02d}"


class Grabacion:
    """Abre el CSV al empezar y escribe una fila por muestra (no guarda todo en memoria)."""

    def __init__(self, base, modo, perfil=0, cfg_firmware="", carpeta=None):
        self.carpeta = carpeta = carpeta or CARPETA
        self.nombre = siguiente_nombre(base, carpeta)
        self.modo, self.perfil, self.cfg_firmware = modo, perfil, cfg_firmware
        self.ruta = carpeta / f"{self.nombre}.csv"
        self._f = open(self.ruta, "w", newline="", encoding="utf-8")
        self._csv = csv.writer(self._f)
        self._csv.writerow(C.COLUMNAS_CRUDAS + ["t_pc_s"])
        self._t0 = time.perf_counter()
        self.muestras = 0
        self._primer_seq = self._ultimo_seq = None
        self._t_us = [None, None]

    def agregar(self, valores):
        """valores: los 19 enteros de una línea D (en el orden de COLUMNAS_CRUDAS)."""
        self._csv.writerow(list(valores) + [f"{time.perf_counter() - self._t0:.6f}"])
        self.muestras += 1
        if self._primer_seq is None:
            self._primer_seq, self._t_us[0] = valores[0], valores[1]
        self._ultimo_seq, self._t_us[1] = valores[0], valores[1]

    @property
    def duracion_s(self):
        return time.perf_counter() - self._t0

    def cerrar(self, nota=""):
        self._f.close()
        if self.muestras == 0:
            self.ruta.unlink(missing_ok=True)
            return None
        esperadas = self._ultimo_seq - self._primer_seq + 1
        meta = {
            "sintetico": False,
            "fecha": datetime.now().isoformat(timespec="seconds"),
            "modo": self.modo,
            "perfil": self.perfil,
            "perfil_nombre": C.PERFILES.get(self.perfil, self.modo),
            "duracion_s": (self._t_us[1] - self._t_us[0]) / 1e6,
            "muestras": self.muestras,
            "perdidas": esperadas - self.muestras,
            "firmware": self.cfg_firmware,
            "config_imu": C.instantanea(),
            "calibracion": {"hombro_offset": P.HOMBRO_OFFSET, "hombro_signo": P.HOMBRO_SIGNO,
                            "codo_offset": P.CODO_OFFSET, "codo_signo": P.CODO_SIGNO,
                            "L1_mm": P.L1_MM, "L2_mm": P.L2_MM},
            "commit": Rp.commit_actual(),
            "nota": nota,
        }
        self.ruta.with_suffix(".json").write_text(
            json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
        actualizar_manifiesto(self.carpeta)
        return self.ruta


def actualizar_manifiesto(carpeta=None):
    carpeta = carpeta or CARPETA
    def rel(nombre):
        return f"datos/crudos/{nombre}.csv"

    def existe(nombre):
        return (carpeta / f"{nombre}.csv").exists()

    estaticos = sorted(f.stem for f in carpeta.glob("estatico_*.csv"))
    escalones = sorted(f.stem for f in carpeta.glob("escalones_*.csv"))
    man = {"origen": "reales",
           "estatico": rel(estaticos[0]) if estaticos else None,
           "dinamico_e1": rel(escalones[0]) if escalones else None,
           "ajuste": [rel(f"{p}_01") for p in C.PERFILES.values() if existe(f"{p}_01")],
           "validacion": [rel(f"{p}_02") for p in C.PERFILES.values() if existe(f"{p}_02")],
           "regla": "ajuste = repetición 01 de cada perfil; validación = repetición 02"}
    (carpeta / "manifiesto.json").write_text(json.dumps(man, indent=2), encoding="utf-8")
    return man


def parsear_linea_datos(linea):
    """'D,1,2,...' -> lista de 19 enteros, o None si la línea no es válida."""
    if not linea.startswith("D,"):
        return None
    partes = linea[2:].split(",")
    if len(partes) != len(C.COLUMNAS_CRUDAS):
        return None
    try:
        return [int(p) for p in partes]
    except ValueError:
        return None
