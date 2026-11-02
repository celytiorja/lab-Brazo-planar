"""Validación AUTOMÁTICA de la integridad de las capturas crudas.

Antes de analizar, conviene comprobar que los archivos están sanos: que no faltan
columnas, que el reloj no retrocede, que no se perdieron muestras, que ninguna
IMU se quedó "congelada" ni saturada, etc. Hacerlo a mano es lento y fácil de
olvidar; aquí lo hace el código, igual para todos los archivos.

    python python/validar_datos.py
    python python/validar_datos.py --manifiesto datos/sinteticos/manifiesto.json

Salida: resultados/<origen>/e1/00_validacion_datos.csv/.md
Cada fila: archivo, chequeo, resultado (OK / AVISO / FALLA) y detalle.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

import config_imu as C
import reporte as Rp

TOLERANCIA_FS = 0.02          # fs real dentro de ±2 % de la nominal
JITTER_MAX_US = 1000.0        # más que esto sugiere que el ESP32 se atrasa
DURACION_MIN_ESTATICO_S = 30.0
SATURACION = 32760            # cuentas: el int16 llega a ±32767
# Coherencia consigna–medición: amplitud del ángulo MEDIDO (integración directa)
# dividida por la amplitud de la CONSIGNA, durante el movimiento. Si el servo no
# obedece (cable suelto, sin fuerza, trabado) la medición no se mueve: cociente ≈ 0.
COHERENCIA_MIN, COHERENCIA_MAX = 0.6, 1.4
CANALES_IMU = [f"{e}{i}" for i in (1, 2) for e in ("ax", "ay", "az", "gx", "gy", "gz")]


def _fila(archivo, chequeo, ok, detalle, aviso=False):
    return {"archivo": archivo, "chequeo": chequeo,
            "resultado": "OK" if ok else ("AVISO" if aviso else "FALLA"), "detalle": detalle}


def validar_archivo(ruta, modo=None):
    """Devuelve una lista de filas con el resultado de cada chequeo."""
    ruta = Path(ruta)
    n = ruta.stem
    if not ruta.exists():
        return [_fila(n, "existe el CSV", False, str(ruta))]
    filas = []
    ruta_json = ruta.with_suffix(".json")
    meta = json.loads(ruta_json.read_text(encoding="utf-8")) if ruta_json.exists() else {}
    filas.append(_fila(n, "existe el JSON de configuración", ruta_json.exists(), ruta_json.name))
    modo = modo or meta.get("modo") or ("estatico" if n.startswith("estatico") else "perfil")

    df = pd.read_csv(ruta)
    faltan = [c for c in C.COLUMNAS_CRUDAS if c not in df.columns]
    filas.append(_fila(n, "columnas esperadas", not faltan, f"faltan: {faltan}" if faltan else
                       f"{len(C.COLUMNAS_CRUDAS)} columnas"))
    if faltan:
        return filas
    crudo = df[C.COLUMNAS_CRUDAS]
    nan = int(crudo.isna().sum().sum())
    filas.append(_fila(n, "sin valores vacíos (NaN)", nan == 0, f"{nan} vacíos"))
    enteros = all(pd.api.types.is_integer_dtype(crudo[c]) for c in crudo.columns)
    filas.append(_fila(n, "valores enteros (cuentas crudas)", enteros, "int" if enteros else "hay decimales"))
    if nan:
        return filas

    seq = crudo["seq"].to_numpy()
    dseq = np.diff(seq)
    filas.append(_fila(n, "seq creciente", bool(np.all(dseq > 0)),
                       f"{int(np.sum(dseq <= 0))} retrocesos"))
    huecos = int(np.sum(dseq[dseq > 1] - 1))
    filas.append(_fila(n, "muestras perdidas (huecos en seq)", huecos == 0,
                       f"{huecos} perdidas de {len(seq) + huecos} ({100*huecos/(len(seq)+huecos):.3f} %)",
                       aviso=huecos / max(len(seq), 1) < 0.01))

    t = crudo["t1_us"].to_numpy(np.int64)
    dt = np.diff(t)
    dt = np.where(dt < 0, dt + 2**32, dt)        # micros() se desborda cada ~71 min
    filas.append(_fila(n, "timestamps monótonos (con desborde de micros)", bool(np.all(dt > 0)),
                       f"{int(np.sum(dt <= 0))} no crecientes"))
    # Δt "normal": se excluyen los saltos por muestras perdidas para medir el jitter.
    normales = dt[dseq == 1] if len(dseq) == len(dt) else dt
    fs_real = 1e6 / np.mean(normales)
    err_fs = abs(fs_real - C.FS_HZ) / C.FS_HZ
    filas.append(_fila(n, f"fs real dentro de ±{TOLERANCIA_FS*100:.0f} %", err_fs <= TOLERANCIA_FS,
                       f"{fs_real:.3f} Hz (nominal {C.FS_HZ:.0f})"))
    jitter = float(np.std(normales))
    filas.append(_fila(n, f"jitter de Δt < {JITTER_MAX_US:.0f} µs", jitter < JITTER_MAX_US,
                       f"σ(Δt) = {jitter:.1f} µs", aviso=True))
    d12 = crudo["t2_us"].to_numpy(np.int64) - t
    d12 = np.where(d12 < 0, d12 + 2**32, d12)
    filas.append(_fila(n, "desfase IMU2−IMU1 entre 0 y 5 ms", bool(np.all((d12 > 0) & (d12 < 5000))),
                       f"media {d12.mean():.0f} µs"))

    duracion = (t[-1] - t[0] + (2**32 if t[-1] < t[0] else 0)) / 1e6
    if modo == "estatico":
        filas.append(_fila(n, f"reposo ≥ {DURACION_MIN_ESTATICO_S:.0f} s",
                           duracion >= DURACION_MIN_ESTATICO_S, f"{duracion:.1f} s"))
    else:
        filas.append(_fila(n, "duración", duracion > 1.0, f"{duracion:.1f} s"))

    sat = {c: int(np.sum(np.abs(crudo[c].to_numpy()) >= SATURACION)) for c in CANALES_IMU}
    sat_total = sum(sat.values())
    filas.append(_fila(n, "sin saturación (|cuentas| < 32760)", sat_total == 0,
                       "ninguna" if sat_total == 0 else str({k: v for k, v in sat.items() if v}),
                       aviso=True))
    congelados = [c for c in CANALES_IMU if crudo[c].std() == 0]
    filas.append(_fila(n, "ninguna IMU congelada (σ > 0 en cada canal)", not congelados,
                       f"congelados: {congelados}" if congelados else "todos varían"))

    perfiles = set(crudo["perfil"].unique())
    fases = crudo["fase"].to_numpy()
    if modo == "estatico":
        ok = perfiles <= {0} and set(np.unique(fases)) <= {-1}
        filas.append(_fila(n, "perfil/fase de reposo (0 / −1)", ok, f"perfiles {perfiles}"))
    else:
        ok = len(perfiles) == 1 and set(np.unique(fases)) <= {0, 1, 2} and bool(np.all(np.diff(fases) >= 0))
        filas.append(_fila(n, "un solo perfil y fases 0→1→2 en orden", ok,
                           f"perfiles {perfiles}, fases {sorted(set(np.unique(fases)))}"))
        filas.append(_coherencia(ruta, n))
    return filas


def _coherencia(ruta, n):
    """¿El brazo MEDIDO por las IMU siguió a la CONSIGNA? (la consigna es un deseo)."""
    from datos_imu import bias_reposo, cargar, theta_de_phi
    from estimadores import IntegracionDirecta, ejecutar
    reg = cargar(ruta)
    mov = reg.fase == 1
    if mov.sum() < 50:
        return _fila(n, "el brazo medido sigue a la consigna", True, "sin fase de movimiento")
    phi, _, _ = ejecutar(IntegracionDirecta(reg.phi_cmd[0], bias_reposo(reg)), reg)
    th = theta_de_phi(phi)
    cocientes = []
    for j in (0, 1):
        s_cmd = np.std(reg.theta_cmd[mov, j])
        if s_cmd > 1.0:                          # esa articulación sí debía moverse
            cocientes.append(np.std(th[mov, j]) / s_cmd)
    ok = all(COHERENCIA_MIN <= c <= COHERENCIA_MAX for c in cocientes)
    detalle = "amplitud medida/consigna = " + ", ".join(f"{c:.2f}" for c in cocientes)
    if not ok:
        detalle += " → alguna articulación NO obedeció (¿servo sin fuerza, cable, trabado?)"
    return _fila(n, "el brazo medido sigue a la consigna", ok, detalle)


def captura_valida(ruta, modo):
    """True si la captura no tiene ningún chequeo en FALLA."""
    return all(f["resultado"] != "FALLA" for f in validar_archivo(ruta, modo))


def archivos_del_manifiesto(man):
    lista = []
    if man.get("estatico"):
        lista.append((man["estatico"], "estatico"))
    for clave in ("dinamico_e1",):
        if man.get(clave):
            lista.append((man[clave], "perfil"))
    for clave in ("ajuste", "validacion"):
        lista += [(r, "perfil") for r in man.get(clave, [])]
    vistos, unicos = set(), []
    for r, m in lista:
        if r not in vistos:
            vistos.add(r)
            unicos.append((r, m))
    return unicos


def validar_manifiesto(man, sal=None):
    filas = []
    for rel, modo in archivos_del_manifiesto(man):
        filas += validar_archivo(Rp.ruta_dato(rel), modo)
    df = pd.DataFrame(filas)
    if sal is not None:
        resumen = df.resultado.value_counts().to_dict()
        Rp.guardar_tabla(df, sal, "00_validacion_datos", "Validación automática de los datos crudos",
                         f"Resumen: {resumen}. " + Rp.encabezado(man))
    return df


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifiesto", default=None)
    args = ap.parse_args()
    man = Rp.cargar_manifiesto(args.manifiesto)
    df = validar_manifiesto(man, Rp.carpeta_resultados(man, "e1"))
    problemas = df[df.resultado != "OK"]
    print(df.resultado.value_counts().to_string())
    if len(problemas):
        print("\nRevisar:\n" + problemas.to_string(index=False))


if __name__ == "__main__":
    main()
