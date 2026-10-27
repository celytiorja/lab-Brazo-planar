"""ENTREGA 2 — Filtro de Kalman: ajuste de Q, validación y comparación.

    python python/analisis_e2.py                                    (datos reales)
    python python/analisis_e2.py --manifiesto datos/sinteticos/manifiesto.json

Requiere haber corrido antes analisis_e1.py (de ahí sale R).

Flujo (sin editar nada a mano):
  1. AJUSTE: con los registros de ajuste se prueban las configuraciones de Q de
     config_kalman.py y se elige una con una regla numérica fija.
  2. VALIDACIÓN: con registros DISTINTOS se evalúa la Q elegida contra la
     integración directa y la media móvil, en las mismas condiciones.
  3. DIAGNÓSTICO: innovaciones (NIS), simetría/positividad de P, ganancia K,
     compromiso Q/R y aceleración angular numérica.
"""
import argparse
import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import chi2

import config_kalman as CK
import metricas as Me
import reporte as Rp
from datos_imu import bias_reposo, cargar, theta_de_phi
from estimadores import IntegracionDirecta, KalmanBrazo, MediaMovilIntegracion, ejecutar


def cargar_R(man):
    ruta = Rp.carpeta_resultados(man, "e1") / "R.json"
    if not ruta.exists():
        raise SystemExit("Falta R. Ejecuta primero:  python python/analisis_e1.py "
                         + (f"--manifiesto {man['_ruta']}" if "sintet" in man["_ruta"] else ""))
    return json.loads(ruta.read_text(encoding="utf-8"))


def crear_metodos(reg, R, usar_incl, est_bias, configs, diagnostico=False):
    """Todos los métodos con la MISMA condición inicial (φ0) y el MISMO sesgo (b)."""
    b = bias_reposo(reg)
    phi0 = reg.phi_cmd[0]
    metodos = [IntegracionDirecta(phi0, b)]
    metodos += [MediaMovilIntegracion(phi0, b, N) for N in CK.VENTANAS_MEDIA_MOVIL]
    for c in configs:
        metodos.append(KalmanBrazo(phi0, b, R, c["q"], usar_incl, est_bias,
                                   nombre=f"Kalman {c['nombre']}", guardar_diagnostico=diagnostico))
    return metodos, b


def mascara_reposo(reg):
    """Reposo de verdad: fase 0 o 2 Y consigna quieta hace ≥ 0.5 s (el servo ya
    frenó). Sin esto, el frenado al inicio del reposo final cuenta como 'ruido'."""
    estac = Me.ventanas_estacionarias(reg.crudo[["cmd_h", "cmd_c"]].to_numpy(), reg.t)
    return np.isin(reg.fase, (0, 2)) & estac


def verdad(reg, ruta):
    """Solo existe en datos sintéticos: el ángulo VERDADERO."""
    v = ruta.with_name(ruta.stem + "_verdad.csv")
    if not v.exists():
        return None
    d = pd.read_csv(v)
    return theta_de_phi(d[["phi1_deg", "phi2_deg"]].to_numpy())


def evaluar(reg, ruta, metodos, b):
    """Corre cada método sobre el registro y calcula las métricas por articulación."""
    fs = 1 / reg.dt[1:].mean()
    mov = reg.fase == 1 if (reg.fase == 1).any() else np.ones(reg.n, bool)
    estac = Me.ventanas_estacionarias(reg.crudo[["cmd_h", "cmd_c"]].to_numpy(), reg.t)
    reposo = mascara_reposo(reg)
    w_corr = reg.w - b
    th_ver = verdad(reg, ruta)
    salidas, filas = {}, []
    for m in metodos:
        phi, omega, t_calc = ejecutar(m, reg)
        th = theta_de_phi(phi)
        salidas[m.nombre] = {"theta": th, "omega": omega, "phi": phi, "metodo": m,
                             "t_calc": t_calc}
    th_dir = salidas["Integración directa"]["theta"]
    for nombre, s in salidas.items():
        alfa = Me.derivada(s["omega"], reg.dt)
        deriva = Me.deriva_final(s["phi"], reg.fase)
        for j in (0, 1):
            directa = nombre == "Integración directa"
            fila = {
                "archivo": reg.nombre, "metodo": nombre, "eslabon": j + 1,
                "ruido_omega_reposo_dps": float(np.std(s["omega"][reposo, j], ddof=1)),
                "retraso_omega_ms": 0.0 if directa else
                Me.correlacion_cruzada(w_corr[mov, j], s["omega"][mov, j], fs, 0.3)[2] * 1e3,
                "retraso_theta_ms": 0.0 if directa else
                Me.correlacion_cruzada(th_dir[mov, j], s["theta"][mov, j], fs, 0.3)[2] * 1e3,
                "error_estacionario_rms_deg": Me.rmse(s["theta"][:, j], reg.theta_cmd[:, j], estac),
                "deriva_final_deg": float(deriva[j]),
                "ruido_alfa_reposo_dps2": float(np.std(alfa[reposo, j], ddof=1)),
                "t_calculo_us": float(np.mean(s["t_calc"][1:])),
            }
            if th_ver is not None:
                fila["rmse_vs_verdad_deg"] = Me.rmse(s["theta"][:, j], th_ver[:, j])
            filas.append(fila)
    return salidas, filas


def consistencia(reg, salida, m_dim):
    """Pruebas estadísticas de las innovaciones y de P para un Kalman."""
    d = salida["metodo"].diag
    nis = np.array(d["nis"])
    lo, hi = chi2.ppf([0.025, 0.975], m_dim)
    innov = np.array(d["innovacion"])
    z = innov / np.sqrt(np.mean(innov**2, axis=0))
    r1 = [float(np.corrcoef(z[1:, i], z[:-1, i])[0, 1]) for i in range(z.shape[1])]
    reposo = mascara_reposo(reg)[1:]
    return {
        "archivo": reg.nombre, "metodo": salida["metodo"].nombre,
        "nis_medio": float(nis.mean()), "nis_esperado": m_dim,
        "nis_medio_reposo": float(nis[reposo].mean()) if reposo.any() else np.nan,
        "nis_medio_movimiento": float(nis[~reposo].mean()) if (~reposo).any() else np.nan,
        "frac_nis_en_95": float(np.mean((nis >= lo) & (nis <= hi))),
        "autocorr_innov_lag1": float(np.mean(r1)),
        "banda_blancura_95": 1.96 / np.sqrt(len(nis)),
        "max_asimetria_P": float(np.max(d["asimetria"])),
        "min_autovalor_P": float(np.min(d["min_autovalor"])),
    }


def ganancia_estacionaria(q, r, dt):
    """Para ω con solo giroscopio, Kalman se reduce a ω̂ ← ω̂ + K(z − ω̂): un filtro
    paso bajo de primer orden. Se itera la Riccati escalar hasta converger y se
    devuelve K y la frecuencia de corte equivalente f_c = −ln(1−K)/(2πΔt)."""
    p = 1.0
    for _ in range(10000):
        p_pred = p + q * dt
        k = p_pred / (p_pred + r)
        p_nuevo = (1 - k) * p_pred
        if abs(p_nuevo - p) < 1e-15:
            break
        p = p_nuevo
    return k, -np.log(1 - k) / (2 * np.pi * dt)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifiesto", default=None)
    args = ap.parse_args()
    man = Rp.cargar_manifiesto(args.manifiesto)
    sal = Rp.carpeta_resultados(man, "e2")
    Rinfo = cargar_R(man)
    R = np.array(Rinfo["R"])
    usar_incl = R.shape[0] == 4
    est_bias = usar_incl and CK.ESTIMAR_BIAS_SI_HAY_INCLINACION
    m_dim = R.shape[0]
    print(f"R {R.shape} de {Rinfo['archivo']} · inclinación={usar_incl} · sesgo en estado={est_bias}")

    dt_nominal = 1 / Rinfo["fs_hz"]
    configs = [CK.resolver_q(c, R, dt_nominal) for c in CK.CONFIGS_Q]
    for c in configs:
        print(f"  {c['nombre']}: f_c = {c['f_corte_hz']} Hz -> q = {c['q']:.4g} °²/s³")
    rutas_aj = [Rp.ruta_dato(p) for p in man["ajuste"]]
    rutas_val = [Rp.ruta_dato(p) for p in man["validacion"]]
    sint = False

    # ------------------------------------------------------------------ 1. AJUSTE
    filas_aj, filas_cons, salidas_aj = [], [], {}
    for ruta in rutas_aj:
        reg = cargar(ruta)
        sint |= reg.sintetico
        metodos, b = crear_metodos(reg, R, usar_incl, est_bias, configs, diagnostico=True)
        s, f = evaluar(reg, ruta, metodos, b)
        filas_aj += f
        salidas_aj[reg.nombre] = (reg, s)
        for nombre, salida in s.items():
            if nombre.startswith("Kalman"):
                filas_cons.append(consistencia(reg, salida, m_dim))
    df_aj = pd.DataFrame(filas_aj)
    nota = Rp.encabezado(man)
    Rp.guardar_tabla(df_aj, sal, "metricas_e2_ajuste", "Métricas con registros de AJUSTE", nota)
    Rp.guardar_tabla(pd.DataFrame(filas_cons), sal, "consistencia_kalman",
                     "Consistencia del filtro (innovaciones y covarianza)",
                     f"NIS = yᵀS⁻¹y ~ χ²({m_dim}) si el modelo es correcto: media ≈ {m_dim} y ~95 % "
                     "de las muestras dentro de la banda. autocorr_innov_lag1 ≈ 0 si las "
                     "innovaciones son blancas. P debe ser simétrica (asimetría ≈ 0) y "
                     "positiva (autovalor mínimo > 0).\n\n" + nota)

    # Regla de selección
    resumen = (df_aj[df_aj.metodo.str.startswith("Kalman")]
               .groupby("metodo")[["retraso_omega_ms", "ruido_omega_reposo_dps",
                                   "error_estacionario_rms_deg", "deriva_final_deg"]]
               .agg(lambda x: float(np.mean(np.abs(x)))).reset_index())
    validas = resumen[resumen.retraso_omega_ms <= CK.RETRASO_MAX_MS]
    if len(validas):
        elegida = validas.sort_values("ruido_omega_reposo_dps").iloc[0]
        motivo = (f"menor ruido de ω en reposo entre las configuraciones con retraso de ω "
                  f"≤ {CK.RETRASO_MAX_MS} ms (promedio en registros de ajuste)")
    else:
        elegida = resumen.sort_values("retraso_omega_ms").iloc[0]
        motivo = "ninguna cumple el retraso máximo: se toma la de menor retraso"
    cfg_elegida = next(c for c in configs if f"Kalman {c['nombre']}" == elegida.metodo)
    seleccion = {"configuracion": cfg_elegida, "regla": motivo,
                 "retraso_max_ms": CK.RETRASO_MAX_MS,
                 "configuraciones_evaluadas": configs,
                 "resumen_ajuste": resumen.to_dict(orient="records"),
                 "R": R.tolist(), "registros_ajuste": man["ajuste"],
                 "commit": Rp.commit_actual()}
    Rp.guardar_json(seleccion, sal, "seleccion_Q")
    Rp.guardar_tabla(resumen, sal, "resumen_seleccion_Q", "Selección de Q (promedios de ajuste)",
                     f"Elegida: **{cfg_elegida['nombre']}** (f_c = {cfg_elegida['f_corte_hz']} Hz, "
                     f"q = {cfg_elegida['q']:.4g} °²/s³). Regla: {motivo}.")
    print(f"Q elegida: {cfg_elegida['nombre']} (q={cfg_elegida['q']:g})")

    # ------------------------------------------------------------------ 2. VALIDACIÓN
    filas_val, salidas_val = [], {}
    for ruta in rutas_val:
        reg = cargar(ruta)
        sint |= reg.sintetico
        metodos, b = crear_metodos(reg, R, usar_incl, est_bias, [cfg_elegida])
        s, f = evaluar(reg, ruta, metodos, b)
        filas_val += f
        salidas_val[reg.nombre] = (reg, s)
    df_val = pd.DataFrame(filas_val)
    Rp.guardar_tabla(df_val, sal, "metricas_e2_validacion",
                     f"VALIDACIÓN final (Q elegida: {cfg_elegida['nombre']})", nota)
    numericas = df_val.drop(columns=["archivo", "eslabon"])
    agregado = numericas.groupby("metodo").agg(lambda x: float(np.mean(np.abs(x)))).reset_index()
    Rp.guardar_tabla(agregado, sal, "metricas_e2_validacion_resumen",
                     "Validación: promedio de |métrica| sobre archivos y eslabones", nota)

    # ------------------------------------------------------------------ 3. GRÁFICAS
    graficar_comparacion(salidas_aj, sal, sint, "10_ajuste_configuraciones_Q",
                         "AJUSTE: configuraciones de Q")
    graficar_comparacion(salidas_val, sal, sint, "15_validacion_comparacion",
                         f"VALIDACIÓN: {cfg_elegida['nombre']} vs métodos base")
    graficar_diagnostico(salidas_aj, cfg_elegida, m_dim, sal, sint)
    graficar_aceleracion(salidas_aj, sal, sint)
    graficar_compromiso(rutas_aj, R, usar_incl, est_bias, cfg_elegida, configs, sal, sint, nota)
    print(f"Listo. Resultados en {sal}")


def _elegir_registro(salidas, preferido="seno_rapido"):
    for nombre in salidas:
        if preferido in nombre:
            return salidas[nombre]
    return next(iter(salidas.values()))


def graficar_comparacion(salidas, sal, sint, nombre_fig, titulo):
    for reg_nombre, (reg, s) in salidas.items():
        fig, axs = plt.subplots(2, 1, figsize=(12, 7), sharex=True)
        for j in (0, 1):
            axs[j].plot(reg.t, reg.theta_cmd[:, j], "k--", lw=1, label="consigna (no es medición)")
            for nombre, d in s.items():
                estilo = "-" if nombre.startswith("Kalman") else ":"
                axs[j].plot(reg.t, d["theta"][:, j], estilo, lw=1.1, label=nombre)
            axs[j].set_ylabel(f"θ{j+1} [°]")
            axs[j].legend(fontsize=7, loc="upper right", ncol=2)
        axs[1].set_xlabel("t [s]")
        fig.suptitle(f"{titulo} — {reg_nombre}")
        Rp.guardar_figura(fig, sal, f"{nombre_fig}_{reg_nombre}", sint)


def graficar_diagnostico(salidas_aj, cfg, m_dim, sal, sint):
    reg, s = _elegir_registro(salidas_aj)
    d = s[f"Kalman {cfg['nombre']}"]["metodo"].diag
    t = reg.t[1:]
    innov = np.array(d["innovacion"])
    nis = np.array(d["nis"])
    lo, hi = chi2.ppf([0.025, 0.975], m_dim)
    fig, axs = plt.subplots(3, 1, figsize=(11, 8), sharex=True)
    for i in range(innov.shape[1]):
        axs[0].plot(t, innov[:, i], lw=0.6, label=f"y{i+1}")
    axs[0].set_ylabel("innovación y = z − Hx̂⁻")
    axs[0].legend(fontsize=8)
    axs[1].semilogy(t, nis, lw=0.6)
    axs[1].axhline(m_dim, color="g", label=f"esperado = {m_dim}")
    axs[1].axhspan(lo, hi, color="g", alpha=0.1, label="banda χ² 95 %")
    axs[1].set_ylabel("NIS")
    axs[1].legend(fontsize=8)
    axs[2].plot(t, reg.fase[1:], "k", lw=1)
    axs[2].set_ylabel("fase")
    axs[2].set_xlabel("t [s]")
    fig.suptitle(f"Innovaciones y NIS — {cfg['nombre']} — {reg.nombre}")
    Rp.guardar_figura(fig, sal, "11_innovaciones_nis", sint)

    Pd = np.array(d["P_diag"])
    K = np.array(d["K"])
    fig, axs = plt.subplots(1, 2, figsize=(12, 4))
    nombres = ["P φ1", "P ω1", "P φ2", "P ω2"] if Pd.shape[1] == 4 else [f"P{i}" for i in range(Pd.shape[1])]
    for i in range(Pd.shape[1]):
        axs[0].semilogy(t, Pd[:, i], label=nombres[i])
    axs[0].set_title("Diagonal de P (incertidumbre del estado)")
    axs[0].set_xlabel("t [s]")
    axs[0].legend(fontsize=8)
    n = Pd.shape[1] // 2
    axs[1].plot(t, K[:, 1, 0], label="K ω1 ← giro1")
    axs[1].plot(t, K[:, n + 1, 1], label="K ω2 ← giro2")
    axs[1].plot(t, K[:, 0, 0], label="K φ1 ← giro1")
    axs[1].set_title("Ganancia de Kalman: converge a un valor estacionario")
    axs[1].set_xlabel("t [s]")
    axs[1].legend(fontsize=8)
    Rp.guardar_figura(fig, sal, "12_P_y_K", sint)


def graficar_aceleracion(salidas_aj, sal, sint):
    reg, s = _elegir_registro(salidas_aj)
    reposo = mascara_reposo(reg)
    dt_med = reg.dt[1:].mean()
    b = bias_reposo(reg)
    w_c = reg.w - b
    fuentes = {"giro crudo, diferencia hacia atrás": Me.derivada(w_c, reg.dt, "atras"),
               "giro crudo, diferencia central": Me.derivada(w_c, reg.dt, "central")}
    for nombre, d in s.items():
        if nombre != "Integración directa":
            fuentes[f"{nombre}, hacia atrás"] = Me.derivada(d["omega"], reg.dt, "atras")
    sigma_w = np.std(w_c[reposo, 0], ddof=1)   # ruido del giro con el brazo quieto
    filas = []
    for nombre, a in fuentes.items():
        filas.append({"fuente": nombre, "sigma_alfa_reposo_dps2": float(np.std(a[reposo, 0], ddof=1))})
    filas.append({"fuente": "TEÓRICO hacia atrás: √2·σω/Δt",
                  "sigma_alfa_reposo_dps2": float(Me.amplificacion_teorica(dt_med, "atras") * sigma_w)})
    filas.append({"fuente": "TEÓRICO central: σω/(√2·Δt)",
                  "sigma_alfa_reposo_dps2": float(Me.amplificacion_teorica(dt_med, "central") * sigma_w)})
    Rp.guardar_tabla(pd.DataFrame(filas), sal, "aceleracion_angular",
                     f"Aceleración angular numérica — ruido en reposo (eslabón 1, {reg.nombre})",
                     f"σω en reposo = {sigma_w:.4f} °/s, Δt = {dt_med*1e3:.2f} ms. Derivar divide "
                     f"por Δt: el ruido se multiplica por ≈ {Me.amplificacion_teorica(dt_med):.0f}.")

    mov = np.flatnonzero(reg.fase == 1)
    z = slice(mov[0], mov[0] + min(400, len(mov))) if len(mov) else slice(0, 400)
    fig, ax = plt.subplots(figsize=(11, 4.5))
    for nombre, a in fuentes.items():
        if "central" in nombre or "Q_alta" in nombre:
            continue
        ax.plot(reg.t[z], a[z, 0], lw=0.8, label=nombre)
    ax.set_ylabel("α1 [°/s²]")
    ax.set_xlabel("t [s]")
    ax.set_title("Aceleración angular por diferenciación numérica: el ruido crece al derivar")
    ax.legend(fontsize=7)
    Rp.guardar_figura(fig, sal, "13_aceleracion_angular", sint)


def graficar_compromiso(rutas_aj, R, usar_incl, est_bias, cfg, configs, sal, sint, nota):
    """Barrido de q: cómo cambian ruido, retraso y ancho de banda con la relación Q/R."""
    filas = []
    for ruta in rutas_aj:
        reg = cargar(ruta)
        b = bias_reposo(reg)
        fs = 1 / reg.dt[1:].mean()
        mov = reg.fase == 1
        reposo = mascara_reposo(reg)
        dt = reg.dt[1:].mean()
        for f_obj in CK.BARRIDO_F_CORTE_HZ:
            q = CK.resolver_q({"f_corte_hz": f_obj}, R, dt)["q"]
            kf = KalmanBrazo(reg.phi_cmd[0], b, R, q, usar_incl, est_bias)
            phi, omega, _ = ejecutar(kf, reg)
            k, fc = ganancia_estacionaria(q, float(np.mean(np.diag(R)[:2])), dt)
            filas.append({"archivo": reg.nombre, "f_objetivo_hz": f_obj, "q": q,
                          "q_dt_sobre_r": q * dt / R[0, 0],
                          "K_omega_estacionaria": k, "f_corte_hz": fc,
                          "ruido_omega_reposo_dps": float(np.std(omega[reposo, 0], ddof=1)),
                          "retraso_omega_ms": Me.correlacion_cruzada(
                              (reg.w - b)[mov, 0], omega[mov, 0], fs, 0.3)[2] * 1e3})
    df = pd.DataFrame(filas)
    Rp.guardar_tabla(df, sal, "compromiso_Q_R", "Barrido de q (compromiso Q/R)", nota)
    g = df.groupby("f_objetivo_hz").mean(numeric_only=True).reset_index()
    fig, ax1 = plt.subplots(figsize=(9, 4.8))
    ax1.loglog(g.q, g.ruido_omega_reposo_dps, "o-", color="tab:blue", label="ruido ω en reposo")
    ax1.set_xlabel("q [°²/s³]  (R fijo, de la Entrega 1)")
    ax1.set_ylabel("ruido ω en reposo [°/s]", color="tab:blue")
    ax2 = ax1.twinx()
    ax2.semilogx(g.q, g.retraso_omega_ms, "s-", color="tab:red", label="retraso de ω")
    ax2.axhline(CK.RETRASO_MAX_MS, color="tab:red", ls=":", lw=1)
    ax2.set_ylabel("retraso de ω [ms]", color="tab:red")
    ax1.axvline(cfg["q"], color="k", ls="--", lw=1)
    ax1.text(cfg["q"], ax1.get_ylim()[1], f" elegida: {cfg['nombre']}", va="top", fontsize=8)
    for c in configs:
        ax1.axvline(c["q"], color="0.7", lw=0.8)
    ax3 = ax1.secondary_xaxis("top", functions=(
        lambda q: np.interp(np.log10(q), np.log10(g.q), g.f_corte_hz),
        lambda f: 10 ** np.interp(f, g.f_corte_hz, np.log10(g.q))))
    ax3.set_xlabel("frecuencia de corte equivalente [Hz]")
    fig.suptitle("Compromiso Q/R: más q = más ancho de banda y menos retraso, pero más ruido", y=1.02)
    Rp.guardar_figura(fig, sal, "14_compromiso_Q_R", sint)


if __name__ == "__main__":
    main()
