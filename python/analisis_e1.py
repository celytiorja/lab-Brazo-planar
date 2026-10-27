"""ENTREGA 1 — Caracterización de las IMU (puntos 2 a 5 de la guía).

    python python/analisis_e1.py                                    (datos reales)
    python python/analisis_e1.py --manifiesto datos/sinteticos/manifiesto.json

Salidas en resultados/<origen>/e1/ (todo generado por código, nada a mano):
  estadisticas_estatico.csv/.md   media, varianza y σ de cada canal (punto 3)
  matriz_R.csv / R.json           covarianza del ruido de medición -> se usa en Kalman (punto 3)
  temporizacion.csv/.md           muestreo real, Δt, jitter, pérdidas, desfase IMU1-IMU2 (punto 3)
  correlacion_cruzada.csv/.md     retrasos con relación física esperada (punto 3)
  metricas_e1.csv/.md             tabla comparativa Euler / media móvil (puntos 4 y 5)
  *.png                           gráficas (punto 5)
"""
import argparse

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import config_kalman as CK
import metricas as Me
import reporte as Rp
from datos_imu import bias_reposo, cargar, theta_de_phi
from estimadores import IntegracionDirecta, MediaMovilIntegracion, ejecutar

COLORES = {"Integración directa": "tab:gray", "consigna": "k"}


def estadisticas_estatico(reg):
    filas = []
    for i in (1, 2):
        for j, eje in enumerate("xyz"):
            for nombre, datos, unidad in ((f"a{eje}{i}", reg.acc[i][:, j], "g"),
                                          (f"g{eje}{i}", reg.gyro[i][:, j], "°/s")):
                filas.append({"canal": nombre, "unidad": unidad, "media": datos.mean(),
                              "varianza": datos.var(ddof=1), "desv_est": datos.std(ddof=1),
                              "min": datos.min(), "max": datos.max()})
    for i in (1, 2):
        d = reg.w[:, i - 1]
        filas.append({"canal": f"w{i} (giro en el plano)", "unidad": "°/s", "media": d.mean(),
                      "varianza": d.var(ddof=1), "desv_est": d.std(ddof=1),
                      "min": d.min(), "max": d.max()})
        if reg.phi_acc is not None:
            d = reg.phi_acc[:, i - 1]
            filas.append({"canal": f"phi_acc{i} (inclinación)", "unidad": "°", "media": d.mean(),
                          "varianza": d.var(ddof=1), "desv_est": d.std(ddof=1),
                          "min": d.min(), "max": d.max()})
    return pd.DataFrame(filas)


def matriz_R(reg):
    """R = covarianza del vector de mediciones que usará Kalman, en reposo."""
    etiquetas = ["w1 [°/s]", "w2 [°/s]"]
    z = [reg.w[:, 0], reg.w[:, 1]]
    if reg.phi_acc is not None:
        etiquetas += ["phi_acc1 [°]", "phi_acc2 [°]"]
        z += [reg.phi_acc[:, 0], reg.phi_acc[:, 1]]
    Z = np.column_stack(z)
    R = np.cov(Z.T, ddof=1)
    return R, etiquetas, Z.mean(axis=0)


def temporizacion(reg):
    dt_ms = reg.dt[1:] * 1e3
    fila = {"archivo": reg.nombre, "muestras": reg.n, "duracion_s": reg.t[-1],
            "fs_real_hz": 1 / reg.dt[1:].mean(), "dt_medio_ms": dt_ms.mean(),
            "dt_desv_us": dt_ms.std() * 1e3, "dt_min_ms": dt_ms.min(), "dt_max_ms": dt_ms.max(),
            "perdidas": reg.perdidas,
            "desfase_imu2_imu1_us": float(np.mean(reg.t2_menos_t1_us))}
    if "t_pc_s" in reg.crudo:
        llegada = reg.crudo["t_pc_s"].to_numpy() - reg.t
        fila["llegada_pc_jitter_ms"] = float(np.std(llegada) * 1e3)
    return fila


def tramo_solo_hombro(reg):
    """Desde el inicio hasta poco antes del primer cambio del codo: ahí el codo
    está fijo y la física dice que IMU2 gira IGUAL que IMU1 (ω2 = ω1)."""
    cambios = np.flatnonzero(np.diff(reg.crudo["cmd_c"].to_numpy()) != 0)
    fin = cambios[0] - 30 if len(cambios) else reg.n
    m = np.zeros(reg.n, bool)
    m[:max(fin, 0)] = True
    return m


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifiesto", default=None)
    args = ap.parse_args()
    man = Rp.cargar_manifiesto(args.manifiesto)
    sal = Rp.carpeta_resultados(man, "e1")

    est = cargar(Rp.ruta_dato(man["estatico"]))
    din = cargar(Rp.ruta_dato(man["dinamico_e1"]))
    sint = est.sintetico or din.sintetico
    fs = 1 / est.dt[1:].mean()
    print(f"Estático: {est.nombre} ({est.n} muestras)  Dinámico: {din.nombre} ({din.n} muestras)")

    # ------------------------------------------------------------------ 3a. Estadística
    tabla = estadisticas_estatico(est)
    Rp.guardar_tabla(tabla, sal, "estadisticas_estatico", "Estadística en reposo",
                     f"Archivo: {est.nombre}. {Rp.encabezado(man)}")

    R, etiquetas, medias = matriz_R(est)
    pd.DataFrame(R, columns=etiquetas, index=etiquetas).to_csv(sal / "matriz_R.csv")
    Rp.guardar_json({"R": R.tolist(), "etiquetas": etiquetas, "medias": medias.tolist(),
                     "archivo": est.nombre, "muestras": est.n, "fs_hz": fs,
                     "commit": Rp.commit_actual()}, sal, "R")

    fig, ax = plt.subplots(figsize=(5, 4))
    im = ax.imshow(R, cmap="viridis")
    for (a, b), v in np.ndenumerate(R):
        ax.text(b, a, f"{v:.2e}", ha="center", va="center", color="w", fontsize=8)
    ax.set_xticks(range(len(etiquetas)), etiquetas, rotation=30)
    ax.set_yticks(range(len(etiquetas)), etiquetas)
    ax.set_title("Matriz R (covarianza del ruido de medición)")
    fig.colorbar(im)
    Rp.guardar_figura(fig, sal, "03_matriz_R", sint)

    # Señales en reposo e histogramas
    fig, axs = plt.subplots(2, 2, figsize=(11, 6), sharex="col")
    for i in (1, 2):
        axs[i - 1, 0].plot(est.t, est.w[:, i - 1], lw=0.5)
        axs[i - 1, 0].axhline(medias[i - 1], color="r", label=f"media = {medias[i-1]:.3f} °/s")
        axs[i - 1, 0].set_ylabel(f"w{i} [°/s]")
        axs[i - 1, 0].legend(loc="upper right")
        x = est.w[:, i - 1]
        axs[i - 1, 1].hist(x, bins=60, density=True, alpha=0.7)
        s = x.std(ddof=1)
        g = np.linspace(x.min(), x.max(), 200)
        axs[i - 1, 1].plot(g, np.exp(-(g - x.mean())**2 / (2 * s**2)) / (s * np.sqrt(2 * np.pi)),
                           "r", label=f"Gauss σ = {s:.3f} °/s")
        axs[i - 1, 1].legend()
    axs[1, 0].set_xlabel("t [s]")
    axs[1, 1].set_xlabel("w [°/s]")
    fig.suptitle(f"Giroscopio en reposo ({est.nombre}): ruido alrededor de un sesgo ≠ 0")
    Rp.guardar_figura(fig, sal, "01_reposo_senales_histogramas", sint)

    # ------------------------------------------------------------------ 3b. Temporización
    t_filas = [temporizacion(est), temporizacion(din)]
    Rp.guardar_tabla(pd.DataFrame(t_filas), sal, "temporizacion", "Muestreo y alineación temporal",
                     "Δt sale de los timestamps del ESP32 (micros()). desfase_imu2_imu1: la IMU2 "
                     "se lee justo después de la IMU1 en cada muestra.")
    fig, ax = plt.subplots(figsize=(7, 3.5))
    ax.hist(din.dt[1:] * 1e3, bins=80)
    ax.set_xlabel("Δt [ms]")
    ax.set_ylabel("muestras")
    ax.set_yscale("log")
    ax.set_title(f"Intervalo real de muestreo ({din.nombre}); nominal 10 ms")
    Rp.guardar_figura(fig, sal, "04_histograma_dt", sint)

    # ------------------------------------------------------------------ 4a. Deriva en reposo
    # Sesgo estimado con los primeros 10 s y probado en el RESTO (fuera de muestra):
    # así no se "hace trampa" restando la media del mismo tramo que se evalúa.
    corte = est.t <= 10.0
    b_ent = est.w[corte].mean(axis=0)
    prueba = ~corte
    t_p = est.t[prueba] - est.t[prueba][0]
    dt_p = est.dt[prueba]
    sin_bias = np.cumsum(dt_p[:, None] * est.w[prueba], axis=0)
    con_bias = np.cumsum(dt_p[:, None] * (est.w[prueba] - b_ent), axis=0)
    fig, axs = plt.subplots(1, 2, figsize=(11, 3.8), sharey=False)
    for i in (0, 1):
        axs[i].plot(t_p, sin_bias[:, i], label="sin quitar sesgo")
        axs[i].plot(t_p, con_bias[:, i], label="quitando sesgo (de los primeros 10 s)")
        axs[i].set_title(f"Eslabón {i+1}: ángulo integrado con el brazo QUIETO")
        axs[i].set_xlabel("t [s]")
        axs[i].set_ylabel("φ [°] (debería ser 0)")
        axs[i].legend()
    Rp.guardar_figura(fig, sal, "05_deriva_en_reposo", sint)
    deriva_reposo = {"sin_sesgo": sin_bias[-1], "con_sesgo": con_bias[-1], "duracion_s": t_p[-1]}

    # ------------------------------------------------------------------ 4b. Euler + media móvil
    b = bias_reposo(din)
    phi0 = din.phi_cmd[0]          # misma condición inicial para todos los métodos
    metodos = [IntegracionDirecta(phi0, b)] + [MediaMovilIntegracion(phi0, b, N)
                                               for N in CK.VENTANAS_MEDIA_MOVIL]
    res = {}
    for m in metodos:
        phi, omega, _ = ejecutar(m, din)
        res[m.nombre] = {"theta": theta_de_phi(phi), "omega": omega}
    theta_cmd = din.theta_cmd
    directa = res["Integración directa"]["theta"]

    # También en el archivo estático: ruido de ω filtrado y deriva a 30 s.
    est_res = {}
    for m in [IntegracionDirecta([0, 0], b_ent)] + [MediaMovilIntegracion([0, 0], b_ent, N)
                                                    for N in CK.VENTANAS_MEDIA_MOVIL]:
        phi, omega, _ = ejecutar(m, est)
        est_res[m.nombre] = (phi, omega)

    fig, axs = plt.subplots(2, 1, figsize=(12, 7), sharex=True)
    for j, nombre_art in enumerate(("θ1 hombro", "θ2 codo")):
        axs[j].plot(din.t, theta_cmd[:, j], "k--", lw=1, label="consigna (no es medición)")
        for nombre, r in res.items():
            axs[j].plot(din.t, r["theta"][:, j], lw=1, label=nombre)
        axs[j].set_ylabel(f"{nombre_art} [°]")
        axs[j].legend(loc="upper right", fontsize=8)
    axs[1].set_xlabel("t [s]")
    fig.suptitle(f"Integración de Euler con y sin media móvil ({din.nombre}), mismas condiciones iniciales")
    Rp.guardar_figura(fig, sal, "07_dinamico_comparacion", sint)

    # Zoom a un escalón para ver el retraso
    cambios = np.flatnonzero(np.any(np.diff(din.crudo[["cmd_h", "cmd_c"]].to_numpy(), axis=0) != 0, axis=1))
    if len(cambios):
        k0 = cambios[min(1, len(cambios) - 1)]
        z = slice(max(k0 - 30, 0), min(k0 + 80, din.n))
        fig, ax = plt.subplots(figsize=(9, 4))
        j = 0 if din.crudo["cmd_h"].iloc[k0 + 1] != din.crudo["cmd_h"].iloc[k0] else 1
        ax.plot(din.t[z], theta_cmd[z, j], "k--", label="consigna")
        for nombre, r in res.items():
            ax.plot(din.t[z], r["theta"][z, j], ".-", ms=3, label=nombre)
        ax.set_xlabel("t [s]")
        ax.set_ylabel(f"θ{j+1} [°]")
        ax.set_title("Zoom a un cambio de consigna: la media móvil llega más tarde")
        ax.legend(fontsize=8)
        Rp.guardar_figura(fig, sal, "08_zoom_retraso", sint)

    # ------------------------------------------------------------------ 3c. Correlación cruzada
    fs_d = 1 / din.dt[1:].mean()
    mov = din.fase == 1 if (din.fase == 1).any() else np.ones(din.n, bool)
    filas_xc, curvas = [], []
    for j in (0, 1):
        lags, c, retraso, pico = Me.correlacion_cruzada(theta_cmd[mov, j], directa[mov, j], fs_d)
        filas_xc.append({"par": f"consigna θ{j+1} → θ{j+1} medido (integración)",
                         "relacion_fisica": "el eslabón sigue a la consigna del servo",
                         "retraso_ms": retraso * 1e3, "coef_pico": pico})
        curvas.append((f"consigna θ{j+1} vs θ{j+1}", lags, c, retraso))
    m_h = tramo_solo_hombro(din)
    if m_h.sum() > 100 and din.w[m_h, 0].std() > 1.0:
        lags, c, retraso, pico = Me.correlacion_cruzada(din.w[m_h, 0], din.w[m_h, 1], fs_d, 0.1)
        filas_xc.append({"par": "w1 (IMU1) → w2 (IMU2), codo fijo",
                         "relacion_fisica": "con el codo quieto ω2 = ω1",
                         "retraso_ms": retraso * 1e3, "coef_pico": pico})
        curvas.append(("w1 vs w2 (codo fijo)", lags, c, retraso))
    Rp.guardar_tabla(pd.DataFrame(filas_xc), sal, "correlacion_cruzada", "Correlación cruzada",
                     "Retraso positivo = la segunda señal llega después. Pico refinado con parábola "
                     "(resolución menor a 1 muestra = 10 ms).")
    fig, axs = plt.subplots(1, len(curvas), figsize=(4.2 * len(curvas), 3.5))
    for ax, (tit, lags, c, retraso) in zip(np.atleast_1d(axs), curvas):
        ax.plot(lags * 1e3, c)
        ax.axvline(retraso * 1e3, color="r", ls="--", label=f"{retraso*1e3:.1f} ms")
        ax.set_title(tit, fontsize=9)
        ax.set_xlabel("retraso [ms]")
        ax.legend()
    Rp.guardar_figura(fig, sal, "06_correlacion_cruzada", sint)

    # ------------------------------------------------------------------ 5. Tabla de métricas
    reposo = din.fase == 0
    estac = Me.ventanas_estacionarias(din.crudo[["cmd_h", "cmd_c"]].to_numpy(), din.t)
    deriva = {n: Me.deriva_final(theta_de_phi(np.column_stack([r["theta"][:, 0],
              r["theta"][:, 0] + r["theta"][:, 1]])), din.fase) for n, r in res.items()}
    filas = []
    for nombre, r in res.items():
        phi_e, om_e = est_res[nombre]
        for j in (0, 1):
            retraso = 0.0 if nombre == "Integración directa" else \
                Me.correlacion_cruzada(directa[mov, j], r["theta"][mov, j], fs_d)[2] * 1e3
            filas.append({
                "metodo": nombre, "articulacion": f"θ{j+1}",
                "ruido_omega_reposo_dps": Me.ruido(om_e[:, j], sin_tendencia=False),
                "deriva_reposo_30s_deg": phi_e[est.t <= 30.0][-1, j],
                "retraso_vs_directa_ms": retraso,
                "error_estacionario_rms_deg": Me.rmse(r["theta"][:, j], theta_cmd[:, j], estac),
                "deriva_final_perfil_deg": deriva[nombre][j],
                "ruido_angulo_reposo_deg": Me.ruido(r["theta"][:, j], reposo),
            })
    nota = ("ruido_omega_reposo: σ de la velocidad estimada con el brazo quieto (archivo estático). "
            "deriva_reposo_30s: ángulo acumulado tras 30 s quieto (debería ser 0). "
            "retraso_vs_directa: correlación cruzada contra la integración directa (que no filtra). "
            "error_estacionario: contra la consigna SOLO donde lleva ≥0.5 s constante (servo ya llegó). "
            "deriva_final_perfil: el perfil vuelve a la pose inicial; lo que no vuelva es deriva.\n\n"
            + Rp.encabezado(man))
    Rp.guardar_tabla(pd.DataFrame(filas), sal, "metricas_e1", "Métricas Entrega 1", nota)
    Rp.guardar_json({"deriva_reposo_fuera_de_muestra": deriva_reposo,
                     "bias_dinamico_dps": b.tolist()}, sal, "resumen_e1")
    print(f"Listo. Resultados en {sal}")


if __name__ == "__main__":
    main()
