"""Utilidades comunes para guardar gráficas y tablas de resultados."""
import json
import subprocess
from pathlib import Path

import matplotlib

matplotlib.use("Agg")   # genera archivos sin abrir ventanas
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent


def cargar_manifiesto(ruta=None):
    """Lista de qué archivo es estático, dinámico, de ajuste y de validación.
    Por defecto usa los datos reales; si no existen, avisa."""
    if ruta is None:
        ruta = RAIZ / "datos" / "crudos" / "manifiesto.json"
    else:
        ruta = Path(ruta)
        if not ruta.is_absolute():   # relativa a donde estés, o a la raíz del proyecto
            ruta = ruta.resolve() if ruta.exists() else RAIZ / ruta
    if not ruta.exists():
        raise SystemExit(
            f"No existe {ruta}.\n"
            "  - Con datos reales: captúralos con python/captura.py y crea ese manifiesto.\n"
            "  - Para probar el código: python python/generar_datos_sinteticos.py y luego\n"
            "    agrega  --manifiesto datos/sinteticos/manifiesto.json")
    m = json.loads(ruta.read_text(encoding="utf-8"))
    m["_ruta"] = str(ruta)
    return m


def ruta_dato(rel):
    return RAIZ / rel


def carpeta_resultados(manifiesto, subcarpeta):
    c = RAIZ / "resultados" / manifiesto.get("origen", "reales") / subcarpeta
    c.mkdir(parents=True, exist_ok=True)
    return c


def commit_actual():
    """Commit de Git con el que se generaron los resultados (trazabilidad)."""
    try:
        h = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=RAIZ,
                           capture_output=True, text=True, check=True).stdout.strip()
        sucio = subprocess.run(["git", "status", "--porcelain"], cwd=RAIZ,
                               capture_output=True, text=True).stdout.strip()
        return h + ("+cambios_sin_commit" if sucio else "")
    except Exception:
        return "desconocido"


def guardar_figura(fig, carpeta, nombre, sintetico=False):
    if sintetico:
        fig.text(0.5, 0.5, "DATOS SINTÉTICOS\nsolo prueba de código", fontsize=34,
                 color="red", alpha=0.12, ha="center", va="center", rotation=25,
                 weight="bold")
    ruta = Path(carpeta) / f"{nombre}.png"
    fig.savefig(ruta, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return ruta


def _formato(v):
    if isinstance(v, float):
        return "—" if v != v else f"{v:.4g}"
    return str(v)


def tabla_markdown(df):
    filas = [" | ".join(map(str, df.columns)), " | ".join("---" for _ in df.columns)]
    filas += [" | ".join(_formato(v) for v in fila) for fila in df.itertuples(index=False)]
    return "\n".join(f"| {f} |" for f in filas)


def guardar_tabla(df, carpeta, nombre, titulo="", nota=""):
    """Guarda la tabla como CSV (para procesar) y como Markdown (para leer)."""
    carpeta = Path(carpeta)
    df.to_csv(carpeta / f"{nombre}.csv", index=False, float_format="%.6g")
    md = [f"# {titulo}", ""] if titulo else []
    md.append(tabla_markdown(df))
    if nota:
        md += ["", nota]
    (carpeta / f"{nombre}.md").write_text("\n".join(md) + "\n", encoding="utf-8")


def _a_json(o):
    """numpy -> tipos de Python que entiende json."""
    if hasattr(o, "tolist"):
        return o.tolist()
    return float(o)


def guardar_json(datos, carpeta, nombre):
    (Path(carpeta) / f"{nombre}.json").write_text(
        json.dumps(datos, indent=2, ensure_ascii=False, default=_a_json), encoding="utf-8")


def encabezado(manifiesto):
    return (f"Generado por código · commit {commit_actual()} · "
            f"manifiesto {Path(manifiesto['_ruta']).resolve().relative_to(RAIZ).as_posix()}")
