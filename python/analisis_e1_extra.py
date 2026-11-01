"""ENTREGA 1 — Análisis complementarios (los llama analisis_e1.py).

Cada función responde UNA pregunta de la guía y guarda su tabla/gráfica:
  sensibilidad_ventana   ¿Cómo cambian ruido y retraso al variar la ventana N?
  variantes_sesgo        ¿Qué pasa si no se compensa el sesgo, o se toma de otro archivo?
  dt_real_vs_nominal     ¿Importa usar el Δt_k real del timestamp en vez de 1/fs?
  ruido_vs_deriva        Separar el ruido de alta frecuencia de la deriva acumulada.
  estructura_R           ¿El ruido es estacionario? ¿R diagonal o completa?
  repetibilidad          ¿Dos repeticiones del mismo perfil dan lo mismo?
  degradacion_movimiento ¿El ruido aparente crece cuando el brazo se mueve?
  requisitos_kalman      Qué debe lograr el Kalman de la Entrega 2 (en números).
"""
import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")   # solo genera archivos: no abre ventanas
import matplotlib.pyplot as plt  # noqa: E402
from scipy.signal import savgol_filter
from scipy.stats import levene

import config_imu as C
import config_kalman as CK
import metricas as Me
import reporte as Rp
from datos_imu import bias_reposo, cargar, theta_de_phi
from estimadores import IntegracionDirecta, MediaMovilIntegracion, ejecutar

VENTANAS_BARRIDO = [1, 3, 5, 9, 15, 21, 31, 51]
VENTANA_ESTACIONARIEDAD_S = 5.0
UMBRAL_CORRELACION = 0.1


def _preparar(din):
    """Máscaras y referencias comunes del registro dinámico."""
    fs = 1 / din.dt[1:].mean()
    mov = din.fase == 1 if (din.fase == 1).any() else np.ones(din.n, bool)
    estac = Me.ventanas_estacionarias(din.crudo[["cmd_h", "cmd_c"]].to_numpy(), din.t)
    reposo = np.isin(din.fase, (0, 2)) & estac
    return fs, mov, estac, reposo


def _theta(metodo, reg):
    phi, omega, _ = ejecutar(metodo, reg)
    return theta_de_phi(phi), phi, omega


# --------------------------------------------------------------------------- a
def sensibilidad_ventana(est, din, b_est, sal, sint):
    fs, mov, estac, _ = _preparar(din)
    b = bias_reposo(din)
    phi0 = din.phi_cmd[0]
    th_dir, _, _ = _theta(IntegracionDirecta(phi0, b), din)
    dt_ms = 1e3 / fs
    filas = []
    for N in VENTANAS_BARRIDO:
        th, phi, _ = _theta(MediaMovilIntegracion(phi0, b, N), din)
        _, _, om_est = _theta(MediaMovilIntegracion([0, 0], b_est, N), est)
        deriva = Me.deriva_final(phi, din.fase)
        for j in (0, 1):
            filas.append({
                "N": N, "eslabon": j + 1,
                "ruido_omega_reposo_dps": float(np.std(om_est[N:, j], ddof=1)),
                "ruido_teorico_dps": float(np.std(est.w[:, j] - b_est[j], ddof=1) / np.sqrt(N)),
                "retraso_ms": 0.0 if N == 1 else
                Me.correlacion_cruzada(th_dir[mov, j], th[mov, j], fs)[2] * 1e3,
                "retraso_teorico_ms": (N - 1) / 2 * dt_ms,
                "error_estacionario_rms_deg": Me.rmse(th[:, j], din.theta_cmd[:, j], estac),
                "deriva_final_deg": float(deriva[j]),
            })
    df = pd.DataFrame(filas)
    Rp.guardar_tabla(df, sal, "sensibilidad_ventana", "Sensibilidad al tamaño de ventana N",
                     "Media móvil de ruido blanco: σ_N = σ/√N y retraso (N−1)/2 muestras. "
                     "La deriva final NO cambia con N: promediar no quita el sesgo.")

    fig, axs = plt.subplots(1, 2, figsize=(12, 4.5))
    for j, m in ((1, "o"), (2, "s")):
        g = df[df.eslabon == j]
        axs[0].plot(g.N, g.retraso_ms, m, label=f"medido eslabón {j}")
        axs[1].plot(g.retraso_ms, g.ruido_omega_reposo_dps, m + "-", label=f"eslabón {j}")
        for _, r in g.iterrows():
            if j == 1:
                axs[1].annotate(f"N={int(r.N)}", (r.retraso_ms, r.ruido_omega_reposo_dps), fontsize=7,
                                xytext=(3, 3), textcoords="offset points")
    g = df[df.eslabon == 1]
    axs[0].plot(g.N, g.retraso_teorico_ms, "k--", label="teórico (N−1)/2·Δt")
    axs[0].set_xlabel("ventana N [muestras]")
    axs[0].set_ylabel("retraso [ms]")
    axs[0].legend()
    axs[0].set_title("Retraso que introduce la ventana")
    axs[1].plot(g.retraso_teorico_ms, g.ruido_teorico_dps, "k--", label="teórico σ/√N")
    axs[1].set_xlabel("retraso [ms]")
    axs[1].set_ylabel("ruido de ω en reposo [°/s]")
    axs[1].set_yscale("log")
    axs[1].legend()
    axs[1].set_title("Compromiso suavizado–retardo")
    Rp.guardar_figura(fig, sal, "10_sensibilidad_ventana", sint)
    return df


# --------------------------------------------------------------------------- b
def variantes_sesgo(est, din, sal):
    fs, mov, estac, _ = _preparar(din)
    phi0 = din.phi_cmd[0]
    variantes = {"sin compensar": np.zeros(2),
                 "sesgo del archivo estático": est.w.mean(axis=0),
                 "sesgo del reposo inicial (mismo archivo)": bias_reposo(din)}
    filas = []
    for nombre_v, b in variantes.items():
        metodos = [IntegracionDirecta(phi0, b)] + [MediaMovilIntegracion(phi0, b, N)
                                                   for N in CK.VENTANAS_MEDIA_MOVIL]
        for m in metodos:   # MISMO tratamiento del sesgo para todos los métodos
            th, phi, _ = _theta(m, din)
            deriva = Me.deriva_final(phi, din.fase)
            for j in (0, 1):
                filas.append({"variante_sesgo": nombre_v, "metodo": m.nombre, "eslabon": j + 1,
                              "sesgo_usado_dps": float(b[j]),
                              "deriva_final_deg": float(deriva[j]),
                              "error_estacionario_rms_deg": Me.rmse(th[:, j], din.theta_cmd[:, j], estac)})
    df = pd.DataFrame(filas)
    Rp.guardar_tabla(df, sal, "variantes_sesgo", "Variantes de compensación del sesgo",
                     "El sesgo se aplica IGUAL a todos los métodos de cada variante. El sesgo cambia "
                     "entre encendidos y con la temperatura: el del reposo del mismo archivo es el "
                     "más cercano al real.")
    return df


# --------------------------------------------------------------------------- c
def dt_real_vs_nominal(registros, sal):
    filas = []
    for reg in registros:
        b = bias_reposo(reg)
        w = reg.w - b
        dt_nom = np.where(np.arange(reg.n) == 0, 0.0, 1 / C.FS_HZ)
        phi_real = np.cumsum(reg.dt[:, None] * w, axis=0)
        phi_nom = np.cumsum(dt_nom[:, None] * w, axis=0)
        dif = phi_real - phi_nom
        for j in (0, 1):
            filas.append({"archivo": reg.nombre, "eslabon": j + 1, "perdidas": reg.perdidas,
                          "dt_max_ms": float(reg.dt.max() * 1e3),
                          "diferencia_final_deg": float(dif[-1, j]),
                          "diferencia_max_deg": float(np.max(np.abs(dif[:, j])))})
    df = pd.DataFrame(filas)
    Rp.guardar_tabla(df, sal, "dt_real_vs_nominal", "Integrar con Δt_k real vs Δt = 1/fs",
                     "Con Δt nominal, cada muestra perdida hace 'desaparecer' 10 ms de giro y el "
                     "ángulo queda corrido; con el Δt_k del timestamp ese tramo se integra completo.")
    return df


# --------------------------------------------------------------------------- d
def ruido_vs_deriva(est, sal, t_corte=10.0):
    """En reposo y FUERA de muestra (sesgo de los primeros 10 s, evaluado después):
    pendiente de la recta = deriva; lo que queda alrededor de la recta = ruido."""
    corte = est.t <= t_corte
    b = est.w[corte].mean(axis=0)
    prueba = ~corte
    sub = cargar_sub(est, prueba)
    filas = []
    for m in [IntegracionDirecta([0, 0], b)] + [MediaMovilIntegracion([0, 0], b, N)
                                               for N in CK.VENTANAS_MEDIA_MOVIL]:
        phi, omega, _ = ejecutar(m, sub)
        t = sub.t
        for j in (0, 1):
            pendiente = np.polyfit(t, phi[:, j], 1)[0]
            filas.append({"metodo": m.nombre, "eslabon": j + 1,
                          "ruido_alta_frec_angulo_deg": Me.ruido(phi[:, j]),
                          "ruido_omega_dps": float(np.std(omega[:, j], ddof=1)),
                          "deriva_deg_por_min": float(pendiente * 60),
                          "angulo_final_deg": float(phi[-1, j])})
    df = pd.DataFrame(filas)
    Rp.guardar_tabla(df, sal, "ruido_vs_deriva", "Ruido de alta frecuencia vs deriva (reposo)",
                     "La media móvil baja el ruido pero NO cambia la pendiente (deriva): son "
                     "problemas distintos. Evaluado fuera de muestra (sesgo de los primeros 10 s).")
    return df


def cargar_sub(reg, mascara):
    """Copia de un Registro con solo las muestras de `mascara` (Δt recalculado)."""
    from dataclasses import replace
    t = reg.t[mascara] - reg.t[mascara][0]
    return replace(reg, crudo=reg.crudo[mascara].reset_index(drop=True), t=t,
                   dt=np.concatenate([[0.0], np.diff(t)]), fase=reg.fase[mascara],
                   perfil=reg.perfil[mascara], w=reg.w[mascara],
                   acc={k: v[mascara] for k, v in reg.acc.items()},
                   gyro={k: v[mascara] for k, v in reg.gyro.items()},
                   theta_cmd=reg.theta_cmd[mascara], phi_cmd=reg.phi_cmd[mascara],
                   phi_acc=None if reg.phi_acc is None else reg.phi_acc[mascara])


# --------------------------------------------------------------------------- e
def estructura_R(est, sal, sint):
    canales = {"w1": est.w[:, 0], "w2": est.w[:, 1]}
    for i in (1, 2):
        for k, e in enumerate("xyz"):
            canales[f"a{e}{i}"] = est.acc[i][:, k]
    nombres = list(canales)
    X = np.column_stack([canales[c] for c in nombres])
    rho = np.corrcoef(X.T)

    # Estacionariedad: ¿la varianza es la misma en cada tramo de 5 s?
    n_vent = int(VENTANA_ESTACIONARIEDAD_S * C.FS_HZ)
    filas = []
    for c in ("w1", "w2"):
        x = canales[c]
        trozos = [x[k:k + n_vent] for k in range(0, len(x) - n_vent + 1, n_vent)]
        varianzas = np.array([np.var(t, ddof=1) for t in trozos])
        medias = np.array([np.mean(t) for t in trozos])
        p = float(levene(*trozos).pvalue) if len(trozos) > 1 else np.nan
        filas.append({"canal": c, "ventanas_5s": len(trozos),
                      "varianza_total": float(np.var(x, ddof=1)),
                      "varianza_min": float(varianzas.min()), "varianza_max": float(varianzas.max()),
                      "cociente_max_min": float(varianzas.max() / varianzas.min()),
                      "media_min": float(medias.min()), "media_max": float(medias.max()),
                      "levene_p": p, "varianza_estacionaria": bool(p > 0.05)})
    r12 = float(rho[0, 1])
    decision = "diagonal" if abs(r12) < UMBRAL_CORRELACION else "completa"
    df = pd.DataFrame(filas)
    Rp.guardar_tabla(df, sal, "estructura_R", "Estructura de R: estacionariedad y correlación",
                     f"Correlación w1–w2 = {r12:+.3f} → |ρ| {'<' if decision == 'diagonal' else '≥'} "
                     f"{UMBRAL_CORRELACION}: R **{decision}** es suficiente. Levene p > 0.05 = no hay "
                     "evidencia de que la varianza cambie entre tramos (ruido estacionario).")
    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    im = ax.imshow(rho, cmap="coolwarm", vmin=-1, vmax=1)
    for (a, b), v in np.ndenumerate(rho):
        ax.text(b, a, f"{v:.2f}", ha="center", va="center", fontsize=7)
    ax.set_xticks(range(len(nombres)), nombres)
    ax.set_yticks(range(len(nombres)), nombres)
    ax.set_title("Correlación entre canales en reposo")
    fig.colorbar(im)
    Rp.guardar_figura(fig, sal, "11_correlacion_canales", sint)
    return df, {"rho_w1_w2": r12, "decision_R": decision, "umbral": UMBRAL_CORRELACION}


# --------------------------------------------------------------------------- g
def pares_repetidos(man):
    """Pares (rep 01, rep 02) del mismo perfil entre ajuste y validación."""
    val = {r.replace("_02.csv", ""): r for r in man.get("validacion", [])}
    return [(r, val[r.replace("_01.csv", "")]) for r in man.get("ajuste", [])
            if r.replace("_01.csv", "") in val]


def repetibilidad(man, sal):
    filas = []
    for a, b in pares_repetidos(man):
        ra, rb = cargar(Rp.ruta_dato(a)), cargar(Rp.ruta_dato(b))
        th_a, _, _ = _theta(IntegracionDirecta(ra.phi_cmd[0], bias_reposo(ra)), ra)
        th_b, _, _ = _theta(IntegracionDirecta(rb.phi_cmd[0], bias_reposo(rb)), rb)
        # Se alinea por TIEMPO (no por número de muestra): si se pierde una muestra
        # en una repetición, el índice se corre pero el tiempo no.
        t = ra.t[ra.t <= rb.t[-1]]
        en_b = lambda x: np.column_stack([np.interp(t, rb.t, x[:, j]) for j in (0, 1)])
        th_b_t = en_b(th_b)
        cmd_b_t = en_b(rb.crudo[["cmd_h", "cmd_c"]].to_numpy(float))
        cmd_a = ra.crudo[["cmd_h", "cmd_c"]].to_numpy(float)[:len(t)]
        igual_cmd = float(np.mean(np.all(np.abs(cmd_a - cmd_b_t) < 0.5, axis=1)))
        for j in (0, 1):
            err = [Me.rmse(r_th[:, j], r.theta_cmd[:, j],
                           Me.ventanas_estacionarias(r.crudo[["cmd_h", "cmd_c"]].to_numpy(), r.t))
                   for r, r_th in ((ra, th_a), (rb, th_b))]
            filas.append({"perfil": ra.nombre.rsplit("_", 1)[0], "eslabon": j + 1,
                          "consigna_coincide_frac": igual_cmd,
                          "rms_diferencia_entre_repeticiones_deg": Me.rmse(th_a[:len(t), j], th_b_t[:, j]),
                          "error_estacionario_rep1_deg": err[0], "error_estacionario_rep2_deg": err[1]})
    df = pd.DataFrame(filas)
    if len(df):
        Rp.guardar_tabla(df, sal, "repetibilidad", "Repetibilidad del ensayo dinámico",
                         "Se comparan las dos repeticiones alineadas por tiempo (la consigna la genera "
                         "el firmware en función del tiempo) con integración directa. consigna_coincide "
                         "< 1 aparece en los bordes de cada cambio por la fluctuación de ±1 muestra.")
    return df


# --------------------------------------------------------------------------- h
def degradacion_movimiento(registros, sal, ventana=11, orden=3):
    """Ruido 'aparente' = giro menos una versión suavizada que SÍ sigue el
    movimiento suave (Savitzky–Golay: ajusta una parábola cúbica local). Si el
    residuo crece al moverse, el ruido no es el de reposo (vibración del servo).
    En los escalones el residuo incluye los arranques bruscos: mirar los senos."""
    filas = []
    for reg in registros:
        _, _, _, reposo = _preparar(reg)
        mov = reg.fase == 1
        if not mov.any() or not reposo.any():
            continue
        for j in (0, 1):
            w = reg.w[:, j]
            resid = w - savgol_filter(w, ventana, orden)
            s_rep = float(np.std(resid[reposo], ddof=1))
            s_mov = float(np.std(resid[mov], ddof=1))
            filas.append({"archivo": reg.nombre, "eslabon": j + 1,
                          "ruido_aparente_reposo_dps": s_rep, "ruido_aparente_movimiento_dps": s_mov,
                          "cociente_mov_reposo": s_mov / s_rep})
    df = pd.DataFrame(filas)
    Rp.guardar_tabla(df, sal, "degradacion_movimiento", "Ruido en reposo vs en movimiento",
                     f"Residuo de alta frecuencia: w − Savitzky–Golay (ventana {ventana}, orden {orden}). "
                     "Un cociente > 1 indica que la R medida en reposo SUBESTIMA el ruido real "
                     "durante el movimiento. El residuo en movimiento incluye vibración del servo, los "
                     "pasos de 1° de la consigna (el servo solo acepta grados enteros) y, en "
                     "'escalones', los arranques bruscos: todo eso es 'ruido' para un modelo de "
                     "velocidad casi constante.")
    return df


# --------------------------------------------------------------------------- i
def _cociente_senos(degr):
    g = degr[degr.archivo.str.contains("seno")] if len(degr) else degr
    g = g if len(g) else degr
    return float(g.cociente_mov_reposo.mean()) if len(g) else float("nan")


def requisitos_kalman(est, R, estructura, sens, rvd, met, degr, sal):
    sig = np.sqrt(np.diag(R)[:2])
    directa = rvd[rvd.metodo == "Integración directa"]
    sin_comp = est.w.mean(axis=0) * 60          # °/min si no se quita el sesgo
    g1 = sens[sens.eslabon == 1].set_index("N")
    objetivo = g1.ruido_omega_reposo_dps.loc[1] / 2
    n_mitad = int(g1[g1.ruido_omega_reposo_dps <= objetivo].index.min()) \
        if (g1.ruido_omega_reposo_dps <= objetivo).any() else None
    ruido_mm5 = float(g1.ruido_omega_reposo_dps.loc[5]) if 5 in g1.index else np.nan
    d = {
        "sigma_giro_dps": sig.tolist(), "R": np.asarray(R).tolist(),
        "estructura_R": estructura,
        "deriva_sin_compensar_deg_min": sin_comp.tolist(),
        "deriva_compensada_deg_min": directa.deriva_deg_por_min.tolist(),
        "media_movil_para_reducir_ruido_a_la_mitad": {
            "N": n_mitad,
            "retraso_ms": float(g1.retraso_ms.loc[n_mitad]) if n_mitad else None},
        "deriva_final_perfil_por_metodo_deg": met.groupby("metodo").deriva_final_perfil_deg
        .apply(lambda x: float(np.mean(np.abs(x)))).to_dict(),
        "cociente_ruido_movimiento_reposo": _cociente_senos(degr),
        "requisitos": {
            "retraso_max_ms": CK.RETRASO_MAX_MS,
            "ruido_omega_max_dps": ruido_mm5,
            "deriva": "no observable con solo giroscopio: acotarla con el sesgo del reposo y "
                      "declararla; corregirla exige referencia absoluta (acelerómetro en plano "
                      "vertical, encoder o cámara)",
        },
    }
    Rp.guardar_json(d, sal, "requisitos_kalman")
    texto = [
        "# Requisitos para el filtro de Kalman (Entrega 2), calculados de la Entrega 1", "",
        f"- Ruido del giroscopio en reposo: σ1 = {sig[0]:.4f} °/s, σ2 = {sig[1]:.4f} °/s → "
        f"R {estructura['decision_R']} (ρ w1–w2 = {estructura['rho_w1_w2']:+.3f}).",
        f"- Deriva SIN compensar el sesgo: {sin_comp[0]:+.1f} y {sin_comp[1]:+.1f} °/min. "
        f"Compensada (fuera de muestra): {directa.deriva_deg_por_min.iloc[0]:+.2f} y "
        f"{directa.deriva_deg_por_min.iloc[1]:+.2f} °/min.",
        (f"- Para bajar el ruido a la mitad, la media móvil necesita N = {n_mitad} → "
         f"retraso ≈ {g1.retraso_ms.loc[n_mitad]:.0f} ms." if n_mitad else
         "- Ninguna ventana del barrido baja el ruido a la mitad."),
        f"- En movimiento suave (perfiles seno) el ruido aparente es {_cociente_senos(degr):.1f}× "
        "el de reposo.",
        "", "## Conclusión",
        "- **Integración directa:** retraso 0, pero todo el ruido pasa y la deriva se acumula.",
        "- **Media móvil:** el ruido baja como 1/√N, pagando (N−1)/2 muestras de retraso; la deriva "
        "final es la MISMA que sin filtrar (ver `variantes_sesgo` y `ruido_vs_deriva`).",
        "- Ninguno resuelve a la vez deriva y retraso.", "", "## Requisitos para la Entrega 2",
        f"1. Retraso de ω ≤ {CK.RETRASO_MAX_MS:.0f} ms.",
        f"2. Ruido de ω en reposo ≤ {ruido_mm5:.4f} °/s (el de media móvil N = 5) o menor.",
        "3. Usar el Δt_k real y la R medida aquí (y considerar que en movimiento el ruido es mayor).",
        "4. Deriva: con solo giroscopio no es observable; se acota y se declara, o se agrega una "
        "referencia absoluta.",
    ]
    (sal / "requisitos_kalman.md").write_text("\n".join(texto) + "\n", encoding="utf-8")
    return d
