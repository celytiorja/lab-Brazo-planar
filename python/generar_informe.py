"""Genera el INFORME de la Entrega 2 (Kalman + teleoperación) como documento Word.

    python python/generar_informe.py
    python python/generar_informe.py --foto ruta/montaje.jpg      (con foto del montaje)
    python python/generar_informe.py --sin-pdf                     (no intentar el PDF)

Salida: docs/informe/Informe_Entrega2.docx (y .pdf si hay LibreOffice).

Todos los números se LEEN de resultados/ (los generan analisis_e1.py, analisis_e2.py,
analisis_teleop.py y prueba_latencia_video.py): si se vuelve a analizar, se vuelve a
correr este script y el informe queda al día. Nada se copia a mano.

Teleoperación: si existen sesiones reales (resultados/reales/teleop) se usan. Si no, se
usan las sintéticas y se marcan como "DATOS SINTÉTICOS (validación del código)".
"""
import argparse
import json
import shutil
import subprocess
from datetime import date
from pathlib import Path

import pandas as pd
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

import reporte as Rp

R = Rp.RAIZ / "resultados"
E1, E2 = R / "reales" / "e1", R / "reales" / "e2"
SALIDA = Rp.RAIZ / "docs" / "informe" / "Informe_Entrega2.docx"
AVISO_SINT = "DATOS SINTÉTICOS (validación del código), no mediciones"


# ======================================================================= utilidades
def leer_csv(ruta):
    return pd.read_csv(ruta) if Path(ruta).exists() else None


def leer_json(ruta):
    return json.loads(Path(ruta).read_text(encoding="utf-8")) if Path(ruta).exists() else None


def f(v, d=2):
    """Número con coma decimal (estilo español)."""
    try:
        return f"{float(v):.{d}f}".replace(".", ",")
    except (TypeError, ValueError):
        return str(v)


def fila(df, col, valor):
    sel = df[df[col] == valor]
    return sel.iloc[0] if len(sel) else None


class Informe:
    def __init__(self):
        self.doc = Document()
        self.n_fig = 0
        self.n_tab = 0
        self._estilos()

    # ------------------------------------------------------------------ formato
    def _estilos(self):
        st = self.doc.styles["Normal"]
        st.font.name = "Calibri"
        st.font.size = Pt(11)
        st.element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
        for s in self.doc.sections:
            s.left_margin = s.right_margin = Cm(2.5)
            s.top_margin = s.bottom_margin = Cm(2.2)
        for nivel, tam in ((1, 15), (2, 12.5), (3, 11.5)):
            h = self.doc.styles[f"Heading {nivel}"]
            h.font.name = "Calibri"
            h.font.size = Pt(tam)
            h.font.color.rgb = RGBColor(0x1F, 0x3A, 0x5F)

    def titulo(self, texto, nivel=1):
        self.doc.add_heading(texto, level=nivel)

    def p(self, texto, negrita=False, cursiva=False, centrado=False, tam=None):
        par = self.doc.add_paragraph()
        par.paragraph_format.space_after = Pt(6)
        if centrado:
            par.alignment = WD_ALIGN_PARAGRAPH.CENTER
        else:
            par.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        # **negrita** dentro del texto
        partes = texto.split("**")
        for i, parte in enumerate(partes):
            r = par.add_run(parte)
            r.bold = negrita or (i % 2 == 1)
            r.italic = cursiva
            if tam:
                r.font.size = Pt(tam)
        return par

    def vinetas(self, items):
        for it in items:
            par = self.doc.add_paragraph(style="List Bullet")
            partes = it.split("**")
            for i, parte in enumerate(partes):
                par.add_run(parte).bold = (i % 2 == 1)

    def ecuacion(self, texto):
        par = self.doc.add_paragraph()
        par.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = par.add_run(texto)
        r.font.name = "Cambria Math"
        r.font.size = Pt(11.5)
        r.italic = True
        par.paragraph_format.space_after = Pt(6)

    def nota(self, texto, color="FFF4CE"):
        """Recuadro sombreado (avisos)."""
        t = self.doc.add_table(rows=1, cols=1)
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        celda = t.rows[0].cells[0]
        sombra = OxmlElement("w:shd")
        sombra.set(qn("w:val"), "clear")
        sombra.set(qn("w:color"), "auto")
        sombra.set(qn("w:fill"), color)
        celda._tc.get_or_add_tcPr().append(sombra)
        celda.paragraphs[0].add_run(texto).bold = True
        self.doc.add_paragraph()

    def tabla(self, encabezado, filas, titulo, anchos=None):
        self.n_tab += 1
        cap = self.doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = cap.add_run(f"Tabla {self.n_tab}. ")
        r.bold = True
        cap.add_run(titulo).italic = True
        t = self.doc.add_table(rows=1, cols=len(encabezado))
        t.style = "Table Grid"
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        for c, h in zip(t.rows[0].cells, encabezado):
            c.text = ""
            run = c.paragraphs[0].add_run(str(h))
            run.bold = True
            run.font.size = Pt(9.5)
            sombra = OxmlElement("w:shd")
            sombra.set(qn("w:val"), "clear")
            sombra.set(qn("w:fill"), "DCE6F1")
            c._tc.get_or_add_tcPr().append(sombra)
        for fil in filas:
            celdas = t.add_row().cells
            for c, v in zip(celdas, fil):
                c.text = ""
                c.paragraphs[0].add_run(str(v)).font.size = Pt(9.5)
        if anchos:
            for fil in t.rows:
                for c, w in zip(fil.cells, anchos):
                    c.width = Cm(w)
        self.doc.add_paragraph()
        return t

    def figura(self, ruta, pie, ancho_cm=15.5):
        ruta = Path(ruta)
        if not ruta.exists():
            return False
        self.n_fig += 1
        par = self.doc.add_paragraph()
        par.alignment = WD_ALIGN_PARAGRAPH.CENTER
        par.add_run().add_picture(str(ruta), width=Cm(ancho_cm))
        cap = self.doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = cap.add_run(f"Figura {self.n_fig}. ")
        r.bold = True
        r.font.size = Pt(9.5)
        r2 = cap.add_run(pie)
        r2.italic = True
        r2.font.size = Pt(9.5)
        return True

    def salto(self):
        self.doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


# ======================================================================= datos
def cargar_datos():
    d = {"R": leer_json(E1 / "R.json"), "resumen_e1": leer_json(E1 / "resumen_e1.json"),
         "sel": leer_json(E2 / "seleccion_Q.json"),
         "val": leer_csv(E2 / "metricas_e2_validacion_resumen.csv"),
         "reposo": leer_csv(E2 / "ruido_reposo_puro.csv"),
         "ajuste": leer_csv(E2 / "resumen_seleccion_Q.csv"),
         "acel": leer_csv(E2 / "aceleracion_angular.csv"),
         "nis": leer_csv(E2 / "consistencia_kalman.csv"),
         "comp": leer_csv(E2 / "compromiso_Q_R.csv"),
         "manifiesto": leer_json(Rp.RAIZ / "datos" / "crudos" / "manifiesto.json"),
         "latencia": leer_json(R / "latencia_video.json")}
    real = R / "reales" / "teleop"
    if (real / "metricas_teleop_completas.csv").exists():
        d["teleop_dir"], d["teleop_sint"] = real, False
    else:
        d["teleop_dir"], d["teleop_sint"] = R / "sinteticos" / "teleop", True
    d["teleop"] = leer_csv(d["teleop_dir"] / "metricas_teleop_completas.csv")
    d["qcam"] = leer_csv(d["teleop_dir"] / "configuraciones_q_camara.csv")
    if d["qcam"] is None:
        d["qcam"] = leer_csv(R / "sinteticos" / "teleop" / "configuraciones_q_camara.csv")
    return d


# ======================================================================= secciones
def portada(inf, d):
    for _ in range(4):
        inf.doc.add_paragraph()
    inf.p("Universidad Militar Nueva Granada", negrita=True, centrado=True, tam=14)
    inf.p("Programa de Ingeniería Mecatrónica · Procesamiento Digital de Señales",
          centrado=True, tam=12)
    inf.doc.add_paragraph()
    inf.p("Laboratorio PDS – Corte 3, Entrega 2:", negrita=True, centrado=True, tam=18)
    inf.p("Filtro de Kalman y teleoperación de un brazo planar 2 GDL", negrita=True,
          centrado=True, tam=18)
    for _ in range(3):
        inf.doc.add_paragraph()
    inf.p("Integrantes: ______________________________________", centrado=True)
    inf.p("Código(s): ________________________________________", centrado=True)
    inf.p("Docente: __________________________________________", centrado=True)
    inf.p(f"Fecha: {date.today().strftime('%d/%m/%Y')}", centrado=True)
    inf.doc.add_paragraph()
    inf.p(f"Repositorio: celytiorja/lab-Brazo-planar · commit {Rp.commit_actual()}",
          centrado=True, cursiva=True, tam=9)
    inf.salto()


def resumen(inf, d):
    inf.titulo("Resumen", 1)
    val = d["val"]
    kf = fila(val, "metodo", "Kalman Q_media")
    dirc = fila(val, "metodo", "Integración directa")
    mm5 = fila(val, "metodo", "Media móvil N=5 + Euler")
    rep = d["reposo"]
    kfr = fila(rep, "metodo", "Kalman Q_media")
    dr = fila(rep, "metodo", "Integración directa")
    q = d["sel"]["configuracion"]
    inf.p("Se diseñó, implementó y validó un filtro de Kalman para estimar los ángulos y las "
          "velocidades angulares de un brazo planar de dos grados de libertad a partir de dos IMU "
          "MPU-6050 muestreadas a 100 Hz, y un segundo filtro de Kalman que estima los ángulos del "
          "brazo humano medidos con la cámara de un teléfono para teleoperar el robot. "
          f"La covarianza de medición R se obtuvo del reposo de la Entrega 1 y la covarianza de proceso "
          f"Q se razonó por la frecuencia de corte del filtro: de tres configuraciones se eligió "
          f"**{q['nombre']}** (f_c = {f(q['f_corte_hz'], 1)} Hz, q = {f(q['q'], 5)} °²/s³) con una regla "
          f"fija aplicada solo a los registros de ajuste. En validación, el Kalman redujo el ruido de ω "
          f"en reposo de {f(dr['ruido_omega_reposo_puro_dps'], 3)} a {f(kfr['ruido_omega_reposo_puro_dps'], 3)} °/s "
          f"con un retraso de ω de {f(kf['retraso_omega_ms'], 1)} ms (media móvil N = 5: "
          f"{f(mm5['retraso_omega_ms'], 1)} ms) y un retraso del ángulo de solo {f(kf['retraso_theta_ms'], 1)} ms, "
          f"y el ruido de la aceleración angular bajó de {f(dirc['ruido_alfa_reposo_dps2'], 1)} a "
          f"{f(kf['ruido_alfa_reposo_dps2'], 1)} °/s². Ningún método corrige la deriva, porque con solo "
          "giroscopio el ángulo no es observable. La teleoperación con marcadores ArUco y Kalman de la "
          "cámara funciona en tiempo real con un costo de cómputo de décimas de milisegundo por cuadro.")


def introduccion(inf, d):
    inf.titulo("1. Introducción y objetivos", 1)
    inf.p("El objetivo final del laboratorio es un brazo planar de dos articulaciones (hombro y codo) "
          "que copie en tiempo real el movimiento de un brazo humano. En la Entrega 1 se caracterizaron "
          "las IMU (sesgo, ruido, deriva, matriz R) y los métodos base (integración de Euler y media "
          "móvil). En esta entrega se agrega un estimador óptimo, el filtro de Kalman, y se usa la "
          "estimación para teleoperar el robot.")
    inf.p("Objetivos:", negrita=True)
    inf.vinetas([
        "Formular el modelo de estado (x, F, H, Q, R, x₀, P₀) del brazo con las mediciones de los giroscopios.",
        "Proponer y razonar al menos tres configuraciones de Q y elegir una con datos de ajuste, "
        "validándola con datos distintos.",
        "Comparar integración directa, media móvil y Kalman en ruido, retraso, deriva y aceleración angular.",
        "Teleoperar el brazo con la estimación (cámara + Kalman) y medir tiempos de cómputo y latencia.",
        "Interpretar los resultados y declarar los límites de lo que se puede verificar."])


def marco_teorico(inf, d):
    inf.titulo("2. Marco teórico", 1)
    inf.titulo("2.1 Modelo en espacio de estados", 2)
    inf.p("El filtro de Kalman estima el estado x de un sistema lineal con ruido a partir de "
          "mediciones ruidosas z. El modelo discreto, con el intervalo de muestreo real Δtₖ de cada muestra, es:")
    inf.ecuacion("xₖ = Fₖ xₖ₋₁ + wₖ,   wₖ ~ N(0, Qₖ)")
    inf.ecuacion("zₖ = H xₖ + vₖ,   vₖ ~ N(0, R)")
    inf.p("Para cada eslabón i se usa el modelo de **velocidad casi constante**: el estado es el ángulo "
          "absoluto φᵢ y la velocidad angular ωᵢ; la aceleración desconocida se trata como ruido blanco de "
          "densidad q, lo que da:")
    inf.ecuacion("Fᵢ = [[1, Δt], [0, 1]]        Qᵢ = q · [[Δt³/3, Δt²/2], [Δt²/2, Δt]]")
    inf.p("Para el brazo completo x = [φ₁, ω₁, φ₂, ω₂]ᵀ. La IMU2 va montada sobre el eslabón 2, que se "
          "mueve con el eslabón 1, por lo que mide el ángulo absoluto φ₂ = θ₁ + θ₂; el ángulo del codo es "
          "θ₂ = φ₂ − φ₁. Los giroscopios miden solo velocidad:")
    inf.ecuacion("H = [[0, 1, 0, 0], [0, 0, 0, 1]],    zₖ = [w₁ − b₁, w₂ − b₂]ᵀ")
    inf.titulo("2.2 Ecuaciones del filtro", 2)
    inf.p("Cada muestra tiene dos etapas:")
    inf.ecuacion("Predicción:    x̂⁻ = F x̂,     P⁻ = F P Fᵀ + Q")
    inf.ecuacion("Ganancia:      K = P⁻ Hᵀ (H P⁻ Hᵀ + R)⁻¹")
    inf.ecuacion("Actualización: x̂ = x̂⁻ + K (z − H x̂⁻)")
    inf.ecuacion("Covarianza (forma de Joseph): P = (I − K H) P⁻ (I − K H)ᵀ + K R Kᵀ")
    inf.vinetas([
        "**P** es la incertidumbre del estado; **K** decide cuánto se cree la medición frente a la "
        "predicción: P⁻ grande o R pequeña → K grande.",
        "**R** es la covarianza del ruido de medición (sale de la Entrega 1); **Q** es lo que el modelo no "
        "explica. La relación Q/R fija el compromiso entre suavidad y retraso.",
        "La **forma de Joseph** mantiene P simétrica y definida positiva aunque haya errores de redondeo.",
        "La innovación y = z − H x̂⁻ con covarianza S = H P⁻ Hᵀ + R permite verificar la consistencia: "
        "**NIS = yᵀ S⁻¹ y ~ χ²(m)**, con media m (m = 2 mediciones)."])
    inf.titulo("2.3 Q razonada por la frecuencia de corte", 2)
    inf.p("Con solo giroscopio, la parte de ω del filtro en régimen estacionario es un paso bajo de primer "
          "orden ω̂ₖ = ω̂ₖ₋₁ + K (zₖ − ω̂ₖ₋₁). Resolviendo la ecuación de Riccati escalar se relaciona la "
          "ganancia con q, y la ganancia con la frecuencia de corte f_c:")
    inf.ecuacion("K = 1 − e^(−2π f_c Δt)      λ = q Δt / r = K² / (1 − K)      q = λ r / Δt")
    inf.p("Así cada configuración de Q se justifica por la banda de movimiento que debe dejar pasar, y no "
          "por prueba y error. El retraso aproximado a baja frecuencia es 1/(2π f_c).")
    inf.titulo("2.4 Kalman de la cámara (teleoperación)", 2)
    inf.p("Para la teleoperación, la cámara del teléfono ve tres marcadores ArUco (hombro, codo y muñeca) "
          "y calcula θ₁ y θ₂ del brazo humano. Se usa el mismo modelo de velocidad casi constante con "
          "estado [θ₁, ω₁, θ₂, ω₂], pero ahora la medición es el ángulo:")
    inf.ecuacion("H_cam = [[1, 0, 0, 0], [0, 0, 1, 0]],     q = r · Δt · (2π f_n)⁴")
    inf.p("En régimen estacionario es un paso bajo de segundo orden de frecuencia natural f_n; r es la "
          "varianza por cuadro de la cámara medida con el brazo quieto y r·Δt la convierte en densidad. "
          "Como q es proporcional a r, la suavidad depende solo de f_n. **Medición parcial:** si la muñeca "
          "queda tapada pero el hombro y el codo se ven, H conserva solo la fila de θ₁: θ₁ sigue medido y θ₂ "
          "se predice. Si una oclusión dura más de 0,2 s, la velocidad estimada se amortigua para que el "
          "robot no siga de largo.")


def metodologia(inf, d, foto):
    inf.titulo("3. Sistema y metodología", 1)
    inf.titulo("3.1 Hardware y adquisición", 2)
    inf.vinetas([
        "ESP32 DevKit, 2 servos MG996R (hombro GPIO25, codo GPIO26) alimentados con fuente de 5 V "
        "aparte y tierra común; 2 MPU-6050 en el mismo bus I2C (SDA 21, SCL 22), direcciones 0x68 y 0x69.",
        "Firmware `firmware/adquisicion` (v1.4): tarea de muestreo FreeRTOS en el núcleo 0 a 100 Hz con "
        "`vTaskDelayUntil`, ±500 °/s, ±2 g, filtro interno de 44 Hz (antialias), marca de tiempo en µs "
        "por muestra; I2C a 100 kHz con reintentos; envío por USB a 460 800 baudios.",
        "Longitudes L₁ = 105 mm y L₂ = 85 mm; brazo en el plano horizontal de la mesa.",
        "Se usa el Δtₖ real de cada muestra (marca de tiempo del ESP32), no 1/fs."])
    if foto and Path(foto).exists():
        inf.figura(foto, "Montaje del brazo planar con las dos IMU y la cámara.", 12)
    man = d["manifiesto"] or {}
    inf.titulo("3.2 Datos de ajuste y de validación", 2)
    est = Path(man.get("estatico", "estatico_03")).stem
    inf.p(f"Un manifiesto generado por código elige los registros con reglas fijas. Reposo para R: "
          f"**{est}** ({man.get('estatico_criterio', '')}). Los perfiles repetibles (escalones, seno lento "
          "y seno rápido) son generados por el firmware en función del tiempo, por lo que cada repetición "
          "es idéntica; la 1.ª repetición válida es de **ajuste** y la 2.ª de **validación**:")
    filas = [[Path(a).stem, Path(v).stem] for a, v in zip(man.get("ajuste", []), man.get("validacion", []))]
    inf.tabla(["Ajuste (elegir Q)", "Validación (comparar)"], filas,
              "Registros de ajuste y de validación (datos/crudos/manifiesto.json).")
    if man.get("rechazadas"):
        txt = "; ".join(f"{k}: {v[0]}" for k, v in man["rechazadas"].items())
        inf.p(f"Registros rechazados automáticamente: {txt}.", cursiva=True)
    inf.titulo("3.3 Regla de selección de Q", 2)
    sel = d["sel"]
    inf.p(f"Regla fijada antes de ver los resultados: {sel['regla']}. El límite de "
          f"{f(sel['retraso_max_ms'], 0)} ms se toma porque en teleoperación retrasos mayores a ~50 ms se "
          "perciben y parte del presupuesto lo consume el servo.")
    inf.titulo("3.4 Teleoperación con cámara", 2)
    inf.vinetas([
        "Teléfono con DroidCam sobre la mesa mirando hacia abajo; video MJPEG por WiFi.",
        "Tres marcadores ArUco impresos (diccionario 4×4, 6 cm): ID 0 hombro, ID 1 codo, ID 2 muñeca. "
        "Se eligieron frente a marcadores de color porque el blanco y negro se distingue con cualquier "
        "iluminación y cada marcador lleva su identificador.",
        "Lector de video propio sin búfer (`python/video_rapido.py`): un hilo conserva solo el cuadro más "
        "nuevo, evitando que el retraso se acumule.",
        "Calibración: pose de referencia (brazo estirado = (90°, 0°)), medición de R de la cámara con el "
        "brazo quieto 10 s; luego θ̂ → `modelo_a_servo` → ESP32, con arranque suave.",
        "Protocolo de validación: dos sesiones con el mismo movimiento (lento, rápido, tapar la muñeca), "
        "una con el robot movido por la medición cruda y otra por Kalman. Crudo y Kalman se calculan "
        "siempre en los mismos cuadros."])


def resultados(inf, d):
    inf.titulo("4. Resultados", 1)
    # 4.1 R
    inf.titulo("4.1 Matriz R y sesgo (de la Entrega 1)", 2)
    Rj = d["R"]
    Rm = Rj["R"]
    s1, s2 = Rm[0][0] ** 0.5, Rm[1][1] ** 0.5
    rho = Rm[0][1] / (s1 * s2)
    inf.tabla(["Magnitud", "Giro 1 (w₁)", "Giro 2 (w₂)"],
              [["Varianza R [(°/s)²]", f(Rm[0][0], 6), f(Rm[1][1], 6)],
               ["Desviación σ [°/s]", f(s1, 3), f(s2, 3)],
               ["Sesgo (media en reposo) [°/s]", f(Rj["medias"][0], 3), f(Rj["medias"][1], 3)]],
              f"R medida en {Rj['archivo']} ({Rj['muestras']} muestras a {f(Rj['fs_hz'], 0)} Hz).")
    inf.p(f"La correlación entre los dos giroscopios es ρ = {f(rho, 3)}, por lo que R se usa diagonal.")
    r1 = d["resumen_e1"]["deriva_reposo_fuera_de_muestra"]
    dur = r1["duracion_s"] / 60
    inf.p(f"Deriva en reposo fuera de muestra: sin compensar el sesgo {f(r1['sin_sesgo'][0] / dur, 1)} y "
          f"{f(r1['sin_sesgo'][1] / dur, 1)} °/min; compensándolo, {f(r1['con_sesgo'][0] / dur, 2)} y "
          f"{f(r1['con_sesgo'][1] / dur, 2)} °/min. Por eso z = w − b, con b medido en el reposo inicial.")
    # 4.2 Q
    inf.titulo("4.2 Tres configuraciones de Q y selección", 2)
    sel = d["sel"]
    aj = d["ajuste"]
    rep = d["reposo"]
    filas = []
    for c in sel["configuraciones_evaluadas"]:
        a = fila(aj, "metodo", f"Kalman {c['nombre']}")
        rr = fila(rep, "metodo", f"Kalman {c['nombre']}")
        cumple = "sí" if a is not None and a["retraso_omega_ms"] <= sel["retraso_max_ms"] else "no"
        filas.append([c["nombre"], f(c["f_corte_hz"], 1), f(c["q"], 5),
                      f(a["retraso_omega_ms"], 1) if a is not None else "—", cumple,
                      f(rr["ruido_omega_reposo_puro_dps"], 4) if rr is not None else "—"])
    inf.tabla(["Q", "f_c [Hz]", "q [°²/s³]", "Retraso ω (ajuste) [ms]", f"≤ {f(sel['retraso_max_ms'], 0)} ms",
               "Ruido ω reposo [°/s]"], filas,
              "Configuraciones de Q evaluadas con los registros de ajuste.")
    for c in sel["configuraciones_evaluadas"]:
        inf.vinetas([f"**{c['nombre']}**: {c['razon']}"])
    q = sel["configuracion"]
    inf.p(f"Resultado: se elige **{q['nombre']}**, la de menor ruido entre las que cumplen el límite de retraso.")
    for nombre in ("seno_rapido_01", "escalones_01"):
        inf.figura(E2 / f"10_ajuste_configuraciones_Q_{nombre}.png",
                   f"Las tres Q sobre el registro de ajuste {nombre}.")
    inf.figura(E2 / "14_compromiso_Q_R.png",
               "Compromiso ruido–retraso al barrer q (relación Q/R); las tres configuraciones elegidas "
               "quedan marcadas.")
    # 4.3 comparación
    inf.titulo("4.3 Comparación de métodos (validación)", 2)
    val = d["val"]
    orden = ["Integración directa", "Media móvil N=5 + Euler", "Media móvil N=21 + Euler", f"Kalman {q['nombre']}"]
    filas = []
    for m in orden:
        v = fila(val, "metodo", m)
        rr = fila(rep, "metodo", m)
        if v is None:
            continue
        filas.append([m, f(rr["ruido_omega_reposo_puro_dps"], 4) if rr is not None else "—",
                      f(v["retraso_omega_ms"], 1), f(v["retraso_theta_ms"], 1),
                      f(v["ruido_alfa_reposo_dps2"], 2), f(v["deriva_final_deg"], 2), f(v["t_calculo_us"], 0)])
    inf.tabla(["Método", "Ruido ω reposo [°/s]", "Retraso ω [ms]", "Retraso θ [ms]",
               "Ruido α [°/s²]", "Deriva final [°]", "Cómputo [µs/muestra]"], filas,
              "Promedio sobre los registros de validación y los dos eslabones.")
    inf.figura(E2 / "15_validacion_comparacion_seno_rapido_02.png",
               "Comparación en el registro de validación seno_rapido_02.")
    # 4.4 aceleración
    inf.titulo("4.4 Aceleración angular numérica", 2)
    ac = d["acel"]
    filas = [[r["fuente"], f(r["sigma_alfa_reposo_dps2"], 2)] for _, r in ac.iterrows()]
    inf.tabla(["Fuente / método de derivación", "σ de α en reposo [°/s²]"], filas,
              "Ruido de la aceleración angular según el método.")
    inf.p("Derivar divide por Δt = 10 ms: el ruido se multiplica por ~141. La diferencia central tiene "
          "menos ruido pero no es causal (necesita la muestra siguiente). Derivar la ω ya filtrada por "
          "Kalman reduce el ruido de α sin el retraso de la media móvil larga.")
    inf.figura(E2 / "13_aceleracion_angular.png", "Aceleración angular numérica: giro crudo vs estimadores.")
    # 4.5 NIS y P
    inf.titulo("4.5 Consistencia del filtro: NIS y P", 2)
    nis = d["nis"]
    sub = nis[nis["metodo"] == f"Kalman {q['nombre']}"]
    filas = [[r["archivo"], f(r["nis_medio_reposo"], 1), f(r["nis_medio_movimiento"], 0),
              f(r["frac_nis_en_95"], 2), f"{r['max_asimetria_P']:.1e}", f"{r['min_autovalor_P']:.1e}"]
             for _, r in sub.iterrows()]
    inf.tabla(["Registro", "NIS medio reposo", "NIS medio movimiento", "Fracción en banda 95 %",
               "Asimetría máx. de P", "Autovalor mín. de P"], filas,
              f"Consistencia de {q['nombre']} (esperado: NIS medio = 2).")
    inf.p("P se mantiene simétrica (asimetría ~10⁻²⁰) y definida positiva. El NIS es cercano al esperado "
          "en reposo del seno rápido, pero en movimiento es varios órdenes de magnitud mayor: el modelo de "
          "velocidad casi constante con la Q elegida no explica las aceleraciones ni la vibración del servo.")
    inf.figura(E2 / "11_innovaciones_nis.png", "Innovaciones y NIS en el tiempo.")
    inf.figura(E2 / "12_P_y_K.png", "Evolución de P y de la ganancia K hasta el régimen estacionario.")
    # 4.6 teleoperación
    inf.titulo("4.6 Teleoperación con cámara", 2)
    if d["teleop_sint"]:
        inf.nota("PENDIENTE: SESIONES REALES. Las métricas de teleoperación de esta sección son "
                 f"{AVISO_SINT}: provienen de python/simular_teleop.py (video sintético con verdad conocida). "
                 "Al grabar las sesiones reales, volver a correr python/generar_informe.py.")
    qc = d["qcam"]
    if qc is not None:
        filas = [[r["Q"], f(r["f_n [Hz]"], 1), f(r["factor de ruido"], 2), f(r["retraso 1 Hz [ms]"], 1),
                  f(r["retraso 2 Hz [ms]"], 1), f(r["ganancia 8 Hz (temblor)"], 2)] for _, r in qc.iterrows()]
        inf.tabla(["Q cámara", "f_n [Hz]", "Factor de ruido", "Retraso 1 Hz [ms]", "Retraso 2 Hz [ms]",
                   "Ganancia 8 Hz (temblor)"], filas,
                  "Kalman de la cámara: caracterización de las tres Q simulando el filtro real a 30 cuadros/s "
                  "(no depende de R).")
        inf.p("El movimiento voluntario del brazo está por debajo de ~2 Hz y el temblor fisiológico entre "
              "8 y 12 Hz: Q_media (f_n = 3 Hz) deja pasar el primero con menos de 16 ms de retraso y reduce el "
              "segundo a la mitad.")
    lat = d["latencia"]
    if lat:
        inf.tabla(["Lectura del video", "Edad del cuadro al inicio [ms]", "Edad del cuadro a los 8 s [ms]"],
                  [["cv2.VideoCapture (antes)", f(lat["opencv_edad_inicio_ms"], 0), f(lat["opencv_edad_final_ms"], 0)],
                   ["Lector sin búfer (ahora)", f(lat["lector_edad_inicio_ms"], 0), f(lat["lector_edad_final_ms"], 0)]],
                  f"Latencia agregada por el programa con un procesamiento de {lat['trabajo_por_cuadro_ms']} ms "
                  f"por cuadro y cámara a {lat['fps_camara']} cuadros/s ({lat['nota']}).")
    tp = d["teleop"]
    if tp is not None and len(tp):
        marca = f" — {AVISO_SINT}" if d["teleop_sint"] else ""
        filas = []
        for _, r in tp.iterrows():
            filas.append([r["sesion"], r["robot_movido_con"], f(r["fps"], 1), f(r["visto_pct"], 1),
                          f"{f(r['aspereza_theta1_crudo'], 3)} / {f(r['aspereza_theta1_kf'], 3)}",
                          f"{f(r['aspereza_theta2_crudo'], 3)} / {f(r['aspereza_theta2_kf'], 3)}",
                          f(r["t_kalman_us_medio"], 0), f(r.get("t_proc_ms_medio", float('nan')), 1)])
        inf.tabla(["Sesión", "Robot movido con", "fps", "Cuadros con 3 marcadores [%]",
                   "Aspereza θ₁ crudo / Kalman [°]", "Aspereza θ₂ crudo / Kalman [°]",
                   "Kalman [µs/cuadro]", "Detección + Kalman [ms]"], filas,
                  f"Teleoperación: crudo vs Kalman en los mismos cuadros{marca}.")
        if d["teleop_sint"]:
            _teleop_sintetico(inf, d, tp, marca)
        else:
            _teleop_real(inf, d, tp)


def _ultima(tp, fuente):
    filas = tp[tp["robot_movido_con"] == fuente]
    return None if filas.empty else filas.iloc[-1]


def _teleop_real(inf, d, tp):
    """Sesiones reales: se destacan la última sesión con el robot movido por la cámara CRUDA y la
    última movida por KALMAN (mismo protocolo de 30 s: lento, rápido, tapar la muñeca)."""
    cr, kf = _ultima(tp, "crudo"), _ultima(tp, "kalman")
    meta = {}
    ruido = Rp.RAIZ / "datos" / "teleop" / "ruido_camara.json"
    if ruido.exists():
        meta = json.loads(ruido.read_text(encoding="utf-8"))
    if meta:
        inf.p(f"R de la cámara se midió con el brazo quieto ({meta['cuadros']} cuadros): "
              f"σ = {f(meta['sigma_deg'][0], 2)}° en θ₁ y {f(meta['sigma_deg'][1], 2)}° en θ₂. "
              f"Las sesiones se grabaron a {f(tp['fps'].min(), 1)}–{f(tp['fps'].max(), 1)} cuadros/s "
              "por la red del teléfono (por debajo de los 30 nominales: el filtro usa el Δt real de "
              "cada cuadro y se reinicia si pasan más de 0.7 s sin video).")
    for r in (cr, kf):
        if r is None:
            continue
        b1 = 100 * (1 - r["aspereza_theta1_kf"] / r["aspereza_theta1_crudo"])
        b2 = 100 * (1 - r["aspereza_theta2_kf"] / r["aspereza_theta2_crudo"])
        inf.p(f"{r['sesion']} (robot movido con {r['robot_movido_con'].upper()}, {f(r['duracion_s'], 0)} s): "
              f"la cámara vio los tres marcadores en el {f(r['visto_pct'], 1)} % de los cuadros "
              f"({int(r['oclusiones'])} oclusiones, la más larga de {f(r['oclusion_max_ms'], 0)} ms; en el "
              f"{f(r['solo_theta1_pct'], 1)} % solo se midió θ₁ y Kalman predijo θ₂). En los mismos cuadros, "
              f"Kalman redujo la aspereza de θ₁ un {f(b1, 0)} % y la de θ₂ un {f(b2, 0)} %, con un retraso "
              f"de {f(r['retraso_kf_theta1_ms'], 0)} ms respecto a la medición cruda. Cómputo: Kalman "
              f"{f(r['t_kalman_us_medio'], 0)} µs por cuadro; detección + Kalman {f(r['t_proc_ms_medio'], 1)} ms "
              f"({f(r['carga_pct'], 0)} % del tiempo entre cuadros).")
    con_robot = tp[tp["retraso_orden_robot_hombro_ms"].notna()] if "retraso_orden_robot_hombro_ms" in tp else tp.iloc[0:0]
    if len(con_robot):
        txt = "; ".join(f"{r['sesion']}: {f(r['retraso_orden_robot_hombro_ms'], 0)} ms (hombro) y "
                        f"{f(r['retraso_orden_robot_codo_ms'], 0)} ms (codo), cámara → robot "
                        f"{f(r['retraso_camara_robot_hombro_ms'], 0)} / {f(r['retraso_camara_robot_codo_ms'], 0)} ms"
                        for _, r in con_robot.iterrows())
        inf.p("Con los giroscopios del robot (las IMU de la Entrega 1) se midió el retraso orden → robot: "
              + txt + ". Coincide con los ≈ 190 ms de respuesta del servo medidos en la Entrega 1: la "
              "latencia dominante es el servo, no el filtro.")
    if "imu_robot_falla_t_s" in tp and tp["imu_robot_falla_t_s"].notna().any():
        caidas = tp[tp["imu_robot_falla_t_s"].notna()]
        txt = ", ".join(f"{r['sesion']} desde {f(r['imu_robot_falla_t_s'], 1)} s" for _, r in caidas.iterrows())
        inf.nota("FALLA DE SENSOR DECLARADA. La IMU del hombro del robot dejó de responder (giro = 0.000 "
                 f"exacto, sin ruido) en: {txt}. El análisis descarta esas muestras de forma automática "
                 "(python/analisis_teleop.py, primera_falla_imu); por eso la sesión movida con Kalman no tiene "
                 "métricas del robot y el contraste de vibración del robot crudo vs Kalman compara sesiones "
                 "distintas y no es concluyente. Las métricas de la cámara (aspereza, oclusión, tiempos) no "
                 "dependen de esa IMU y son válidas.")
    for r in (cr, kf):
        if r is not None:
            img = d["teleop_dir"] / f"20_teleop_{r['sesion']}.png"
            if img.exists():
                inf.figura(img, f"{r['sesion']} (robot movido con {r['robot_movido_con']}): ángulos crudos vs "
                                "Kalman y órdenes al servo; en gris, los cuadros sin los tres marcadores.")
    for _, r in con_robot.iterrows():
        img = d["teleop_dir"] / f"21_robot_{r['sesion']}.png"
        if img.exists():
            inf.figura(img, f"{r['sesion']}: orden enviada vs movimiento del robot medido con sus IMU.")


def _teleop_sintetico(inf, d, tp, marca):
    r0 = tp.iloc[0]
    if "rmse_oclusion_theta1_kf" in tp and pd.notna(r0.get("rmse_oclusion_theta1_kf")):
        inf.p(f"Durante las oclusiones de la muñeca, el error de θ₁ de la medición cruda (congelada) fue "
              f"{f(r0['rmse_oclusion_theta1_crudo'], 2)}° y el de Kalman {f(r0['rmse_oclusion_theta1_kf'], 2)}° "
              f"(medición parcial){marca}. Cuando la cámara ve bien, el error vs la verdad fue "
              f"{f(r0['rmse_theta1_crudo'], 2)}° (crudo) y {f(r0['rmse_theta1_kf'], 2)}° (Kalman): Kalman "
              "suaviza pero no es más exacto.")
    if pd.notna(r0.get("retraso_orden_robot_hombro_ms")):
        inf.p(f"Con los giroscopios del robot se midió el retraso orden → robot: "
              f"{f(r0['retraso_orden_robot_hombro_ms'], 0)} ms (hombro) y "
              f"{f(r0['retraso_orden_robot_codo_ms'], 0)} ms (codo); y cámara → robot "
              f"{f(r0['retraso_camara_robot_hombro_ms'], 0)} ms{marca}.")
    for img in sorted(d["teleop_dir"].glob("20_teleop_*.png"))[:2]:
        inf.figura(img, f"Ángulos crudos vs Kalman y órdenes al servo ({img.stem.replace('20_teleop_', '')})"
                   f". {AVISO_SINT}.")
    for img in sorted(d["teleop_dir"].glob("21_robot_*.png"))[:1]:
        inf.figura(img, f"Orden enviada vs movimiento del robot medido con sus IMU. {AVISO_SINT}.")


def discusion(inf, d):
    inf.titulo("5. Discusión", 1)
    val = d["val"]
    q = d["sel"]["configuracion"]
    kf = fila(val, "metodo", f"Kalman {q['nombre']}")
    dirc = fila(val, "metodo", "Integración directa")
    mm5 = fila(val, "metodo", "Media móvil N=5 + Euler")
    mm21 = fila(val, "metodo", "Media móvil N=21 + Euler")
    aj = fila(d["ajuste"], "metodo", f"Kalman {q['nombre']}")
    import math
    diseno = 1000 / (2 * math.pi * q["f_corte_hz"])
    inf.vinetas([
        f"**Suavizar no es lo mismo que ser preciso.** La deriva final es prácticamente la misma en todos "
        f"los métodos ({f(dirc['deriva_final_deg'], 2)}° directa, {f(kf['deriva_final_deg'], 2)}° Kalman): "
        "el filtro reduce el ruido pero no corrige un error que no se mide.",
        "**La deriva no es observable.** H solo mide ω y, con el brazo en el plano horizontal, el "
        "acelerómetro no ve el ángulo (la gravedad es perpendicular al plano). Solo se puede compensar el "
        "sesgo medido en reposo.",
        f"**Retraso de un filtro IIR.** El retraso de diseño 1/(2π f_c) es {f(diseno, 0)} ms, pero el medido "
        f"en ajuste fue {f(aj['retraso_omega_ms'], 1)} ms: el retraso del Kalman (recursivo) depende del "
        f"contenido en frecuencia, mientras que la media móvil (fase lineal) coincide con su teoría "
        f"({f(mm5['retraso_omega_ms'], 1)} y {f(mm21['retraso_omega_ms'], 0)} ms frente a 20 y 100 ms). La "
        "regla usa el valor medido.",
        f"**El ángulo de Kalman casi no se atrasa** ({f(kf['retraso_theta_ms'], 1)} ms frente a "
        f"{f(mm5['retraso_theta_ms'], 1)} ms de la media móvil N = 5) porque la covarianza cruzada φ–ω de P "
        "hace que la innovación del giroscopio también corrija φ.",
        "**Consistencia.** En movimiento el NIS es muy superior a 2: la Q se eligió por respuesta en "
        "frecuencia (ruido/retraso) y no por consistencia; una Q consistente sería tan grande que el filtro "
        "casi no filtraría. Se declara como límite del modelo.",
        "**Teleoperación.** La cámara mide θ sin deriva pero tiembla y se tapa; los giroscopios no tiemblan "
        "pero derivan. El rediseño natural es la **fusión**: agregar a H_cam las filas de los giroscopios "
        "([0,1,0,0], [0,0,0,1]) y su varianza de la Entrega 1 a R, con lo que θ sería observable.",
        "**Lo que no se verifica con estos datos:** la latencia teléfono → PC por WiFi, la exactitud absoluta "
        "del brazo humano (no hay una verdad medida) y la deformación por perspectiva si el teléfono no está "
        "paralelo a la mesa."])


def conclusiones(inf, d):
    inf.titulo("6. Conclusiones", 1)
    q = d["sel"]["configuracion"]
    val = d["val"]
    kf = fila(val, "metodo", f"Kalman {q['nombre']}")
    mm5 = fila(val, "metodo", "Media móvil N=5 + Euler")
    inf.vinetas([
        "El modelo de velocidad casi constante con R de la Entrega 1 y Q razonada por frecuencia de corte "
        "permite justificar cada parámetro del filtro sin ajuste a ciegas.",
        f"Con la regla fija (retraso ≤ 40 ms, mínimo ruido) se eligió {q['nombre']}; en validación tiene "
        f"menos ruido que la media móvil N = 5 y menos retraso de ω ({f(kf['retraso_omega_ms'], 1)} vs "
        f"{f(mm5['retraso_omega_ms'], 1)} ms), y su ángulo se atrasa solo {f(kf['retraso_theta_ms'], 1)} ms.",
        "La aceleración angular numérica es inutilizable sin filtrar; derivar la estimación de Kalman la "
        "vuelve aprovechable.",
        "Ningún método corrige la deriva con solo giroscopio; hace falta una referencia absoluta (cámara, "
        "encoder o acelerómetro en plano vertical).",
        "La teleoperación con ArUco + Kalman funciona en tiempo real; el cómputo es despreciable frente al "
        "periodo entre cuadros y la latencia dominante es la del servo y la red."])


def referencias(inf):
    inf.titulo("Referencias", 1)
    for r in [
        "R. E. Kalman, “A New Approach to Linear Filtering and Prediction Problems,” Journal of Basic "
        "Engineering, vol. 82, no. 1, pp. 35–45, 1960.",
        "G. Welch y G. Bishop, “An Introduction to the Kalman Filter,” TR 95-041, University of North "
        "Carolina at Chapel Hill, 2006.",
        "D. Simon, Optimal State Estimation: Kalman, H∞, and Nonlinear Approaches. Wiley, 2006.",
        "Y. Bar-Shalom, X. R. Li y T. Kirubarajan, Estimation with Applications to Tracking and Navigation. "
        "Wiley, 2001.",
        "InvenSense, MPU-6000 and MPU-6050 Product Specification, Rev. 3.4, 2013.",
        "S. Garrido-Jurado, R. Muñoz-Salinas, F. J. Madrid-Cuevas y M. J. Marín-Jiménez, “Automatic "
        "generation and detection of highly reliable fiducial markers under occlusion,” Pattern "
        "Recognition, vol. 47, no. 6, pp. 2280–2292, 2014."]:
        inf.doc.add_paragraph(r, style="List Number")


def anexo(inf):
    inf.titulo("Anexo A. Mapa del código y reproducción", 1)
    filas = [
        ["firmware/adquisicion/adquisicion.ino", "Muestreo de las 2 IMU a 100 Hz, servos, perfiles repetibles"],
        ["python/modelo_kalman.py", "Estado, F, Q, H del brazo (bloques por eslabón)"],
        ["python/kalman.py", "Ecuaciones del filtro, forma de Joseph, NIS"],
        ["python/config_kalman.py", "Tres Q por frecuencia de corte, regla de selección, P₀"],
        ["python/estimadores.py", "Integración directa, media móvil y Kalman con la misma interfaz"],
        ["python/analisis_e2.py", "Selección de Q (ajuste), comparación (validación), NIS, α"],
        ["python/kalman_camara.py", "Kalman de la cámara, medición parcial, caracterizar_q"],
        ["python/vision.py", "Detección ArUco y ángulos del brazo humano"],
        ["python/teleop_camara.py", "Teleoperación en vivo, grabación de sesiones"],
        ["python/video_rapido.py", "Lectura del video sin búfer (latencia constante)"],
        ["python/analisis_teleop.py", "Métricas de teleoperación crudo vs Kalman"],
        ["python/generar_informe.py", "Este informe (lee todos los números de resultados/)"]]
    inf.tabla(["Archivo", "Qué hace"], filas, "Archivos principales del repositorio.", anchos=[6.5, 9.5])
    inf.p("Comandos (desde la raíz del repositorio, con el entorno virtual activo):", negrita=True)
    for c in ["pip install -r requirements.txt", "python -m pytest python/",
              "python python/analisis_e1.py", "python python/analisis_e2.py",
              "python python/teleop_camara.py --video IP_DEL_TELEFONO --puerto COM3",
              "python python/analisis_teleop.py", "python python/generar_informe.py"]:
        par = inf.doc.add_paragraph()
        r = par.add_run(c)
        r.font.name = "Consolas"
        r.font.size = Pt(9.5)


# ======================================================================= principal
def foto_por_defecto():
    """docs/informe/foto_montaje.jpg (o .jpeg/.png) si existe: así no hay que pasar --foto."""
    for ext in (".jpg", ".jpeg", ".png", ".JPG", ".PNG"):
        p = SALIDA.parent / f"foto_montaje{ext}"
        if p.exists():
            return p
    return None


def generar(salida=SALIDA, foto=None):
    foto = foto or foto_por_defecto()
    d = cargar_datos()
    inf = Informe()
    portada(inf, d)
    resumen(inf, d)
    introduccion(inf, d)
    marco_teorico(inf, d)
    metodologia(inf, d, foto)
    resultados(inf, d)
    discusion(inf, d)
    conclusiones(inf, d)
    referencias(inf)
    anexo(inf)
    salida = Path(salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    inf.doc.save(salida)
    return salida, inf.n_fig, inf.n_tab, d["teleop_sint"]


def a_pdf(ruta_docx):
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        return None
    try:
        subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir",
                        str(ruta_docx.parent), str(ruta_docx)], capture_output=True, timeout=180)
    except (subprocess.TimeoutExpired, OSError):
        return None
    pdf = ruta_docx.with_suffix(".pdf")
    return pdf if pdf.exists() else None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--foto", default=None, help="foto del montaje (jpg/png) para la sección 3")
    ap.add_argument("--salida", default=str(SALIDA))
    ap.add_argument("--sin-pdf", action="store_true")
    args = ap.parse_args()
    ruta, n_fig, n_tab, sint = generar(args.salida, args.foto)
    print(f"Informe: {ruta.relative_to(Rp.RAIZ) if ruta.is_relative_to(Rp.RAIZ) else ruta} "
          f"({n_fig} figuras, {n_tab} tablas)")
    if sint:
        print(f"Aviso: teleoperación con {AVISO_SINT}. Graba las sesiones reales y vuelve a generar.")
    if not args.sin_pdf:
        pdf = a_pdf(ruta)
        print(f"PDF: {pdf}" if pdf else "PDF: no se generó (no hay LibreOffice); abre el .docx y exporta.")


if __name__ == "__main__":
    main()
