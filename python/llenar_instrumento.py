"""Diligencia el INSTRUMENTO de evaluación de la Entrega 2 y le agrega los RESULTADOS (Anexo A).

    python python/llenar_instrumento.py
    python python/llenar_instrumento.py --equipo 07 --integrantes "Juan Cely (1234567)" "Otra Persona (7654321)" \
        --entrega "Juan Cely" --fecha 2026-11-18

Toma la plantilla del docente (docs/entrega/plantilla_INSTRUMENTO_PDS_KALMAN_ENTREGA_2_v2.0.docx) y:
  1. llena la identificación (sección 1) con lo que se sabe; lo que no, queda "⟨COMPLETAR⟩" en amarillo;
  2. llena el registro mínimo de evidencias E5–E9 (sección 3) con archivo + parte del Anexo A;
  3. escribe el localizador de cada criterio (sección 4). NO marca niveles ni puntajes: eso es del docente;
  4. agrega al final el ANEXO A con los resultados (ecuaciones, tablas y figuras) por evidencia.

Todos los números salen de resultados/ (generar_informe.cargar_datos): nada se copia a mano.
Salida: docs/entrega/INSTRUMENTO_PDS_KALMAN_ENTREGA_2_Equipo<NN>_v2.0.docx (+ .pdf si hay LibreOffice).
"""
import argparse
import json
import math
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_COLOR_INDEX, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

import generar_informe_ieee as IE
import reporte as Rp
from generar_informe import E1, E2, cargar_datos, f, fila

CARPETA = Rp.RAIZ / "docs" / "entrega"
PLANTILLA = CARPETA / "plantilla_INSTRUMENTO_PDS_KALMAN_ENTREGA_2_v2.0.docx"
PEND = "⟨COMPLETAR⟩"
AZUL = "1F4E78"                       # color de los encabezados de tabla de la plantilla
ANCHO_FIG_CM = 16.5


# ====================================================================== utilidades de escritura
def _run(par, texto, tam=None, negrita=False, cursiva=False, color=None):
    """Agrega texto; ⟨COMPLETAR⟩ sale en amarillo y **negrita** entre dobles asteriscos."""
    for i, trozo in enumerate(texto.split("**")):
        for j, t in enumerate(trozo.split(PEND)):
            if j > 0:
                r = par.add_run(PEND)
                r.bold = True
                r.font.highlight_color = WD_COLOR_INDEX.YELLOW
                if tam:
                    r.font.size = Pt(tam)
            if not t:
                continue
            # subíndices de una letra: φ_i, Δt_k, f_c, H_cam (como en el informe IEEE)
            piezas, pos = [], 0
            for m in IE.SUBINDICE.finditer(t):
                piezas += [(t[pos:m.end(1)], False), (m.group(2).strip("{}"), True)]
                pos = m.end()
            piezas.append((t[pos:], False))
            for txt, sub in piezas:
                if not txt:
                    continue
                r = par.add_run(txt)
                r.bold = negrita or (i % 2 == 1)
                r.italic = cursiva
                r.font.subscript = sub or None
                if tam:
                    r.font.size = Pt(tam)
                if color:
                    r.font.color.rgb = RGBColor.from_string(color)
    return par


def poner_en_celda(celda, texto, tam=8):
    par = celda.paragraphs[0]
    for r in list(par.runs):
        r._r.getparent().remove(r._r)
    for k, linea in enumerate(texto.split("\n")):
        p = par if k == 0 else celda.add_paragraph(style=par.style)
        _run(p, linea, tam)


def sin_numeracion(par):
    """Los títulos de la plantilla van numerados (1., 2., …); el anexo no."""
    pPr = par._p.get_or_add_pPr()
    numPr = OxmlElement("w:numPr")
    numId = OxmlElement("w:numId")
    numId.set(qn("w:val"), "0")
    numPr.append(numId)
    pPr.append(numPr)


def estilo(doc, nombre):
    """Busca el estilo por su nombre visible (la plantilla lo guarda como "Heading 2", con mayúscula)."""
    for st in doc.styles:
        if st.name == nombre:
            return st
    return doc.styles["Normal"]


class Anexo:
    def __init__(self, doc):
        self.doc = doc
        self.n_fig = self.n_tab = self.n_eq = 0

    def titulo(self, texto, nivel=2):
        h = self.doc.add_paragraph(texto, style=estilo(self.doc, f"Heading {nivel}"))
        sin_numeracion(h)
        h.paragraph_format.keep_with_next = True
        return h

    def p(self, texto, tam=9.5):
        par = self.doc.add_paragraph(style=estilo(self.doc, "Body Text"))
        par.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        par.paragraph_format.space_after = Pt(4)
        return _run(par, texto, tam)

    def vinetas(self, items, tam=9.5):
        for it in items:
            par = self.doc.add_paragraph(style=estilo(self.doc, "List Paragraph"))
            par.paragraph_format.left_indent = Cm(0.6)
            par.paragraph_format.first_line_indent = Cm(-0.35)
            par.paragraph_format.space_after = Pt(2)
            _run(par, "• " + it, tam)

    def ecuacion(self, nodo):
        self.n_eq += 1
        par = self.doc.add_paragraph()
        par.paragraph_format.space_before = Pt(2)
        par.paragraph_format.space_after = Pt(2)
        tabs = par.paragraph_format.tab_stops
        tabs.add_tab_stop(Cm(9.0), WD_TAB_ALIGNMENT.CENTER)
        tabs.add_tab_stop(Cm(18.5), WD_TAB_ALIGNMENT.RIGHT)
        par.add_run("\t")
        par._p.append(IE.omath(nodo))
        par.add_run(f"\t(A{self.n_eq})")

    def tabla(self, encabezado, filas, titulo, anchos_cm=None):
        self.n_tab += 1
        cap = self.doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.paragraph_format.keep_with_next = True
        cap.paragraph_format.space_before = Pt(6)
        _run(cap, f"Tabla A{self.n_tab}. ", 8.5, negrita=True)
        _run(cap, titulo, 8.5, cursiva=True)
        t = self.doc.add_table(rows=1, cols=len(encabezado))
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        bordes = OxmlElement("w:tblBorders")
        for lado in ("top", "left", "bottom", "right", "insideH", "insideV"):
            b = OxmlElement(f"w:{lado}")
            b.set(qn("w:val"), "single")
            b.set(qn("w:sz"), "4")
            b.set(qn("w:color"), "7F7F7F")
            bordes.append(b)
        t._tbl.tblPr.append(bordes)
        for c, h in zip(t.rows[0].cells, encabezado):
            c.text = ""
            sh = OxmlElement("w:shd")
            sh.set(qn("w:val"), "clear")
            sh.set(qn("w:color"), "auto")
            sh.set(qn("w:fill"), AZUL)
            c._tc.get_or_add_tcPr().append(sh)
            _run(c.paragraphs[0], str(h), 8, negrita=True, color="FFFFFF")
            c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        for fil in filas:
            for c, v in zip(t.add_row().cells, fil):
                c.text = ""
                _run(c.paragraphs[0], str(v), 8)
                c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        for k, fil in enumerate(t.rows):
            fil._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
            if k < len(t.rows) - 1:
                for c in fil.cells:
                    c.paragraphs[0].paragraph_format.keep_with_next = True
        if anchos_cm:
            t.autofit = False
            for fil in t.rows:
                for c, w in zip(fil.cells, anchos_cm):
                    c.width = Cm(w)
        self.doc.add_paragraph().paragraph_format.space_after = Pt(2)
        return f"Tabla A{self.n_tab}"

    def figura(self, ruta, pie, ancho_cm=ANCHO_FIG_CM):
        ruta = Path(ruta)
        if not ruta.exists():
            return None
        self.n_fig += 1
        par = self.doc.add_paragraph()
        par.alignment = WD_ALIGN_PARAGRAPH.CENTER
        par.paragraph_format.keep_with_next = True
        par.add_run().add_picture(str(ruta), width=Cm(ancho_cm))
        cap = self.doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.paragraph_format.space_after = Pt(8)
        _run(cap, f"Figura A{self.n_fig}. ", 8.5, negrita=True)
        _run(cap, pie, 8.5, cursiva=True)
        return f"Figura A{self.n_fig}"

    def salto(self):
        self.doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


# ====================================================================== secciones 1, 3 y 4
def identificacion(doc, a, commit):
    fila_por = {r.cells[0].text.strip(): r for r in doc.tables[0].rows}

    def campo(prefijo, texto):
        for k, r in fila_por.items():
            if k.startswith(prefijo):
                poner_en_celda(r.cells[1], texto)
                return
        raise KeyError(prefijo)
    equipo = a.equipo or PEND
    integrantes = "\n".join(a.integrantes) if a.integrantes else f"Cely — código {PEND}\n{PEND} (nombre y código de los demás integrantes)"
    campo("Número y nombre del equipo", f"Equipo {equipo} — Brazo planar 2 GDL con filtro de Kalman y teleoperación por cámara")
    campo("Integrantes", integrantes)
    campo("Persona designada", a.entrega or PEND)
    campo("Repositorio", f"https://github.com/celytiorja/lab-Brazo-planar — rama claude/friendly-feynman-xfljpf, "
          f"etiqueta git entrega2; commit al generar este formato: {commit}")
    campo("Enlace de la entrega", "Mismo repositorio. Resultados: ANEXO A de este documento. Guía de evidencias: "
          "docs/LOCALIZADORES_E2.md. Informe de apoyo: docs/informe/Informe_Entrega2_IEEE.pdf")
    campo("Fecha de entrega", f"Entrega: {a.fecha or PEND} — Evaluación: (la registra el docente)")


EVIDENCIAS = {
    "E5": "Anexo A.1 (estado, mediciones, F, H, Q, R, x̂0, P0 y ecuaciones). Código: python/kalman.py (predicción, "
          "K, actualización con forma de Joseph, NIS); python/modelo_kalman.py (F, Q y H con el Δt_k real); "
          "python/estimadores.py (directa, media móvil, Kalman; θ2 = φ2 − φ1); python/config_kalman.py (3 Q, P0, "
          "regla ≤ 40 ms); R de la Entrega 1: resultados/reales/e1/R.json. Ejecución: python python/analisis_e2.py. "
          "Pruebas: python -m pytest python/.",
    "E6": "Anexo A.2 (Tablas de ajuste/validación y de las 3 Q). Datos: datos/crudos/*.csv + manifiesto.json; "
          "selección: resultados/reales/e2/seleccion_Q.json, resumen_seleccion_Q.md, metricas_e2_ajuste.md; "
          "cámara: resultados/reales/teleop/configuraciones_q_camara.md.",
    "E7": "Anexo A.3 (comparación de métodos, aceleración angular, consistencia y límites). Archivos: "
          "resultados/reales/e2/ metricas_e2_validacion_resumen.md, 15_validacion_comparacion_*.png, "
          "aceleracion_angular.md, 13_aceleracion_angular.png, consistencia_kalman.md, 12_P_y_K.png, "
          "compromiso_Q_R.md, 14_compromiso_Q_R.png; límites: docs/GUIA_ENTREGA2.md §4.",
    "E8": "Anexo A.4 (montaje, interfaz, crudo vs Kalman, tiempos y robot). En vivo: python python/teleop_camara.py "
          "--video <IP> --puerto auto. Sesiones: datos/teleop/sesion_03 (crudo) y sesion_04 (Kalman); métricas: "
          "python python/analisis_teleop.py → resultados/reales/teleop/resumen_teleop.md, 20_teleop_*.png, "
          f"21_robot_*.png; latencia: resultados/latencia_video.json. Video de apoyo: {PEND} (opcional).",
    "E9": "La registra el docente en la sección 6. Anexo A.5: preguntas del instrumento con el localizador de cada "
          "respuesta. Preparación: docs/ENTREGAS.md y docs/GUIA_ENTREGA2.md §5.",
}

LOCALIZADORES = {
    "C1": " E5–E7 → Anexo A.1 y A.3: modelo y ecuaciones (A1–A9), R de la E1 (Tabla A1), P simétrica y positiva "
          "y K estacionaria (Figura de P y K), Δt_k real en estimadores.paso(dt, …), aceleración angular con su "
          "amplificación de ruido (Tabla de aceleración). Acoplamiento articular θ2 = φ2 − φ1; bias como estado "
          "opcional justificado. Las 3 Q corren desde config_kalman.py con analisis_e2.py sin editar salidas.",
    "C2": " E6, E8 → Anexo A.2 y A.4: ajuste ≠ validación; directa, MM y Kalman en las mismas condiciones; "
          "teleoperación real con la estimación: sesión 03 (robot con crudo) vs sesión 04 (robot con Kalman), "
          "tiempos de cómputo por cuadro, latencia del lector de video y retraso orden→robot medido con el "
          "giroscopio del robot. Falla de la IMU del hombro del robot declarada y descartada por código.",
    "C3": " E6–E8 → Anexo A.2–A.4: regla ≤ 40 ms y elección de Q_media, compromiso Q/R cuantitativo (IMU y "
          "cámara), suavizado ≠ precisión, deriva igual en todos los métodos (no observable), NIS alto en "
          "movimiento como límite del modelo; rediseño propuesto: fusión cámara + giroscopios.",
}


def registro_y_localizadores(doc):
    for r in doc.tables[5].rows[1:]:
        cod = r.cells[0].text.strip()
        if cod in EVIDENCIAS:
            poner_en_celda(r.cells[2], EVIDENCIAS[cod])
    crit = None
    for p in doc.paragraphs:
        if p.text.startswith("Nivel C"):          # "Nivel C1 marcado: …" fija el criterio siguiente
            crit = p.text[6:8]
        if p.text.startswith("Localizador y observación"):
            if crit in LOCALIZADORES:
                tam = p.runs[0].font.size
                for r in list(p.runs):
                    if r.text == "\t":
                        r._r.getparent().remove(r._r)
                p.add_run(LOCALIZADORES[crit]).font.size = tam


# ====================================================================== ANEXO A: resultados
def anexo(doc, d):
    ax = Anexo(doc)
    ax.salto()
    ax.titulo("ANEXO A — Resultados y evidencias de la Entrega 2 (E5–E9)", 2)
    ax.p("Este anexo reúne los resultados del equipo para que se verifiquen junto con este instrumento. Todas las "
         "tablas y figuras se generan por código desde los datos del repositorio (python python/llenar_instrumento.py); "
         "ningún número se escribió a mano. Datos reales del robot (IMU a 100 Hz) y de la cámara del teléfono.")
    sel, q = d["sel"], d["sel"]["configuracion"]
    val, rep, aj = d["val"], d["reposo"], d["ajuste"]

    # ---------------------------------------------------------------- A.1 (E5)
    ax.titulo("A.1 Modelo e implementación del filtro de Kalman (E5)", 3)
    ax.p("**Estado y mediciones.** Para cada eslabón i se estima el ángulo absoluto φ_i [°] y la velocidad angular "
         "ω_i [°/s]: x = [φ1, ω1, φ2, ω2]ᵀ. Los giroscopios miden solo velocidad (con el sesgo b medido en reposo "
         "restado): z = [w1 − b1, w2 − b2]ᵀ [°/s]. La IMU 2 está sobre el eslabón 2, así que mide φ2 = θ1 + θ2 y el "
         "ángulo del codo es θ2 = φ2 − φ1 (acoplamiento articular). Modelo de velocidad casi constante, con el "
         "intervalo real Δt_k entre muestras (marca de tiempo del ESP32):")
    S, Sp, Fr, Mat, Par, T = IE.Sub, IE.Sup, IE.Fr, IE.Mat, IE.Par, IE.T
    ax.ecuacion([S("F", "i"), "=", Mat([["1", S("Δt", "k")], ["0", "1"]]), ",   ", S("Q", "i"), "=", "q",
                 Mat([[Fr(Sp(S("Δt", "k"), "3"), "3"), Fr(Sp(S("Δt", "k"), "2"), "2")],
                      [Fr(Sp(S("Δt", "k"), "2"), "2"), S("Δt", "k")]])])
    ax.ecuacion(["H", "=", Mat([["0", "1", "0", "0"], ["0", "0", "0", "1"]]), ",   ", "R", "=",
                 Mat([[f(d["R"]["R"][0][0], 5), "0"], ["0", f(d["R"]["R"][1][1], 5)]]), T("  (°/s)²")])
    ax.ecuacion([Sp(S("x̂", "k"), "−"), "=", "F", S("x̂", "k−1"), ",   ", Sp(S("P", "k"), "−"), "=",
                 "F", S("P", "k−1"), Sp("F", "T"), "+", "Q"])
    ax.ecuacion([S("K", "k"), "=", Sp(S("P", "k"), "−"), Sp("H", "T"),
                 Sp(Par(["H", Sp(S("P", "k"), "−"), Sp("H", "T"), "+", "R"]), "−1")])
    ax.ecuacion([S("x̂", "k"), "=", Sp(S("x̂", "k"), "−"), "+", S("K", "k"),
                 Par([S("z", "k"), "−", "H", Sp(S("x̂", "k"), "−")])])
    ax.ecuacion([S("P", "k"), "=", Par(["I", "−", S("K", "k"), "H"]), Sp(S("P", "k"), "−"),
                 Sp(Par(["I", "−", S("K", "k"), "H"]), "T"), "+", S("K", "k"), "R", Sp(S("K", "k"), "T"),
                 T("   (Joseph)")])
    ax.ecuacion([S("y", "k"), "=", S("z", "k"), "−", "H", Sp(S("x̂", "k"), "−"), ",   ", T("NIS"), "=",
                 Sp(S("y", "k"), "T"), Sp(S("S", "k"), "−1"), S("y", "k"), "∼", Sp("χ", "2"), Par("2")])
    ax.p("**Inicialización.** x̂0 = [φ1(0), 0, φ2(0), 0] desde la pose conocida de reposo; P0 = diag(2², 5², 2², 5²) "
         "(±2° de ángulo, ±5 °/s de velocidad). **Q a partir de una frecuencia de corte** f_c (la parte de ω es un "
         "paso bajo de primer orden en régimen estacionario):")
    ax.ecuacion(["K", "=", "1", "−", Sp("e", ["−2π", S("f", "c"), "Δt"]), ",   ", "q", "=",
                 Fr("r", "Δt"), Fr(Sp("K", "2"), ["1", "−", "K"])])
    Rj = d["R"]
    Rm = Rj["R"]
    r1 = d["resumen_e1"]["deriva_reposo_fuera_de_muestra"]
    dur = r1["duracion_s"] / 60
    ax.tabla(["Magnitud (Entrega 1)", "Giro 1", "Giro 2"],
             [["R [(°/s)²]", f(Rm[0][0], 5), f(Rm[1][1], 5)],
              ["σ [°/s]", f(Rm[0][0] ** 0.5, 3), f(Rm[1][1] ** 0.5, 3)],
              ["Sesgo b [°/s]", f(Rj["medias"][0], 2), f(Rj["medias"][1], 2)],
              ["Deriva sin restar b [°/min]", f(r1["sin_sesgo"][0] / dur, 1), f(r1["sin_sesgo"][1] / dur, 1)],
              ["Deriva restando b [°/min]", f(r1["con_sesgo"][0] / dur, 2), f(r1["con_sesgo"][1] / dur, 2)]],
             f"R fundamentada en la Entrega 1 ({Rj['archivo']}, {Rj['muestras']} muestras a 100 Hz); correlación "
             "entre giros ≈ 0 → R diagonal.", [6.5, 3.5, 3.5])
    ax.p("**Kalman de la cámara (teleoperación).** Mismo modelo con estado [θ1, ω1, θ2, ω2] y H_cam = [[1,0,0,0],"
         "[0,0,1,0]] (la cámara mide ángulos); q_cam = r·Δt·(2π f_n)⁴. Si la muñeca no se ve, H conserva solo la "
         "fila de θ1 (medición parcial) y θ2 se predice con ω̂, que la cámara no mide.")
    ax.figura(IE.diagrama_sistema(IE.SALIDA.parent / "diagrama_sistema.png"),
              "Diagrama de bloques del sistema (PC en azul, robot en verde, maestro y cámara en amarillo).", 15)

    # ---------------------------------------------------------------- A.2 (E6)
    ax.titulo("A.2 Datos de ajuste y validación y las tres configuraciones de Q (E6)", 3)
    man = d["manifiesto"] or {}
    ax.tabla(["Ajuste (elegir Q)", "Validación (comparar)"],
             [[Path(a_).stem, Path(v).stem] for a_, v in zip(man.get("ajuste", []), man.get("validacion", []))],
             f"Asignación automática (datos/crudos/manifiesto.json); reposo para R: "
             f"{Path(man.get('estatico', 'estatico_03')).stem}.", [6, 6])
    if man.get("rechazadas"):
        ax.p("Rechazados por código: " + "; ".join(f"{k} ({v[0]})" for k, v in man["rechazadas"].items()) + ".")
    filas = []
    for c in sel["configuraciones_evaluadas"]:
        a_ = fila(aj, "metodo", f"Kalman {c['nombre']}")
        rr = fila(rep, "metodo", f"Kalman {c['nombre']}")
        k = 1 - math.exp(-2 * math.pi * c["f_corte_hz"] * c["dt_usado"])
        cumple = "sí" if a_["retraso_omega_ms"] <= sel["retraso_max_ms"] else "no"
        filas.append([c["nombre"], f(c["f_corte_hz"], 1), f(k, 3), f(c["q"], 5), f(a_["retraso_omega_ms"], 1),
                      cumple, f(rr["ruido_omega_reposo_puro_dps"], 4)])
    ax.tabla(["Q", "f_c [Hz]", "K estacionaria", "q [°²/s³]", "Retraso ω [ms]",
              f"≤ {f(sel['retraso_max_ms'], 0)} ms", "Ruido ω reposo [°/s]"], filas,
             "Tres configuraciones razonadas de Q evaluadas en los registros de ajuste.")
    ax.vinetas([f"**{c['nombre']}**: {c['razon']}" for c in sel["configuraciones_evaluadas"]])
    ax.p(f"**Selección final:** {q['nombre']} (f_c = {f(q['f_corte_hz'], 0)} Hz, q = {f(q['q'], 5)} °²/s³). Regla fijada "
         f"antes de ver resultados: {sel['regla']}.")
    ax.figura(E2 / "10_ajuste_configuraciones_Q_seno_rapido_01.png",
              "Las tres Q sobre el registro de ajuste seno_rapido_01.")
    ax.figura(E2 / "14_compromiso_Q_R.png", "Compromiso ruido–retraso al barrer q (relación Q/R).", 12)
    qc = d["qcam"]
    if qc is not None:
        ax.tabla(["Q cámara", "f_n [Hz]", "Ruido ×", "Retraso 1 Hz [ms]", "Retraso 2 Hz [ms]", "Temblor 8 Hz ×"],
                 [[r["Q"], f(r["f_n [Hz]"], 1), f(r["factor de ruido"], 2), f(r["retraso 1 Hz [ms]"], 1),
                   f(r["retraso 2 Hz [ms]"], 1), f(r["ganancia 8 Hz (temblor)"], 2)] for _, r in qc.iterrows()],
                 "Tres Q del Kalman de la cámara (simulando el filtro real a 30 cuadros/s).")

    # ---------------------------------------------------------------- A.3 (E7)
    ax.titulo("A.3 Comparación de métodos, aceleración angular y consistencia (E7)", 3)
    filas = []
    for m in ("Integración directa", "Media móvil N=5 + Euler", "Media móvil N=21 + Euler", f"Kalman {q['nombre']}"):
        v, rr = fila(val, "metodo", m), fila(rep, "metodo", m)
        filas.append([m, f(rr["ruido_omega_reposo_puro_dps"], 4), f(v["retraso_omega_ms"], 1),
                      f(v["retraso_theta_ms"], 1), f(v["ruido_alfa_reposo_dps2"], 2), f(v["deriva_final_deg"], 2),
                      f(v["t_calculo_us"], 0)])
    ax.tabla(["Método", "Ruido ω [°/s]", "Retraso ω [ms]", "Retraso θ [ms]", "Ruido α [°/s²]", "Deriva [°]",
              "Cómputo [µs]"], filas,
             "Validación (registros distintos a los de ajuste), promedio de archivos y eslabones.",
             [4.2, 2.1, 2.1, 2.1, 2.1, 1.9, 2.0])
    kf = fila(val, "metodo", f"Kalman {q['nombre']}")
    mm5 = fila(val, "metodo", "Media móvil N=5 + Euler")
    ax.p(f"Con un retraso de ω similar al de la media móvil de 5 muestras ({f(kf['retraso_omega_ms'], 1)} vs "
         f"{f(mm5['retraso_omega_ms'], 1)} ms), Kalman tiene menos ruido y su ángulo se atrasa solo "
         f"{f(kf['retraso_theta_ms'], 1)} ms (vs {f(mm5['retraso_theta_ms'], 1)} ms). La deriva final es la misma en "
         "todos los métodos: filtrar no corrige un error que no se mide.")
    ax.figura(E2 / "15_validacion_comparacion_seno_rapido_02.png",
              "Directa, medias móviles y Kalman en el registro de validación seno_rapido_02.")
    ac = d["acel"]
    ax.tabla(["Fuente / esquema numérico", "σ de α en reposo [°/s²]"],
             [[r["fuente"], f(r["sigma_alfa_reposo_dps2"], 2)] for _, r in ac.iterrows()],
             "Aceleración angular numérica: α_k = (ω_k − ω_{k−1})/Δt (hacia atrás) o central; el ruido se "
             "amplifica como √2·σ_ω/Δt.", [10, 4])
    ax.figura(E2 / "13_aceleracion_angular.png", "Aceleración angular: giro crudo frente a los estimadores.")
    nis = d["nis"]
    sub = nis[nis["metodo"] == f"Kalman {q['nombre']}"]
    ax.tabla(["Registro", "NIS medio reposo", "NIS medio movimiento", "Fracción en banda 95 %",
              "Asimetría máx. de P", "Autovalor mín. de P"],
             [[r["archivo"], f(r["nis_medio_reposo"], 1), IE.cientifico(r["nis_medio_movimiento"]),
               f(r["frac_nis_en_95"], 2), IE.cientifico(r["max_asimetria_P"]), IE.cientifico(r["min_autovalor_P"])]
              for _, r in sub.iterrows()],
             f"Consistencia de {q['nombre']} (esperado: NIS medio = 2; P simétrica y definida positiva).")
    ax.figura(E2 / "12_P_y_K.png", "Covarianza P y ganancia K: convergen a su régimen estacionario.")
    ax.p("**Límites de lo verificable.**")
    ax.vinetas([
        "La deriva no es observable: H mide solo ω y, con el brazo en plano horizontal, el acelerómetro no ve el "
        "ángulo. Solo se compensa el sesgo medido en reposo.",
        "NIS ≫ 2 en movimiento: el modelo de velocidad casi constante no explica los arranques del servo; la Q se "
        "eligió por respuesta en frecuencia y se declara el límite.",
        "No hay una referencia absoluta del ángulo del brazo humano en la teleoperación: se afirma suavidad y "
        "continuidad en oclusiones, no mayor exactitud (suavizar ≠ precisión).",
        "La latencia teléfono → PC por WiFi no se mide con estos datos."])

    # ---------------------------------------------------------------- A.4 (E8)
    ax.titulo("A.4 Teleoperación del brazo usando la estimación (E8)", 3)
    montaje = IE.figura_montaje(IE.SALIDA.parent / "montaje.jpg")
    if montaje:
        ax.figura(montaje, "(a) Modelo CAD; (b) robot impreso con una IMU por eslabón; (c) conexionado al ESP32.")
    ax.figura(IE.FOTOS / "interfaz_teleop.png",
              "Interfaz de teleoperación: marcadores ArUco reconocidos, θ crudo (naranja) vs Kalman (azul), "
              "gráficas de 6 s, robot y parámetros (captura de la sesión 01, red doméstica, 4,8 cuadros/s).")
    tp = d["teleop"]
    if tp is not None and len(tp):
        ruido = Rp.RAIZ / "datos" / "teleop" / "ruido_camara.json"
        if ruido.exists():
            sig = json.loads(ruido.read_text(encoding="utf-8"))["sigma_deg"]
            ax.p(f"R de la cámara medida con el brazo quieto: σ = {f(sig[0], 2)}° (θ1) y {f(sig[1], 2)}° (θ2). "
                 "Protocolo de cada sesión (≈ 30 s): movimiento lento, rápido y dos oclusiones de la muñeca; crudo y "
                 "Kalman se calculan siempre sobre los mismos cuadros.")
        filas = []
        for _, r in tp.iterrows():
            filas.append([r["sesion"], r["robot_movido_con"], f(r["duracion_s"], 0), f(r["fps"], 1),
                          f(r["visto_pct"], 0), f"{f(r['aspereza_theta1_crudo'], 2)} / {f(r['aspereza_theta1_kf'], 2)}",
                          f"{f(r['aspereza_theta2_crudo'], 2)} / {f(r['aspereza_theta2_kf'], 2)}",
                          f(r["retraso_kf_theta1_ms"], 0), f(r["t_kalman_us_medio"], 0), f(r["t_proc_ms_medio"], 1)])
        ax.tabla(["Sesión", "Robot movido con", "Duración [s]", "fps", "3 marcadores [%]",
                  "Aspereza θ1 crudo / KF [°]", "Aspereza θ2 crudo / KF [°]", "Retraso KF [ms]",
                  "Kalman [µs/cuadro]", "Detección + KF [ms]"], filas,
                 "Teleoperación real: crudo frente a Kalman en los mismos cuadros (sesiones 03 = crudo y 04 = "
                 "Kalman son las del protocolo).")
        con = tp[tp["retraso_orden_robot_hombro_ms"].notna()]
        if len(con):
            ax.tabla(["Sesión", "Orden → robot hombro [ms]", "Orden → robot codo [ms]", "Cámara → robot hombro [ms]",
                      "Cámara → robot codo [ms]", "IMU del robot válida [%]"],
                     [[r["sesion"], f(r["retraso_orden_robot_hombro_ms"], 0), f(r["retraso_orden_robot_codo_ms"], 0),
                       f(r["retraso_camara_robot_hombro_ms"], 0), f(r["retraso_camara_robot_codo_ms"], 0),
                       f(r.get("imu_robot_valida_pct", 100), 0)] for _, r in con.iterrows()],
                     "Latencia medida con el giroscopio del propio robot (estabilidad del lazo de teleoperación).")
        lat = d["latencia"]
        if lat:
            ax.p(f"**Latencia del lector de video** (DroidCam simulado, {lat['trabajo_por_cuadro_ms']} ms de proceso por "
                 f"cuadro): con cv2.VideoCapture la edad del cuadro crecía de {f(lat['opencv_edad_inicio_ms'], 0)} a "
                 f"{f(lat['opencv_edad_final_ms'], 0)} ms; con el lector sin búfer se mantiene en "
                 f"{f(lat['lector_edad_final_ms'], 0)} ms.")
        if "imu_robot_falla_t_s" in tp and tp["imu_robot_falla_t_s"].notna().any():
            caidas = tp[tp["imu_robot_falla_t_s"].notna()]
            ax.p("**Falla de sensor declarada:** la IMU del hombro del robot dejó de responder ("
                 + ", ".join(f"{r['sesion']} desde {f(r['imu_robot_falla_t_s'], 1)} s" for _, r in caidas.iterrows())
                 + "; giro = 0,000 exacto). Esas muestras se descartan por código (analisis_teleop.primera_falla_imu); "
                 "por eso la sesión 04 no tiene métricas del robot. Las métricas de la cámara no dependen de esa IMU.")
        kk = tp[tp["robot_movido_con"] == "kalman"].iloc[-1]
        ax.figura(d["teleop_dir"] / f"20_teleop_{kk['sesion']}.png",
                  f"{kk['sesion']} (robot movido con Kalman): ángulos crudos (puntos) y Kalman (línea), órdenes al "
                  "servo; en gris, cuadros sin los tres marcadores (θ2 predicho).")
        if len(con):
            rr = con.iloc[-1]
            ax.figura(d["teleop_dir"] / f"21_robot_{rr['sesion']}.png",
                      f"{rr['sesion']}: orden enviada frente al movimiento del robot medido con sus IMU.")

    # ---------------------------------------------------------------- A.5 (E9)
    ax.titulo("A.5 Comprobación individual (E9): preguntas y dónde se sustenta cada respuesta", 3)
    ax.tabla(["Criterio", "Pregunta del instrumento", "Dónde está la respuesta"],
             [["C1", "Vector de estado, una etapa de predicción o actualización; papel de H y de las mediciones.",
               "A.1 (ecuaciones A1–A6); python/kalman.py, python/modelo_kalman.py"],
              ["C2", "Reproducir o identificar una Q; cómo se controlaron las condiciones de comparación y se validó "
                     "la teleoperación.", "A.2 (tablas de Q y ajuste/validación), A.4 (sesiones 03 y 04)"],
              ["C3", "Interpretar una métrica y justificar la Q final; distinguir suavizado de precisión; límite de "
                     "una conclusión.", "A.2 (regla ≤ 40 ms), A.3 (comparación y límites)"]],
             "Preguntas de comprobación individual (la respuesta observada la registra el docente en la sección 6).",
             [1.6, 9, 6.5])
    return ax


# ====================================================================== principal
def generar(a):
    commit = Rp.commit_actual()
    doc = Document(PLANTILLA)
    identificacion(doc, a, commit)
    registro_y_localizadores(doc)
    ax = anexo(doc, cargar_datos())
    nombre = f"INSTRUMENTO_PDS_KALMAN_ENTREGA_2_Equipo{a.equipo or 'XX'}_v2.0.docx"
    salida = CARPETA / nombre
    doc.save(salida)
    return salida, ax


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--equipo", default=None, help="número del equipo, p. ej. 07")
    ap.add_argument("--integrantes", nargs="+", default=None, help='"Nombre Apellido (código)" …')
    ap.add_argument("--entrega", default=None, help="persona designada para entregar")
    ap.add_argument("--fecha", default=None, help="fecha de entrega")
    ap.add_argument("--sin-pdf", action="store_true")
    a = ap.parse_args()
    salida, ax = generar(a)
    print(f"Instrumento: {salida.relative_to(Rp.RAIZ)} (Anexo A: {ax.n_tab} tablas, {ax.n_fig} figuras, "
          f"{ax.n_eq} ecuaciones)")
    if not a.sin_pdf:
        pdf = IE.a_pdf(salida)
        print(f"PDF: {pdf.relative_to(Rp.RAIZ)}" if pdf else "PDF: ábrelo en Word y usa Guardar como PDF.")


if __name__ == "__main__":
    main()
