"""Pruebas de la cadena de las Entregas 1 y 2 (Kalman, media móvil, datos)."""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import config_imu as C
import config_kalman as CK
from estimadores import IntegracionDirecta, KalmanBrazo, MediaMovilIntegracion
from grabador import parsear_linea_datos
from kalman import FiltroKalman
from metricas import correlacion_cruzada
from tiempo_real import valores_a_fisico


def test_kalman_escalar_converge_al_valor_medido():
    kf = FiltroKalman([0.0], [[100.0]])
    for _ in range(200):
        kf.predecir(np.eye(1), np.eye(1) * 1e-4)
        kf.actualizar(np.array([5.0]), np.eye(1), np.eye(1) * 0.1)
    assert kf.x[0] == pytest.approx(5.0, abs=1e-2)
    asim, min_ev = kf.chequeo_P()
    assert asim < 1e-12 and min_ev > 0


def test_brazo_quieto_sin_ruido_no_se_mueve():
    R = np.diag([0.0036, 0.0036])
    kf = KalmanBrazo([30, 75], [0.5, -0.2], R, q=0.05)
    for _ in range(500):
        phi, omega = kf.paso(0.01, np.array([0.5, -0.2]))   # solo el sesgo
    assert phi == pytest.approx([30, 75], abs=1e-6)
    assert omega == pytest.approx([0, 0], abs=1e-6)


def test_giro_constante_se_integra_igual_en_los_tres_metodos():
    metodos = [IntegracionDirecta([0, 0], [0, 0]), MediaMovilIntegracion([0, 0], [0, 0], 5),
               KalmanBrazo([0, 0], [0, 0], np.diag([0.0036] * 2), q=0.05)]
    for m in metodos:
        for _ in range(1000):                 # 10 s a 20 °/s -> 200°
            phi, _ = m.paso(0.01, np.array([20.0, -10.0]))
        assert phi == pytest.approx([200, -100], abs=1.5), m.nombre


def test_retraso_media_movil_es_n_menos_1_medios():
    fs, N = 100.0, 21
    t = np.arange(0, 20, 1 / fs)
    w = 30 * np.sin(2 * np.pi * 0.5 * t)
    mm = MediaMovilIntegracion([0, 0], [0, 0], N)
    salida = np.array([mm.paso(1 / fs, np.array([x, x]))[1][0] for x in w])
    retraso = correlacion_cruzada(w, salida, fs)[2]
    assert retraso * 1e3 == pytest.approx((N - 1) / 2 * 10, abs=2)


def test_q_desde_frecuencia_de_corte():
    r, dt = 0.0036, 0.01
    for fc in (1.5, 5, 15):
        q = CK.q_desde_f_corte(fc, r, dt)
        p = 1.0                                # Riccati escalar hasta converger
        for _ in range(20000):
            pp = p + q * dt
            k = pp / (pp + r)
            p = (1 - k) * pp
        assert -np.log(1 - k) / (2 * np.pi * dt) == pytest.approx(fc, rel=1e-3)


def test_linea_del_firmware_y_conversion_iguales_al_analisis():
    linea = "D,7,1000,1410,1,0,90,90,10,20,16384,1,2,655,30,40,16300,3,4,-1310"
    v = parsear_linea_datos(linea)
    assert len(v) == len(C.COLUMNAS_CRUDAS)
    _, cmd_h, cmd_c, w, _ = valores_a_fisico(v)
    assert (cmd_h, cmd_c) == (90, 90)
    esperado = [C.EJE_GIRO[1][1] * 655 / 65.5, C.EJE_GIRO[2][1] * -1310 / 65.5]
    assert w == pytest.approx(esperado)
    assert parsear_linea_datos("# cfg algo") is None
    assert parsear_linea_datos("D,1,2,3") is None


# ---------------------------------------------------------------- Entrega 1: verificación y datos
def _captura_sana(carpeta, n=3200, modo="estatico"):
    """Escribe un CSV crudo mínimo y correcto (más su JSON) para las pruebas."""
    import json
    rng = np.random.default_rng(1)
    df = pd.DataFrame({c: rng.integers(-50, 50, n) for c in C.COLUMNAS_CRUDAS})
    df["seq"] = np.arange(n)
    df["t1_us"] = 1_000_000 + np.arange(n) * 10_000
    df["t2_us"] = df["t1_us"] + 410
    df["perfil"], df["fase"] = 0, -1
    ruta = carpeta / "estatico_01.csv"
    df.to_csv(ruta, index=False)
    ruta.with_suffix(".json").write_text(json.dumps({"modo": modo}), encoding="utf-8")
    return ruta, df


def test_validacion_acepta_captura_sana(tmp_path):
    from validar_datos import validar_archivo
    ruta, _ = _captura_sana(tmp_path)
    filas = validar_archivo(ruta)
    assert all(f["resultado"] == "OK" for f in filas), [f for f in filas if f["resultado"] != "OK"]


def test_validacion_detecta_problemas(tmp_path):
    from validar_datos import validar_archivo
    ruta, df = _captura_sana(tmp_path, n=2000)            # 20 s: reposo demasiado corto
    df = df.drop(index=[100, 101]).reset_index(drop=True)  # muestras perdidas
    df["gz1"] = 7                                          # IMU congelada
    df.loc[50, "gx2"] = 32767                              # saturación
    df.to_csv(ruta, index=False)
    malos = {f["chequeo"].split(" ")[0] for f in validar_archivo(ruta) if f["resultado"] != "OK"}
    assert {"reposo", "muestras", "ninguna", "sin"} <= malos


def test_desborde_de_micros_no_es_error(tmp_path):
    from validar_datos import validar_archivo
    ruta, df = _captura_sana(tmp_path)
    df["t1_us"] = (2**32 - 50_000 + np.arange(len(df)) * 10_000) % 2**32
    df["t2_us"] = (df["t1_us"] + 410) % 2**32
    df.to_csv(ruta, index=False)
    f = {x["chequeo"]: x["resultado"] for x in validar_archivo(ruta)}
    assert f["timestamps monótonos (con desborde de micros)"] == "OK"


def test_verificacion_cinematica_encuentra_offset(tmp_path):
    import parametros as P
    import verificacion_cinematica as V
    from cinematica import cinematica_directa
    df = V.crear_plantilla()
    assert set(df.tipo) == {"directa", "inversa"} and (df.groupby("id").size() == 2).all()
    (x, y), _ = cinematica_directa(df.theta1_deg + 1.0, df.theta2_deg - 2.0, P.L1_MM, P.L2_MM)
    df["x_med_mm"], df["y_med_mm"] = x, y
    ruta = tmp_path / "v.csv"
    df.to_csv(ruta, index=False)
    r = V.analizar(ruta, tmp_path, sintetico=True)
    f = r["fuentes"]
    assert f["offset_estimado_theta1_deg"] == pytest.approx(1.0, abs=1e-3)
    assert f["offset_estimado_theta2_deg"] == pytest.approx(-2.0, abs=1e-3)
    assert f["rmse_corrigiendo_offsets_mm"] < 1e-3
    assert f["repetibilidad_media_mm"] == pytest.approx(0.0, abs=1e-9)


def test_coherencia_detecta_servo_que_no_obedece(tmp_path):
    """Si un eslabón no se mueve aunque la consigna sí, la captura se rechaza."""
    import json
    import shutil

    from validar_datos import captura_valida
    origen = Path(__file__).resolve().parent.parent / "datos" / "sinteticos"
    for ext in (".csv", ".json"):
        shutil.copy(origen / f"escalones_01{ext}", tmp_path / f"escalones_01{ext}")
    ruta = tmp_path / "escalones_01.csv"
    assert captura_valida(ruta, "perfil")

    d = pd.read_csv(ruta)
    d["gz1"] = d["gz1"].iloc[:50].mean().round().astype(int)   # el hombro "no se mueve"
    d["gz2"] = d["gz2"].iloc[:50].mean().round().astype(int)
    d.to_csv(ruta, index=False)
    assert not captura_valida(ruta, "perfil")


def test_generar_informe_crea_el_docx(tmp_path):
    """El informe de la Entrega 2 se genera leyendo los resultados (sin copiar números a mano)."""
    pytest.importorskip("docx")
    import generar_informe as GI
    if GI.leer_json(GI.E2 / "seleccion_Q.json") is None:
        pytest.skip("faltan los resultados reales de la Entrega 2")
    ruta, n_fig, n_tab, _ = GI.generar(tmp_path / "informe.docx")
    assert ruta.exists() and ruta.stat().st_size > 10_000
    assert n_tab >= 5 and n_fig >= 5


def test_generar_informe_ieee(tmp_path):
    """Informe IEEE: dos columnas, ecuaciones de Word (OMML), TABLA I... y Fig. 1..."""
    pytest.importorskip("docx")
    import generar_informe as GI
    import generar_informe_ieee as IE
    if GI.leer_json(GI.E2 / "seleccion_Q.json") is None:
        pytest.skip("faltan los resultados reales de la Entrega 2")
    ruta, inf = IE.generar(tmp_path / "ieee.docx", autores=["A (1)"], afiliacion="U")
    assert ruta.exists() and inf.n_eq >= 10 and inf.n_tab >= 5 and inf.n_fig >= 5
    xml = inf.doc.element.xml
    assert 'w:num="2"' in xml and "m:oMath" in xml
    assert IE.romano(14) == "XIV" and IE.cientifico(1.2e6) == "1,2×10⁶"
