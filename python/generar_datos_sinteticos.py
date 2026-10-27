"""Genera capturas SINTÉTICAS con el mismo formato que firmware/adquisicion.

⚠️ Solo sirven para PROBAR el código antes de tener las IMU conectadas. Nunca se
entregan como datos reales: se guardan en datos/sinteticos/, su .json dice
"sintetico": true y todas las gráficas que salen de ellos llevan una marca.

Como aquí SÍ se conoce el ángulo verdadero, se guarda también <nombre>_verdad.csv.
Eso permite mostrar algo que con datos reales no se puede: la diferencia entre
"más suave" y "más exacto".

Ejecutar:  python python/generar_datos_sinteticos.py
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

import config_imu as C
import parametros as P
import perfiles

RAIZ = Path(__file__).resolve().parent.parent

# Modelo simple de un MG996R: sigue la consigna con un retardo de primer orden
# (τ) y con velocidad máxima limitada.
TAU_SERVO_S = 0.06
VEL_MAX_SERVO = 350.0       # °/s
# Ruido típico de una MPU-6050 a 100 Hz con DLPF de 44 Hz.
SIGMA_GIRO = 0.06           # °/s, ruido blanco
SIGMA_VIBRACION = 0.4       # °/s extra mientras los servos se mueven
SIGMA_ACEL = 0.003          # g
CAMINATA_BIAS = 0.002       # °/s/√s, el sesgo cambia muy despacio


def simular(nombre, perfil, duracion_s, rng, carpeta):
    fs_int = 1000.0                       # se simula a 1 kHz y se muestrea a 100 Hz
    n_int = int(duracion_s * fs_int)
    t_int = np.arange(n_int) / fs_int
    servo = np.array([90.0, 90.0])
    cmd_hist, servo_hist, fase_hist = [], [], []
    for t in t_int:
        if perfil:
            c = perfiles.consigna(perfil, t)
            if c is None:
                break
            h, cc, fase = c
        else:
            h, cc, fase = 90, 90, -1
        objetivo = np.array([h, cc], float)
        vel = np.clip((objetivo - servo) / TAU_SERVO_S, -VEL_MAX_SERVO, VEL_MAX_SERVO)
        servo = servo + vel / fs_int
        cmd_hist.append((h, cc))
        servo_hist.append(servo.copy())
        fase_hist.append(fase)
    cmd_hist = np.array(cmd_hist)
    servo_hist = np.array(servo_hist)
    fase_hist = np.array(fase_hist)

    # Servo real -> θ del modelo -> ángulos absolutos de los eslabones.
    th1 = (servo_hist[:, 0] - P.HOMBRO_OFFSET) * P.HOMBRO_SIGNO
    th2 = (servo_hist[:, 1] - P.CODO_OFFSET) * P.CODO_SIGNO
    phi = np.column_stack([th1, th1 + th2])
    omega = np.gradient(phi, 1 / fs_int, axis=0)

    # Muestreo a 100 Hz con timestamps con fluctuación y alguna muestra perdida.
    paso = int(fs_int / C.FS_HZ)
    idx = np.arange(0, len(phi), paso)
    n = len(idx)
    t0_us = int(rng.integers(1_000_000, 5_000_000))
    t1 = t0_us + idx * 1000 + rng.normal(0, 20, n).round().astype(int)
    t2 = t1 + 410 + rng.normal(0, 5, n).round().astype(int)

    bias = rng.normal(0, 0.8, 2) + np.cumsum(rng.normal(0, CAMINATA_BIAS * np.sqrt(1 / C.FS_HZ), (n, 2)), axis=0)
    moviendo = np.abs(omega[idx]) > 1.0
    w_med = omega[idx] + bias + rng.normal(0, SIGMA_GIRO, (n, 2)) \
        + moviendo * rng.normal(0, SIGMA_VIBRACION, (n, 2))

    filas = {"seq": np.arange(n), "t1_us": t1, "t2_us": t2,
             "perfil": perfil, "fase": fase_hist[idx],
             "cmd_h": cmd_hist[idx, 0], "cmd_c": cmd_hist[idx, 1]}
    for i in (1, 2):
        canal, signo = C.EJE_GIRO[i]
        gyro = {"gx": rng.normal(0, SIGMA_GIRO, n), "gy": rng.normal(0, SIGMA_GIRO, n),
                "gz": rng.normal(0, SIGMA_GIRO, n)}
        gyro[canal] = signo * w_med[:, i - 1]
        if C.PLANO_VERTICAL:
            ang = np.radians(phi[idx, i - 1])
            acc = {"ax": np.sin(ang), "ay": np.cos(ang), "az": np.zeros(n)}
        else:
            acc = {"ax": np.zeros(n), "ay": np.zeros(n), "az": np.ones(n)}
        for eje in ("ax", "ay", "az"):
            filas[f"{eje}{i}"] = np.round((acc[eje] + rng.normal(0, SIGMA_ACEL, n)) * C.ACC_LSB_POR_G)
        for eje in ("gx", "gy", "gz"):
            filas[f"{eje}{i}"] = np.round(gyro[eje] * C.GYRO_LSB_POR_DPS)

    df = pd.DataFrame(filas)[C.COLUMNAS_CRUDAS].astype(int)
    df["t_pc_s"] = (df["t1_us"] - t0_us) / 1e6 + 0.003 + rng.exponential(0.001, n)
    verdad = pd.DataFrame({"phi1_deg": phi[idx, 0], "phi2_deg": phi[idx, 1],
                           "omega1_dps": omega[idx, 0], "omega2_dps": omega[idx, 1]})

    # Muestras perdidas (≈ 1 de cada 2000): se borran filas, el hueco queda en seq.
    perdidas = rng.random(n) < 0.0005
    perdidas[:5] = False
    df, verdad = df[~perdidas], verdad[~perdidas]

    carpeta.mkdir(parents=True, exist_ok=True)
    df.to_csv(carpeta / f"{nombre}.csv", index=False)
    verdad.to_csv(carpeta / f"{nombre}_verdad.csv", index=False, float_format="%.5f")
    meta = {
        "sintetico": True,
        "advertencia": "DATOS SINTÉTICOS generados por python/generar_datos_sinteticos.py. No son mediciones.",
        "modo": "perfil" if perfil else "estatico",
        "perfil": perfil, "perfil_nombre": C.PERFILES.get(perfil, "reposo"),
        "duracion_s": float(df["t1_us"].iloc[-1] - df["t1_us"].iloc[0]) / 1e6,
        "muestras": int(len(df)),
        "config_imu": C.instantanea(),
        "calibracion": {"hombro_offset": P.HOMBRO_OFFSET, "hombro_signo": P.HOMBRO_SIGNO,
                        "codo_offset": P.CODO_OFFSET, "codo_signo": P.CODO_SIGNO,
                        "L1_mm": P.L1_MM, "L2_mm": P.L2_MM},
        "simulacion": {"tau_servo_s": TAU_SERVO_S, "vel_max_servo": VEL_MAX_SERVO,
                       "sigma_giro": SIGMA_GIRO, "sigma_vibracion": SIGMA_VIBRACION,
                       "sigma_acel": SIGMA_ACEL, "bias_inicial_dps": bias[0].round(4).tolist()},
    }
    (carpeta / f"{nombre}.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False),
                                            encoding="utf-8")
    return nombre


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--carpeta", default=str(RAIZ / "datos" / "sinteticos"))
    ap.add_argument("--semilla", type=int, default=2026)
    args = ap.parse_args()
    carpeta = Path(args.carpeta)
    rng = np.random.default_rng(args.semilla)

    simular("estatico_01", 0, 40.0, rng, carpeta)
    for rep in (1, 2):
        for p, nom in C.PERFILES.items():
            simular(f"{nom}_{rep:02d}", p, perfiles.duracion_total(p), rng, carpeta)

    rel = lambda nombre: f"datos/sinteticos/{nombre}.csv"
    manifiesto = {
        "origen": "sinteticos",
        "estatico": rel("estatico_01"),
        "dinamico_e1": rel("escalones_01"),
        "ajuste": [rel(f"{n}_01") for n in C.PERFILES.values()],
        "validacion": [rel(f"{n}_02") for n in C.PERFILES.values()],
    }
    (carpeta / "manifiesto.json").write_text(json.dumps(manifiesto, indent=2), encoding="utf-8")
    print(f"Datos sintéticos en {carpeta}")


if __name__ == "__main__":
    main()
