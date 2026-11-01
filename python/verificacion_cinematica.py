"""ENTREGA 1, punto 1 — Verificación de la cinemática con el brazo REAL.

Idea: mandar al brazo posiciones conocidas, medir con regla dónde queda la punta
y comparar con lo que predice el modelo. La diferencia es el ERROR OBSERVADO.

    python python/verificacion_cinematica.py --plantilla     crea la hoja para medir
    (mides x_med_mm, y_med_mm de cada fila en papel milimetrado y guardas)
    python python/verificacion_cinematica.py                 calcula errores y gráficas

Dos tipos de prueba:
  directa:  se eligen ángulos de servo -> el modelo dice dónde DEBE quedar la punta.
  inversa:  se elige un punto (x, y) -> la cinemática inversa da los ángulos ->
            se redondean a grados enteros (el servo no acepta decimales) -> se mide.
Cada punto se mide 2 veces (columna `repeticion`) para ver la REPETIBILIDAD.
"""
import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")   # solo genera archivos: no abre ventanas
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np
import pandas as pd
from matplotlib.patches import Circle
from scipy.optimize import least_squares

import parametros as P
import reporte as Rp
from cinematica import cinematica_directa, cinematica_inversa
from servos import modelo_a_servo, servo_a_modelo

CSV_POR_DEFECTO = Rp.RAIZ / "datos" / "verificacion_cinematica.csv"
RESOLUCION_SERVO_DEG = 1.0     # servo.write() solo acepta grados enteros

# Puntos elegidos para cubrir el espacio de trabajo (cerca, lejos, izquierda, derecha).
PUNTOS_DIRECTA = [(45, 90), (90, 90), (135, 90), (60, 60), (120, 120)]   # (servo_h, servo_c)
PUNTOS_INVERSA = [(150, 70), (0, 170), (-110, 125), (80, 150), (160, 40)]  # (x, y) mm, r ≈ 165–170
COLUMNAS = ["id", "tipo", "repeticion", "servo_h", "servo_c", "theta1_deg", "theta2_deg",
            "x_obj_mm", "y_obj_mm", "x_teo_mm", "y_teo_mm", "x_med_mm", "y_med_mm"]


def _fila(id_, tipo, rep, sh, sc, x_obj=np.nan, y_obj=np.nan):
    t1, t2 = servo_a_modelo(sh, sc)
    (x, y), _ = cinematica_directa(t1, t2, P.L1_MM, P.L2_MM)
    return {"id": id_, "tipo": tipo, "repeticion": rep, "servo_h": sh, "servo_c": sc,
            "theta1_deg": t1, "theta2_deg": t2, "x_obj_mm": x_obj, "y_obj_mm": y_obj,
            "x_teo_mm": round(float(x), 2), "y_teo_mm": round(float(y), 2),
            "x_med_mm": np.nan, "y_med_mm": np.nan}


def crear_plantilla(repeticiones=2):
    filas, k = [], 1
    for sh, sc in PUNTOS_DIRECTA:
        for rep in range(1, repeticiones + 1):
            filas.append(_fila(f"P{k:02d}", "directa", rep, sh, sc))
        k += 1
    for x, y in PUNTOS_INVERSA:
        for codo in ("abajo", "arriba"):      # la que respete los límites de los servos
            t1, t2 = cinematica_inversa(x, y, P.L1_MM, P.L2_MM, codo=codo)
            t1 = float(t1) % 360
            if P.THETA1_MIN <= t1 <= P.THETA1_MAX and P.THETA2_MIN <= float(t2) <= P.THETA2_MAX:
                sh, sc = modelo_a_servo(t1, float(t2))
                for rep in range(1, repeticiones + 1):
                    filas.append(_fila(f"P{k:02d}", "inversa", rep, sh, sc, x, y))
                k += 1
                break
    return pd.DataFrame(filas, columns=COLUMNAS)


def encabezado_calibracion(extra=""):
    return (f"# L1_mm={P.L1_MM} L2_mm={P.L2_MM} hombro_offset={P.HOMBRO_OFFSET} "
            f"hombro_signo={P.HOMBRO_SIGNO} codo_offset={P.CODO_OFFSET} codo_signo={P.CODO_SIGNO}"
            f"{extra}\n# Origen = eje del hombro; x = dirección de θ1 = 0; y perpendicular "
            f"(θ1 = 90°). Medir la punta en mm.\n")


def guardar_plantilla(ruta, sobrescribir=False):
    ruta = Path(ruta)
    if ruta.exists() and not sobrescribir:
        raise SystemExit(f"{ruta} ya existe (tiene tus medidas). Usa --sobrescribir si de verdad "
                         "quieres empezar de nuevo.")
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "w", encoding="utf-8", newline="") as f:
        f.write(encabezado_calibracion())
        crear_plantilla().to_csv(f, index=False)
    return ruta


def _jacobiano(t1, t2):
    """d(x, y)/d(θ1, θ2) en mm/rad: cuánto se mueve la punta por cada radián de error."""
    a, b = np.radians(t1), np.radians(t1 + t2)
    return np.array([[-P.L1_MM * np.sin(a) - P.L2_MM * np.sin(b), -P.L2_MM * np.sin(b)],
                     [P.L1_MM * np.cos(a) + P.L2_MM * np.cos(b), P.L2_MM * np.cos(b)]])


def error_por_resolucion(t1, t2):
    """σ de posición [mm] que produce SOLO redondear cada servo a 1°.
    Redondear da un error uniforme en ±0.5°  ->  σ = 1°/√12 por articulación."""
    s = np.radians(RESOLUCION_SERVO_DEG) / np.sqrt(12)
    J = _jacobiano(t1, t2)
    return float(np.sqrt(np.sum((J * s) ** 2)))


def estimar_offsets(df):
    """¿Qué corrimiento constante de cada articulación (δ1, δ2) explica mejor los
    errores? (mínimos cuadrados). Si al corregirlo el error baja mucho, la causa
    principal era la calibración (offset), no el ruido."""
    def residuos(d):
        (x, y), _ = cinematica_directa(df.theta1_deg + d[0], df.theta2_deg + d[1], P.L1_MM, P.L2_MM)
        return np.concatenate([x - df.x_med_mm, y - df.y_med_mm])
    r = least_squares(residuos, [0.0, 0.0])
    e = r.fun.reshape(2, -1)
    rmse_corr = float(np.sqrt(np.mean(e[0] ** 2 + e[1] ** 2)))
    return float(r.x[0]), float(r.x[1]), rmse_corr


def es_sintetico(ruta_csv):
    """Las medidas inventadas por el generador llevan 'SINTÉTICO' en el encabezado."""
    with open(ruta_csv, encoding="utf-8") as f:
        return any("SINTÉTICO" in linea for linea in f.readlines()[:3])


def analizar(ruta_csv, sal, sintetico=None):
    """Calcula errores, repetibilidad y fuentes de error. Devuelve el resumen (dict)."""
    if sintetico is None:
        sintetico = es_sintetico(ruta_csv)
    df = pd.read_csv(ruta_csv, comment="#")
    df = df.dropna(subset=["x_med_mm", "y_med_mm"]).copy()
    if df.empty:
        print(f"{ruta_csv}: aún no hay medidas (x_med_mm, y_med_mm vacías).")
        return None
    df["error_mm"] = np.hypot(df.x_med_mm - df.x_teo_mm, df.y_med_mm - df.y_teo_mm)
    df["error_vs_objetivo_mm"] = np.hypot(df.x_med_mm - df.x_obj_mm, df.y_med_mm - df.y_obj_mm)
    df["sigma_resolucion_mm"] = [error_por_resolucion(a, b) for a, b in
                                 zip(df.theta1_deg, df.theta2_deg)]

    # Repetibilidad: distancia entre las mediciones repetidas del MISMO punto.
    rep = (df.groupby("id")[["x_med_mm", "y_med_mm"]]
           .agg(lambda s: s.max() - s.min()).pipe(lambda d: np.hypot(d.x_med_mm, d.y_med_mm)))
    rep = rep[df.groupby("id").size() > 1]

    d1, d2, rmse_corr = estimar_offsets(df)
    resumen = []
    for tipo, g in [("todos", df)] + list(df.groupby("tipo")):
        resumen.append({"tipo": tipo, "n": len(g), "rmse_mm": float(np.sqrt(np.mean(g.error_mm**2))),
                        "media_mm": float(g.error_mm.mean()), "max_mm": float(g.error_mm.max()),
                        "sigma_resolucion_media_mm": float(g.sigma_resolucion_mm.mean())})
    tabla_res = pd.DataFrame(resumen)
    fuentes = {
        "offset_estimado_theta1_deg": d1, "offset_estimado_theta2_deg": d2,
        "rmse_sin_corregir_mm": resumen[0]["rmse_mm"],
        "rmse_corrigiendo_offsets_mm": rmse_corr,
        "repetibilidad_media_mm": float(rep.mean()) if len(rep) else np.nan,
        "repetibilidad_max_mm": float(rep.max()) if len(rep) else np.nan,
        "sigma_resolucion_1grado_mm": float(df.sigma_resolucion_mm.mean()),
    }

    cols = ["id", "tipo", "repeticion", "servo_h", "servo_c", "x_teo_mm", "y_teo_mm",
            "x_med_mm", "y_med_mm", "error_mm", "error_vs_objetivo_mm", "sigma_resolucion_mm"]
    nota = ("error_mm: medido vs teórico de los ángulos ENVIADOS (error del modelo/brazo). "
            "error_vs_objetivo: en inversa, medido vs punto pedido (incluye redondear a 1°). "
            "sigma_resolucion: error esperado SOLO por la resolución de 1° del servo.")
    Rp.guardar_tabla(df[cols], sal, "verificacion_cinematica", "Verificación cinemática por punto", nota)
    Rp.guardar_tabla(tabla_res, sal, "verificacion_cinematica_resumen",
                     "Verificación cinemática: resumen",
                     "Fuentes de error (mínimos cuadrados sobre todos los puntos): "
                     f"offset θ1 = {d1:+.2f}°, offset θ2 = {d2:+.2f}°. RMSE {resumen[0]['rmse_mm']:.2f} mm "
                     f"→ {rmse_corr:.2f} mm al corregirlos. Repetibilidad media "
                     f"{fuentes['repetibilidad_media_mm']:.2f} mm. Resolución de 1° ≈ "
                     f"{fuentes['sigma_resolucion_1grado_mm']:.2f} mm.")
    Rp.guardar_json({"resumen": resumen, "fuentes_de_error": fuentes,
                     "archivo": str(Path(ruta_csv).name)}, sal, "verificacion_cinematica")
    graficar(df, sal, sintetico, d1, d2)
    return {"resumen": resumen, "fuentes": fuentes}


def graficar(df, sal, sintetico, d1, d2):
    alcance = P.L1_MM + P.L2_MM
    fig, ax = plt.subplots(figsize=(8, 7))
    ax.add_patch(Circle((0, 0), alcance, color="0.92", zorder=0))
    ax.add_patch(Circle((0, 0), abs(P.L1_MM - P.L2_MM), color="white", zorder=0))
    for tipo, marca in (("directa", "o"), ("inversa", "s")):
        g = df[df.tipo == tipo]
        ax.plot(g.x_teo_mm, g.y_teo_mm, marca, mfc="none", mec="tab:blue", ms=9,
                label=f"teórico ({tipo})")
        ax.plot(g.x_med_mm, g.y_med_mm, "x", color="tab:red", ms=7)
    ax.plot([], [], "x", color="tab:red", label="medido")
    escala = 5
    for _, r in df.iterrows():
        ax.annotate("", xy=(r.x_teo_mm + escala * (r.x_med_mm - r.x_teo_mm),
                            r.y_teo_mm + escala * (r.y_med_mm - r.y_teo_mm)),
                    xytext=(r.x_teo_mm, r.y_teo_mm),
                    arrowprops=dict(arrowstyle="->", color="tab:red", lw=1))
    for pid, g in df.groupby("id"):
        ax.text(g.x_teo_mm.iloc[0] + 4, g.y_teo_mm.iloc[0] + 4, pid, fontsize=7)
    ax.plot(0, 0, "ks")
    ax.set_aspect("equal")
    ax.set_xlim(-alcance * 1.1, alcance * 1.1)
    ax.set_ylim(-alcance * 0.3, alcance * 1.1)
    ax.grid(alpha=0.3)
    ax.set_xlabel("x [mm]")
    ax.set_ylabel("y [mm]")
    ax.legend(fontsize=8, loc="lower right")
    ax.set_title(f"Verificación cinemática (flechas de error ×{escala}); offsets estimados "
                 f"δθ1 = {d1:+.1f}°, δθ2 = {d2:+.1f}°", fontsize=10)
    Rp.guardar_figura(fig, sal, "09_verificacion_cinematica", sintetico)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plantilla", action="store_true", help="crear la hoja de medición")
    ap.add_argument("--sobrescribir", action="store_true")
    ap.add_argument("--csv", default=None, help=f"por defecto {CSV_POR_DEFECTO.relative_to(Rp.RAIZ)}")
    ap.add_argument("--manifiesto", default=None, help="usa su clave 'verificacion_cinematica'")
    args = ap.parse_args()
    if args.plantilla:
        ruta = guardar_plantilla(args.csv or CSV_POR_DEFECTO, args.sobrescribir)
        print(f"Plantilla creada: {ruta}. Mide cada fila y llena x_med_mm, y_med_mm.")
        return
    man = {"origen": "reales"}
    ruta = Path(args.csv) if args.csv else CSV_POR_DEFECTO
    if args.manifiesto:
        man = Rp.cargar_manifiesto(args.manifiesto)
        if man.get("verificacion_cinematica"):
            ruta = Rp.ruta_dato(man["verificacion_cinematica"])
    if not ruta.exists():
        raise SystemExit(f"No existe {ruta}. Primero: python python/verificacion_cinematica.py --plantilla")
    sal = Rp.carpeta_resultados(man, "e1")
    r = analizar(ruta, sal)
    if r:
        print(f"RMSE {r['resumen'][0]['rmse_mm']:.2f} mm. Resultados en {sal}")


if __name__ == "__main__":
    main()
