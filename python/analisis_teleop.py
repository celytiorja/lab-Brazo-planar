"""Análisis de las sesiones de TELEOPERACIÓN con cámara (Entrega 2: E8, C2-N3…N5).

    python python/analisis_teleop.py                  (sesiones reales: datos/teleop)
    python python/analisis_teleop.py --sinteticos     (prueba: datos/sinteticos/teleop)

Se corre SOLO al salir de teleop_camara.py si grabaste sesiones.

Preguntas que responde, con números medidos:
  1. ¿La cámara ve bien?          fps reales, Δt (jitter), % de cuadros con los 3 marcadores,
                                  oclusiones (cuántas y cuánto duraron).
  2. ¿Kalman suaviza?             "aspereza" = RMS de la 2.ª diferencia del ángulo (cuánto
                                  cambia el cambio entre cuadros): crudo vs Kalman.
  3. ¿Qué le llega al servo?      con la MISMA regla de envío de teleop_camara.py se calculan
                                  las órdenes que habría mandado cada fuente: órdenes/s y
                                  cambios de dirección/s (temblor del servo).
  4. ¿Cuánto retrasa Kalman?      el corrimiento en el tiempo que mejor alinea Kalman con crudo.
  5. ¿Cuánto cuesta calcular?     tiempo de Kalman (µs) y de detección + Kalman (ms) por cuadro,
                                  comparado con el periodo entre cuadros.
  6. Con robot (IMU del robot):   retraso orden -> robot y cámara -> robot, y cuánto VIBRA el
                                  robot (giroscopio) cuando lo mueve crudo vs Kalman.
  7. Sintéticos (verdad conocida): error RMS de crudo y Kalman contra la verdad, también
                                  durante las oclusiones.

La comparación crudo vs Kalman se hace sobre los MISMOS cuadros (las dos se calculan
siempre): mismas condiciones, solo cambia el método.
"""
import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import config_camara as CC  # noqa: E402
import reporte as Rp  # noqa: E402
from servos import modelo_a_servo, servo_a_modelo  # noqa: E402

CARPETAS = {"reales": Rp.RAIZ / "datos" / "teleop",
            "sinteticos": Rp.RAIZ / "datos" / "sinteticos" / "teleop"}
RETRASO_MAX_S = 0.6           # se buscan retrasos entre 0 y esto
PASO_RETRASO_S = 0.005


# ----------------------------------------------------------------- utilidades
def tramos(mascara):
    """Lista de (inicio, fin) de los tramos True consecutivos (fin exclusivo)."""
    m = np.concatenate([[False], np.asarray(mascara, bool), [False]])
    d = np.diff(m.astype(int))
    return list(zip(np.flatnonzero(d == 1), np.flatnonzero(d == -1)))


def aspereza(theta, validos=None):
    """RMS de θ[k+1] − 2θ[k] + θ[k−1] usando solo tríos de cuadros válidos consecutivos."""
    theta = np.asarray(theta, float)
    ok = np.isfinite(theta) if validos is None else (np.asarray(validos, bool) & np.isfinite(theta))
    d2 = theta[2:] - 2 * theta[1:-1] + theta[:-2]
    usar = ok[2:] & ok[1:-1] & ok[:-2]
    return float(np.sqrt(np.mean(d2[usar] ** 2))) if usar.any() else np.nan


def ordenes_simuladas(t, theta1, theta2):
    """Órdenes que se habrían mandado al servo con la regla de teleop_camara.decidir_envio."""
    from teleop_camara import decidir_envio
    ultimo, t_ult = None, -1e9
    cmd_por_cuadro = np.full((len(t), 2), np.nan)
    enviados = []
    for k in range(len(t)):
        if not (np.isfinite(theta1[k]) and np.isfinite(theta2[k])):
            if ultimo is not None:
                cmd_por_cuadro[k] = ultimo
            continue
        cmd = modelo_a_servo(theta1[k], theta2[k])
        if decidir_envio(cmd, ultimo, t[k], t_ult):
            ultimo, t_ult = cmd, t[k]
            enviados.append((t[k], *cmd))
        cmd_por_cuadro[k] = ultimo
    return cmd_por_cuadro, np.array(enviados).reshape(-1, 3)


def cambios_de_direccion(serie):
    """Cuántas veces la serie (escalonada) cambia de subir a bajar o al revés."""
    d = np.diff(serie[np.isfinite(serie)])
    d = d[d != 0]
    return int(np.sum(np.sign(d[1:]) != np.sign(d[:-1]))) if len(d) > 1 else 0


def mejor_retraso(t_ref, y_ref, t_y, y, quitar_tendencia=False, validos_ref=None):
    """Retraso τ ≥ 0 tal que y(t + τ) se parece más a y_ref(t) (mínimo error RMS).

    Devuelve (τ en s, error RMS con ese τ). Si quitar_tendencia, a ambas se les quita
    la recta de mejor ajuste (sirve cuando una viene de integrar un giroscopio con sesgo).
    """
    t_ref, y_ref, t_y, y = map(lambda a: np.asarray(a, float), (t_ref, y_ref, t_y, y))
    ok = np.isfinite(y_ref) & (np.ones_like(y_ref, bool) if validos_ref is None
                               else np.asarray(validos_ref, bool))
    oky = np.isfinite(y)
    if ok.sum() < 20 or oky.sum() < 20:
        return np.nan, np.nan
    t_ref, y_ref = t_ref[ok], y_ref[ok]
    t_y, y = t_y[oky], y[oky]
    mejor = (np.nan, np.inf)
    for tau in np.arange(0, RETRASO_MAX_S + 1e-9, PASO_RETRASO_S):
        dentro = (t_ref + tau >= t_y[0]) & (t_ref + tau <= t_y[-1])
        if dentro.sum() < 20:
            break
        a = y_ref[dentro]
        b = np.interp(t_ref[dentro] + tau, t_y, y)
        if quitar_tendencia:
            a = a - np.polyval(np.polyfit(t_ref[dentro], a, 1), t_ref[dentro])
            b = b - np.polyval(np.polyfit(t_ref[dentro], b, 1), t_ref[dentro])
        else:
            a, b = a - a.mean(), b - b.mean()
        e = float(np.sqrt(np.mean((a - b) ** 2)))
        if e < mejor[1]:
            mejor = (float(tau), e)
    return mejor


# ----------------------------------------------------------------- una sesión
def cargar_sesion(ruta):
    df = pd.read_csv(ruta)
    meta_ruta = Path(ruta).with_suffix(".json")
    meta = json.loads(meta_ruta.read_text(encoding="utf-8")) if meta_ruta.exists() else {}
    ruta_robot = Path(ruta).with_name(Path(ruta).stem + "_robot.csv")
    robot = pd.read_csv(ruta_robot) if ruta_robot.exists() else None
    return df, meta, robot


def fuente_del_robot(df):
    env = df[df["enviando"] == 1]
    if env.empty:
        return "sin robot"
    return env["fuente"].mode().iloc[0].split(":")[0]


def analizar_sesion(ruta):
    df, meta, robot = cargar_sesion(ruta)
    t = df["t_s"].to_numpy()
    visto = df["visto"].to_numpy().astype(bool)
    crudo = df[["theta1_crudo", "theta2_crudo"]].to_numpy(float)
    kf = df[["theta1_kf", "theta2_kf"]].to_numpy(float)
    dt = np.diff(t)
    res = {"sesion": Path(ruta).stem, "robot_movido_con": fuente_del_robot(df),
           "duracion_s": t[-1] - t[0], "cuadros": len(t),
           "fps": (len(t) - 1) / (t[-1] - t[0]), "dt_medio_ms": dt.mean() * 1e3,
           "dt_std_ms": dt.std() * 1e3, "dt_max_ms": dt.max() * 1e3,
           "visto_pct": 100 * visto.mean()}
    if "solo_theta1" in df:
        res["solo_theta1_pct"] = 100 * df["solo_theta1"].mean()
    if "hombro_memoria" in df:
        res["hombro_memoria_pct"] = 100 * df["hombro_memoria"].mean()
    huecos = [(a, b) for a, b in tramos(~visto) if a > 0]      # sin el arranque
    res["oclusiones"] = len(huecos)
    res["oclusion_max_ms"] = max(((t[min(b, len(t) - 1)] - t[a - 1]) * 1e3 for a, b in huecos),
                                 default=0.0)

    # 2) Suavidad del ángulo, en los MISMOS cuadros (los que la cámara vio)
    for j, n in enumerate(("theta1", "theta2")):
        res[f"aspereza_{n}_crudo"] = aspereza(crudo[:, j], visto)
        res[f"aspereza_{n}_kf"] = aspereza(kf[:, j], visto)

    # 3) Órdenes al servo con cada fuente (misma regla de envío)
    c_crudo, env_crudo = ordenes_simuladas(t, *np.where(visto[:, None], crudo, np.nan).T)
    c_kf, env_kf = ordenes_simuladas(t, *kf.T)
    dur = t[-1] - t[0]
    res["ordenes_s_crudo"] = len(env_crudo) / dur
    res["ordenes_s_kf"] = len(env_kf) / dur
    for j, n in enumerate(("hombro", "codo")):
        res[f"cambios_dir_s_{n}_crudo"] = cambios_de_direccion(c_crudo[:, j]) / dur
        res[f"cambios_dir_s_{n}_kf"] = cambios_de_direccion(c_kf[:, j]) / dur

    # 4) Retraso de Kalman respecto a crudo (solo cuadros vistos de crudo)
    for j, n in enumerate(("theta1", "theta2")):
        tau, _ = mejor_retraso(t, crudo[:, j], t, kf[:, j], validos_ref=visto)
        res[f"retraso_kf_{n}_ms"] = tau * 1e3

    # 5) Tiempos de cómputo
    res["t_kalman_us_medio"] = df["t_calc_kf_us"].mean()
    res["t_kalman_us_p95"] = df["t_calc_kf_us"].quantile(0.95)
    if "t_proc_ms" in df:
        res["t_proc_ms_medio"] = df["t_proc_ms"].mean()
        res["t_proc_ms_p95"] = df["t_proc_ms"].quantile(0.95)
        res["carga_pct"] = 100 * df["t_proc_ms"].mean() / (dt.mean() * 1e3)

    # 7) Verdad (solo sintéticos)
    if "theta1_verdad" in df:
        verdad = df[["theta1_verdad", "theta2_verdad"]].to_numpy(float)
        # crudo "congelado": lo que tendría el robot si solo usa la cámara
        crudo_cong = pd.DataFrame(np.where(visto[:, None], crudo, np.nan)).ffill().to_numpy()
        for j, n in enumerate(("theta1", "theta2")):
            res[f"rmse_{n}_crudo"] = float(np.sqrt(np.nanmean((crudo[visto, j] - verdad[visto, j]) ** 2)))
            res[f"rmse_{n}_kf"] = float(np.sqrt(np.nanmean((kf[visto, j] - verdad[visto, j]) ** 2)))
            if (~visto[10:]).any():
                m = ~visto
                m[:10] = False
                res[f"rmse_oclusion_{n}_crudo"] = float(np.sqrt(np.nanmean(
                    (crudo_cong[m, j] - verdad[m, j]) ** 2)))
                res[f"rmse_oclusion_{n}_kf"] = float(np.sqrt(np.nanmean((kf[m, j] - verdad[m, j]) ** 2)))

    extra = {"t": t, "visto": visto, "crudo": crudo, "kf": kf,
             "verdad": df[["theta1_verdad", "theta2_verdad"]].to_numpy(float)
             if "theta1_verdad" in df else None,
             "c_crudo": c_crudo, "c_kf": c_kf, "robot": None, "meta": meta}

    # 6) Robot: giroscopio (IMU de la Entrega 1)
    if robot is not None and len(robot) > 50 and (df["enviado"] == 1).sum() > 5:
        extra["robot"] = analizar_robot(df, robot, t, crudo, visto, res)
    return res, extra


def analizar_robot(df, robot, t, crudo, visto, res):
    """Retrasos y vibración del robot a partir de su giroscopio."""
    tr = robot["t_s"].to_numpy()
    w1 = robot["w1_dps"].to_numpy()
    w_codo = robot["w2_dps"].to_numpy() - w1                # θ2 = φ2 − φ1 -> ω_codo = ω2 − ω1
    # Ángulo del robot integrando (Euler con Δt de la PC); el sesgo se vuelve una recta
    # que mejor_retraso(quitar_tendencia=True) elimina.
    dtr = np.diff(tr, prepend=tr[0])
    th_robot = np.column_stack([np.cumsum(w1 * dtr), np.cumsum(w_codo * dtr)])
    # Orden enviada (escalonada) en el tiempo de cada cuadro
    env = df[df["enviado"] == 1]
    th_cmd = np.array([servo_a_modelo(h, c) for h, c in zip(env["cmd_h"], env["cmd_c"])])
    t_cmd = env["t_s"].to_numpy()
    idx = np.searchsorted(t_cmd, tr, side="right") - 1
    ok = idx >= 0
    cmd_en_tr = np.full((len(tr), 2), np.nan)
    cmd_en_tr[ok] = th_cmd[idx[ok]]
    salida = {"tr": tr, "th_robot": th_robot, "cmd_en_tr": cmd_en_tr, "w": np.column_stack([w1, w_codo])}
    for j, n in enumerate(("hombro", "codo")):
        tau, e = mejor_retraso(tr, cmd_en_tr[:, j], tr, th_robot[:, j], quitar_tendencia=True)
        res[f"retraso_orden_robot_{n}_ms"] = tau * 1e3
        res[f"error_seguimiento_{n}_deg"] = e
        tau2, _ = mejor_retraso(t, crudo[:, j], tr, th_robot[:, j], quitar_tendencia=True,
                                validos_ref=visto)
        res[f"retraso_camara_robot_{n}_ms"] = tau2 * 1e3
        # Vibración: lo que queda del giroscopio al quitarle su media móvil de 110 ms
        w = salida["w"][:, j]
        suave = np.convolve(w, np.ones(11) / 11, mode="same")
        res[f"vibracion_robot_{n}_dps"] = float(np.sqrt(np.mean((w - suave)[5:-5] ** 2)))
        salida[f"tau_{n}"] = tau
    return salida


# ----------------------------------------------------------------- gráficas
def graficar_sesion(nombre, extra, carpeta, sint):
    t, visto = extra["t"], extra["visto"]
    fig, ejes = plt.subplots(3, 1, figsize=(11, 8.5), sharex=True)
    for j, (ax, n) in enumerate(zip(ejes[:2], ("θ1 (hombro)", "θ2 (codo)"))):
        for a, b in tramos(~visto):
            ax.axvspan(t[a], t[min(b, len(t) - 1)], color="0.85", lw=0)
        ax.plot(t[visto], extra["crudo"][visto, j], ".", ms=3, color="tab:orange", label="cámara cruda")
        ax.plot(t, extra["kf"][:, j], "-", lw=1.4, color="tab:blue", label="Kalman")
        if extra["verdad"] is not None:
            ax.plot(t, extra["verdad"][:, j], "k--", lw=0.9, label="verdad (sintético)")
        ax.set_ylabel(f"{n} [°]")
        ax.grid(alpha=0.3)
    ejes[0].legend(loc="upper right", fontsize=8, ncol=3)
    ejes[0].set_title(f"{nombre}: ángulos de tu brazo (gris = la cámara no vio los 3 marcadores)")
    ax = ejes[2]
    ax.step(t, extra["c_crudo"][:, 1], where="post", color="tab:orange", lw=1, label="órdenes si fuera crudo")
    ax.step(t, extra["c_kf"][:, 1], where="post", color="tab:blue", lw=1, label="órdenes con Kalman")
    ax.set_ylabel("servo codo [°]")
    ax.set_xlabel("tiempo de la sesión [s]")
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(alpha=0.3)
    Rp.guardar_figura(fig, carpeta, f"20_teleop_{nombre}", sint)

    r = extra["robot"]
    if r is None:
        return
    fig, ejes = plt.subplots(2, 1, figsize=(11, 6), sharex=True)
    for j, (ax, n) in enumerate(zip(ejes, ("hombro", "codo"))):
        def sin_tendencia(y):
            ok = np.isfinite(y)
            p = np.polyfit(r["tr"][ok], y[ok], 1)
            return y - np.polyval(p, r["tr"])
        ax.plot(r["tr"], sin_tendencia(r["cmd_en_tr"][:, j]), color="tab:blue", lw=1.2,
                label="orden enviada")
        ax.plot(r["tr"], sin_tendencia(r["th_robot"][:, j]), color="tab:green", lw=1,
                label=f"robot (giroscopio integrado), retraso ≈ {r[f'tau_{n}'] * 1e3:.0f} ms")
        ax.set_ylabel(f"{n} [°] (sin tendencia)")
        ax.legend(loc="upper right", fontsize=8)
        ax.grid(alpha=0.3)
    ejes[0].set_title(f"{nombre}: lo que se le ordenó al robot vs lo que hizo (IMU del robot)")
    ejes[1].set_xlabel("tiempo de la sesión [s]")
    Rp.guardar_figura(fig, carpeta, f"21_robot_{nombre}", sint)


# ----------------------------------------------------------------- todo
def analizar(origen="reales"):
    entrada = CARPETAS[origen]
    salida = Rp.RAIZ / "resultados" / origen / "teleop"
    salida.mkdir(parents=True, exist_ok=True)
    rutas = sorted(entrada.glob("sesion_??.csv"))
    if not rutas:
        raise SystemExit(f"No hay sesiones en {entrada.relative_to(Rp.RAIZ)} (tecla G en teleop_camara.py)")
    sint = origen == "sinteticos"
    filas = []
    for ruta in rutas:
        try:
            if sum(1 for _ in open(ruta, encoding="utf-8")) < 31:
                print(f"  {ruta.name}: menos de 1 s grabado, se omite.")
                continue
            res, extra = analizar_sesion(ruta)
            filas.append(res)
            graficar_sesion(res["sesion"], extra, salida, sint)
        except Exception as e:                   # una sesión dañada no tumba las demás
            print(f"  {ruta.name}: no se pudo analizar ({type(e).__name__}: {e})")
    if not filas:
        raise SystemExit("Ninguna sesión se pudo analizar.")
    tabla = pd.DataFrame(filas)
    _guardar_caracterizacion_q(salida)
    nota_sint = ("\n\n> ⚠️ DATOS SINTÉTICOS: video generado por código para probar el análisis. "
                 "No son mediciones." if sint else "")
    Rp.guardar_tabla(tabla, salida, "metricas_teleop_completas", "Teleoperación: todas las métricas",
                     nota_sint)
    _guardar_resumen(tabla, salida, nota_sint)
    return salida


def _guardar_caracterizacion_q(salida):
    """Las 3 Q de la cámara, caracterizadas simulando el filtro real (no depende de R)."""
    from kalman_camara import caracterizar_q
    filas = []
    for cfg in CC.CONFIGS_Q_CAMARA:
        c = caracterizar_q(cfg["f_n_hz"])
        filas.append({"Q": cfg["nombre"], "f_n [Hz]": cfg["f_n_hz"],
                      "factor de ruido": round(c["factor_ruido"], 2),
                      "ganancia 1 Hz": round(c["ganancia_1Hz"], 2),
                      "retraso 1 Hz [ms]": round(c["retraso_ms_1Hz"], 1),
                      "ganancia 2 Hz": round(c["ganancia_2Hz"], 2),
                      "retraso 2 Hz [ms]": round(c["retraso_ms_2Hz"], 1),
                      "ganancia 8 Hz (temblor)": round(c["ganancia_8Hz"], 2),
                      "razon": cfg["razon"]})
    Rp.guardar_tabla(pd.DataFrame(filas), salida, "configuraciones_q_camara",
                     "Kalman de la cámara: las 3 configuraciones de Q",
                     "Simulación del filtro real a 30 cuadros/s (kalman_camara.caracterizar_q). "
                     "q = r·Δt·(2π f_n)⁴: como q es proporcional a r, este comportamiento NO "
                     "depende de la R medida. Factor de ruido = desviación de la salida / de la "
                     "entrada. Movimiento voluntario < 2 Hz; temblor fisiológico ~8–12 Hz.")


def _fmt(v, d=1):
    return "—" if v is None or (isinstance(v, float) and not np.isfinite(v)) else f"{v:.{d}f}"


def _guardar_resumen(tabla, salida, nota_sint):
    """Tabla corta para leer en voz alta: crudo vs Kalman, lado a lado."""
    L = ["# Teleoperación con cámara: crudo vs Kalman", "",
         "Se generó con `python python/analisis_teleop.py`. Las dos columnas salen de los "
         "MISMOS cuadros de video (mismas condiciones); solo cambia el método." + nota_sint, ""]
    for _, r in tabla.iterrows():
        L += [f"## {r['sesion']} (robot movido con: {r['robot_movido_con']})", "",
              f"- Duración {r['duracion_s']:.1f} s, {r['cuadros']} cuadros, **{r['fps']:.1f} fps** "
              f"(Δt = {r['dt_medio_ms']:.1f} ± {r['dt_std_ms']:.1f} ms, máx {r['dt_max_ms']:.0f} ms).",
              f"- La cámara vio los 3 marcadores en el **{r['visto_pct']:.1f} %** de los cuadros; "
              f"{int(r['oclusiones'])} oclusiones, la más larga de {r['oclusion_max_ms']:.0f} ms"
              + (f"; en el {r['solo_theta1_pct']:.1f} % de los cuadros solo se vio θ1 (muñeca tapada: "
                 f"Kalman actualizó solo θ1 y predijo θ2)." if r.get("solo_theta1_pct", 0) > 0 else "."), "",
              "| Métrica | Crudo (cámara) | Kalman |", "|---|---|---|",
              f"| Aspereza θ1 [°] (RMS 2.ª diferencia, mismos cuadros) | {_fmt(r['aspereza_theta1_crudo'], 3)} | "
              f"{_fmt(r['aspereza_theta1_kf'], 3)} |",
              f"| Aspereza θ2 [°] | {_fmt(r['aspereza_theta2_crudo'], 3)} | {_fmt(r['aspereza_theta2_kf'], 3)} |",
              f"| Órdenes al servo por segundo | {_fmt(r['ordenes_s_crudo'])} | {_fmt(r['ordenes_s_kf'])} |",
              f"| Cambios de dirección/s del servo hombro | {_fmt(r['cambios_dir_s_hombro_crudo'])} | "
              f"{_fmt(r['cambios_dir_s_hombro_kf'])} |",
              f"| Cambios de dirección/s del servo codo | {_fmt(r['cambios_dir_s_codo_crudo'])} | "
              f"{_fmt(r['cambios_dir_s_codo_kf'])} |",
              f"| Retraso respecto a crudo θ1 / θ2 [ms] | 0 | {_fmt(r['retraso_kf_theta1_ms'], 0)} / "
              f"{_fmt(r['retraso_kf_theta2_ms'], 0)} |"]
        if "rmse_theta1_kf" in r and np.isfinite(r.get("rmse_theta1_kf", np.nan)):
            L.append(f"| Error RMS vs verdad (cuadros vistos) θ1 / θ2 [°] (sintético) | {_fmt(r['rmse_theta1_crudo'], 2)} / "
                     f"{_fmt(r['rmse_theta2_crudo'], 2)} | {_fmt(r['rmse_theta1_kf'], 2)} / "
                     f"{_fmt(r['rmse_theta2_kf'], 2)} |")
        if np.isfinite(r.get("rmse_oclusion_theta1_kf", np.nan)):
            L.append(f"| Error RMS en oclusiones θ1 / θ2 [°] (sintético) | "
                     f"{_fmt(r['rmse_oclusion_theta1_crudo'], 2)} / {_fmt(r['rmse_oclusion_theta2_crudo'], 2)} | "
                     f"{_fmt(r['rmse_oclusion_theta1_kf'], 2)} / {_fmt(r['rmse_oclusion_theta2_kf'], 2)} |")
        L += ["", f"- Cómputo por cuadro: Kalman **{r['t_kalman_us_medio']:.0f} µs** "
              f"(p95 {r['t_kalman_us_p95']:.0f} µs)"
              + (f"; detección + Kalman **{r['t_proc_ms_medio']:.1f} ms** (p95 {r['t_proc_ms_p95']:.1f} ms) "
                 f"= {r['carga_pct']:.0f} % del tiempo entre cuadros." if "t_proc_ms_medio" in r else ".")]
        if np.isfinite(r.get("retraso_orden_robot_hombro_ms", np.nan)):
            L += [f"- Robot (giroscopios de la E1): retraso orden → robot "
                  f"**{r['retraso_orden_robot_hombro_ms']:.0f} ms** (hombro) / "
                  f"{r['retraso_orden_robot_codo_ms']:.0f} ms (codo); cámara → robot "
                  f"**{r['retraso_camara_robot_hombro_ms']:.0f} ms** / {r['retraso_camara_robot_codo_ms']:.0f} ms. "
                  f"Vibración del robot: {r['vibracion_robot_hombro_dps']:.2f} / "
                  f"{r['vibracion_robot_codo_dps']:.2f} °/s."]
        L.append("")
    con_robot = tabla[tabla["robot_movido_con"] != "sin robot"]
    if {"crudo", "kalman"} <= set(con_robot["robot_movido_con"]) and "vibracion_robot_hombro_dps" in con_robot:
        g = con_robot.groupby("robot_movido_con")[["vibracion_robot_hombro_dps", "vibracion_robot_codo_dps"]].mean()
        L += ["## Contraste en el robot: teleoperar con crudo vs con Kalman", "",
              "| Robot movido con | Vibración hombro [°/s] | Vibración codo [°/s] |", "|---|---|---|"]
        for fuente, v in g.iterrows():
            L.append(f"| {fuente} | {v.iloc[0]:.2f} | {v.iloc[1]:.2f} |")
        L.append("")
    L += ["## Las 3 configuraciones de Q", "",
          "Ver `configuraciones_q_camara.md`: menor f_n = más suave (menos ruido y temblor) "
          "pero más retraso. Q_media (f_n = 3 Hz) deja pasar el movimiento voluntario (< 2 Hz) "
          "con < 16 ms de retraso y reduce el temblor de 8 Hz a la mitad.", "",
          "## Cómo leerlo", "",
          "- **Aspereza**: si el ángulo cambiara a velocidad constante daría 0. El temblor de la "
          "detección la sube. Menor = más suave.",
          "- **Cambios de dirección/s**: cada uno es el servo yendo y viniendo: eso es el temblor que "
          "se ve y se oye en el robot.",
          "- **Retraso**: el precio de suavizar (Q más baja = más suave y más tarde). Es pequeño "
          "porque el modelo de velocidad casi constante sigue las rampas sin retraso: solo se "
          "atrasa cuando la velocidad cambia.",
          "- **Oclusión**: la cámara cruda se queda congelada; Kalman sigue con su modelo de velocidad "
          "casi constante (sirve para huecos cortos; en huecos largos la predicción se aleja).",
          "- **Límite**: la latencia teléfono → PC (WiFi) no se puede medir con estos datos; el retraso "
          "cámara → robot cuenta desde que el cuadro LLEGA al PC.", ""]
    (salida / "resumen_teleop.md").write_text("\n".join(L), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sinteticos", action="store_true", help="analizar datos/sinteticos/teleop")
    args = ap.parse_args()
    carpeta = analizar("sinteticos" if args.sinteticos else "reales")
    print(f"Listo: {carpeta.relative_to(Rp.RAIZ)}/resumen_teleop.md")
    print((carpeta / "resumen_teleop.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
