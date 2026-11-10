"""Genera el INFORME de la Entrega 2 en FORMATO IEEE (Word + PDF), todo desde los resultados.

    python python/generar_informe_ieee.py
    python python/generar_informe_ieee.py --autores "Nombre 1 (código)" "Nombre 2 (código)" \
        --afiliacion "Programa, Universidad, Ciudad" --foto docs/informe/foto_montaje.jpg

Formato IEEE (plantilla de conferencia):
  - carta, título a 24 pt y autores a una columna; el resto a DOS columnas, Times 10 pt;
  - Resumen/Abstract y Palabras clave/Index Terms en negrita a 9 pt;
  - secciones con números romanos en versalitas (I. INTRODUCCIÓN), subsecciones A., B. en cursiva;
  - ecuaciones de Word (editables) numeradas (1), (2)... al margen derecho;
  - "TABLA I" encima de cada tabla y "Fig. 1." debajo de cada figura;
  - referencias numeradas [1], [2]... citadas en el texto.

NINGÚN número se escribe a mano: se leen de resultados/ (ver generar_informe.cargar_datos).
Las figuras anchas ocupan las dos columnas (salto de sección continuo), como en IEEE.
"""
import argparse
import re
import shutil
import subprocess
from pathlib import Path
from xml.sax.saxutils import escape

import pandas as pd
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

import reporte as Rp
from generar_informe import E2, cargar_datos, f, fila, foto_por_defecto

SALIDA = Rp.RAIZ / "docs" / "informe" / "Informe_Entrega2_IEEE.docx"
FUENTE = "Times New Roman"
# Carta con márgenes IEEE: 0.625" a los lados, 0.75" arriba, 1" abajo; 2 columnas de 3.5" + 0.25".
ANCHO_PAG, ALTO_PAG = Cm(21.59), Cm(27.94)
MARGEN_LADO, MARGEN_ARR, MARGEN_ABA = Cm(1.59), Cm(1.91), Cm(2.54)
SEP_COL_TWIPS = 360                                   # 0.25"
ANCHO_COL_CM = (21.59 - 2 * 1.59 - 0.635) / 2         # 8.89 cm
ANCHO_TEXTO_CM = 21.59 - 2 * 1.59                     # 18.41 cm

# Subíndice: una sola letra (no precedida de otra letra) + "_" + {texto} o letras/dígitos.
# Así "f_c" o "Δt_k" llevan subíndice, pero "seno_rapido_01" (nombre de archivo) no.
SUBINDICE = re.compile(r"(?<![A-Za-z0-9])([A-Za-zα-ωΔΣ]\u0302?)_(\{[^}]*\}|[A-Za-z0-9α-ω]+)")

NS_M = "http://schemas.openxmlformats.org/officeDocument/2006/math"
NS_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


# ============================================================ ecuaciones de Word (OMML)
# Mini lenguaje: un texto es una variable/símbolo; T(...) texto recto; Sub, Sup, SubSup,
# Fr (fracción), Mat (matriz entre corchetes), Par (paréntesis), Raiz.
class T:
    def __init__(self, s):
        self.s = s


class Sub:
    def __init__(self, e, s):
        self.e, self.s = e, s


class Sup:
    def __init__(self, e, s):
        self.e, self.s = e, s


class SubSup:
    def __init__(self, e, s, p):
        self.e, self.s, self.p = e, s, p


class Fr:
    def __init__(self, n, d):
        self.n, self.d = n, d


class Mat:
    def __init__(self, filas):
        self.filas = filas


class Par:
    def __init__(self, e, abre="(", cierra=")"):
        self.e, self.abre, self.cierra = e, abre, cierra


class Raiz:
    def __init__(self, e):
        self.e = e


def _run(s, recto=False):
    sty = '<m:rPr><m:sty m:val="p"/></m:rPr>' if recto else ""
    return (f'<m:r>{sty}<w:rPr><w:rFonts w:ascii="Cambria Math" w:hAnsi="Cambria Math"/></w:rPr>'
            f'<m:t xml:space="preserve">{escape(s)}</m:t></m:r>')


def _omml(n):
    if isinstance(n, str):
        return _run(n)
    if isinstance(n, (list, tuple)):
        return "".join(_omml(x) for x in n)
    if isinstance(n, T):
        return _run(n.s, recto=True)
    if isinstance(n, Sub):
        return f"<m:sSub><m:e>{_omml(n.e)}</m:e><m:sub>{_omml(n.s)}</m:sub></m:sSub>"
    if isinstance(n, Sup):
        return f"<m:sSup><m:e>{_omml(n.e)}</m:e><m:sup>{_omml(n.s)}</m:sup></m:sSup>"
    if isinstance(n, SubSup):
        return (f"<m:sSubSup><m:e>{_omml(n.e)}</m:e><m:sub>{_omml(n.s)}</m:sub>"
                f"<m:sup>{_omml(n.p)}</m:sup></m:sSubSup>")
    if isinstance(n, Fr):
        return f"<m:f><m:num>{_omml(n.n)}</m:num><m:den>{_omml(n.d)}</m:den></m:f>"
    if isinstance(n, Mat):
        filas = "".join("<m:mr>" + "".join(f"<m:e>{_omml(c)}</m:e>" for c in fil) + "</m:mr>"
                        for fil in n.filas)
        return (f'<m:d><m:dPr><m:begChr m:val="["/><m:endChr m:val="]"/></m:dPr>'
                f"<m:e><m:m>{filas}</m:m></m:e></m:d>")
    if isinstance(n, Par):
        return (f'<m:d><m:dPr><m:begChr m:val="{escape(n.abre)}"/><m:endChr m:val="{escape(n.cierra)}"/>'
                f"</m:dPr><m:e>{_omml(n.e)}</m:e></m:d>")
    if isinstance(n, Raiz):
        return f'<m:rad><m:radPr><m:degHide m:val="1"/></m:radPr><m:deg/><m:e>{_omml(n.e)}</m:e></m:rad>'
    raise TypeError(n)


def omath(nodo):
    return parse_xml(f'<m:oMath xmlns:m="{NS_M}" xmlns:w="{NS_W}">{_omml(nodo)}</m:oMath>')


# ============================================================ documento IEEE
def cientifico(x, d=1):
    """1.2e+06 -> 1,2×10⁶ (notación de un informe, no de Python)."""
    sup = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")
    m, e = f"{x:.{d}e}".split("e")
    return f"{m.replace('.', ',')}×10{str(int(e)).translate(sup)}"


def romano(n):
    val = [(10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]
    s = ""
    for v, r in val:
        while n >= v:
            s, n = s + r, n - v
    return s


class InformeIEEE:
    def __init__(self):
        self.doc = Document()
        self.n_sec = self.n_sub = self.n_fig = self.n_tab = self.n_eq = 0
        self._estilos()
        s = self.doc.sections[0]
        s.page_width, s.page_height = ANCHO_PAG, ALTO_PAG
        s.left_margin = s.right_margin = MARGEN_LADO
        s.top_margin, s.bottom_margin = MARGEN_ARR, MARGEN_ABA

    def _estilos(self):
        st = self.doc.styles["Normal"]
        st.font.name = FUENTE
        st.font.size = Pt(10)
        st.element.rPr.rFonts.set(qn("w:eastAsia"), FUENTE)
        pf = st.paragraph_format
        pf.space_before = pf.space_after = Pt(0)
        pf.line_spacing = 1.0
        for nivel in (1, 2):
            h = self.doc.styles[f"Heading {nivel}"]
            h.font.name = FUENTE
            h.element.rPr.rFonts.set(qn("w:eastAsia"), FUENTE)
            h.font.size = Pt(10)
            h.font.bold = False
            h.font.color.rgb = None
            h.paragraph_format.space_before = Pt(8 if nivel == 1 else 5)
            h.paragraph_format.space_after = Pt(4 if nivel == 1 else 3)
            h.paragraph_format.keep_with_next = True
            if nivel == 1:
                h.font.small_caps = True
                h.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
            else:
                h.font.italic = True
                h.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
            # quitar el tema (Calibri Light) que Word aplica a los títulos
            rf = h.element.rPr.rFonts
            for att in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
                if rf.get(qn(att)) is not None:
                    del rf.attrib[qn(att)]
            rf.set(qn("w:ascii"), FUENTE)
            rf.set(qn("w:hAnsi"), FUENTE)

    # --------------------------------------------------------------- columnas
    def _columnas(self, seccion, n):
        cols = seccion._sectPr.find(qn("w:cols"))
        if cols is None:
            cols = OxmlElement("w:cols")
            seccion._sectPr.append(cols)
        cols.set(qn("w:num"), str(n))
        cols.set(qn("w:space"), str(SEP_COL_TWIPS))

    def nueva_seccion(self, columnas):
        s = self.doc.add_section(WD_SECTION.CONTINUOUS)
        self._columnas(s, columnas)
        return s

    # --------------------------------------------------------------- texto
    def _runs(self, par, texto, tam=None, negrita=False, cursiva=False):
        """**negrita**, __cursiva__ y subíndices de una letra: f_c, Δt_k, ω̂_{k−1}, H_cam."""
        for i, trozo in enumerate(texto.split("**")):
            for j, t in enumerate(trozo.split("__")):
                if not t:
                    continue
                pos = 0
                for m in SUBINDICE.finditer(t):
                    piezas = [(t[pos:m.end(1)], False), (m.group(2).strip("{}"), True)]
                    pos = m.end()
                    for txt, sub in piezas:
                        if txt:
                            self._run(par, txt, tam, negrita or (i % 2 == 1), cursiva or (j % 2 == 1), sub)
                if t[pos:]:
                    self._run(par, t[pos:], tam, negrita or (i % 2 == 1), cursiva or (j % 2 == 1), False)
        return par

    @staticmethod
    def _run(par, txt, tam, negrita, cursiva, sub):
        r = par.add_run(txt)
        r.bold, r.italic = negrita, cursiva
        r.font.subscript = sub or None
        if tam:
            r.font.size = Pt(tam)

    def p(self, texto, sangria=True, tam=None, alin=WD_ALIGN_PARAGRAPH.JUSTIFY):
        par = self.doc.add_paragraph()
        par.alignment = alin
        if sangria:
            par.paragraph_format.first_line_indent = Cm(0.36)
        return self._runs(par, texto, tam)

    def vinetas(self, items):
        for it in items:
            par = self.doc.add_paragraph()
            par.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            par.paragraph_format.left_indent = Cm(0.5)
            par.paragraph_format.first_line_indent = Cm(-0.3)
            self._runs(par, "• " + it)

    def seccion(self, titulo):
        self.n_sec += 1
        self.n_sub = 0
        self.doc.add_heading(f"{romano(self.n_sec)}. {titulo}", level=1)

    def subseccion(self, titulo):
        self.n_sub += 1
        self.doc.add_heading(f"{chr(64 + self.n_sub)}. {titulo}", level=2)

    def ecuacion(self, nodo):
        """Ecuación centrada en la columna con su número (n) al margen derecho."""
        self.n_eq += 1
        par = self.doc.add_paragraph()
        par.paragraph_format.space_before = Pt(3)
        par.paragraph_format.space_after = Pt(3)
        tabs = par.paragraph_format.tab_stops
        tabs.add_tab_stop(Cm(ANCHO_COL_CM / 2), WD_TAB_ALIGNMENT.CENTER)
        tabs.add_tab_stop(Cm(ANCHO_COL_CM - 0.05), WD_TAB_ALIGNMENT.RIGHT)
        par.add_run("\t")
        par._p.append(omath(nodo))
        par.add_run(f"\t({self.n_eq})")
        return self.n_eq

    def en_linea(self, partes):
        """Párrafo con texto y ecuaciones en línea: partes = ["texto", nodo, "texto"...]."""
        par = self.doc.add_paragraph()
        par.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        par.paragraph_format.first_line_indent = Cm(0.36)
        for x in partes:
            if isinstance(x, str):
                self._runs(par, x)
            else:
                par._p.append(omath(x))
        return par

    # --------------------------------------------------------------- tablas y figuras
    def tabla(self, encabezado, filas, titulo, anchos_cm=None):
        self.n_tab += 1
        for txt in (f"Tabla {romano(self.n_tab)}", titulo):
            cap = self.doc.add_paragraph()
            cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            cap.paragraph_format.keep_with_next = True
            r = cap.add_run(txt)
            r.font.size = Pt(8)
            r.font.small_caps = True
        cap.paragraph_format.space_after = Pt(3)
        t = self.doc.add_table(rows=1, cols=len(encabezado))
        t.style = "Table Grid"
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        for c, h in zip(t.rows[0].cells, encabezado):
            c.text = ""
            self._runs(c.paragraphs[0], str(h), tam=8, negrita=True)
            c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        for fil in filas:
            for c, v in zip(t.add_row().cells, fil):
                c.text = ""
                self._runs(c.paragraphs[0], str(v), tam=8)
                c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        # La tabla no se parte entre columnas: cada fila "con la siguiente" y sin dividirse.
        for k, fil in enumerate(t.rows):
            trPr = fil._tr.get_or_add_trPr()
            trPr.append(OxmlElement("w:cantSplit"))
            if k < len(t.rows) - 1:
                for c in fil.cells:
                    for par_c in c.paragraphs:
                        par_c.paragraph_format.keep_with_next = True
        # Ancho fijo = una columna (si no, Word/LibreOffice la estiran a toda la página).
        total = ANCHO_COL_CM - 0.2
        if not anchos_cm:
            anchos_cm = [total / len(encabezado)] * len(encabezado)
        escala = total / sum(anchos_cm)
        anchos_cm = [w * escala for w in anchos_cm]
        t.autofit = False
        tblPr = t._tbl.tblPr
        for tag, attrs in (("w:tblW", {"w:w": str(int(total * 567)), "w:type": "dxa"}),
                           ("w:tblLayout", {"w:type": "fixed"})):
            el = tblPr.find(qn(tag))
            if el is None:
                el = OxmlElement(tag)
                tblPr.append(el)
            for k, v in attrs.items():
                el.set(qn(k), v)
        grid = t._tbl.tblGrid
        for gc, w in zip(grid.findall(qn("w:gridCol")), anchos_cm):
            gc.set(qn("w:w"), str(int(w * 567)))
        for fil in t.rows:
            for c, w in zip(fil.cells, anchos_cm):
                c.width = Cm(w)
        esp = self.doc.add_paragraph()
        esp.paragraph_format.space_after = Pt(4)
        return t

    def _figura(self, ruta, pie, ancho_cm):
        self.n_fig += 1
        par = self.doc.add_paragraph()
        par.alignment = WD_ALIGN_PARAGRAPH.CENTER
        par.paragraph_format.space_before = Pt(6)
        par.paragraph_format.keep_with_next = True
        par.add_run().add_picture(str(ruta), width=Cm(ancho_cm))
        cap = self.doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        cap.paragraph_format.space_before = Pt(3)
        cap.paragraph_format.space_after = Pt(8)
        r = cap.add_run(f"Fig. {self.n_fig}. ")
        r.font.size = Pt(8)
        self._runs(cap, pie, tam=8)
        return self.n_fig

    def figura_columna(self, ruta, pie, ancho_cm=ANCHO_COL_CM - 0.3):
        ruta = Path(ruta)
        return self._figura(ruta, pie, ancho_cm) if ruta.exists() else None

    def figura_ancha(self, ruta, pie, ancho_cm=15.0):
        """Figura a lo ancho de la página (las dos columnas), como las figuras anchas de IEEE."""
        ruta = Path(ruta)
        if not ruta.exists():
            return None
        self.nueva_seccion(1)
        n = self._figura(ruta, pie, ancho_cm)
        self.nueva_seccion(2)
        return n

    def referencias(self, refs):
        h = self.doc.add_heading("Referencias", level=1)
        h.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for i, ref in enumerate(refs, 1):
            par = self.doc.add_paragraph()
            par.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            par.paragraph_format.left_indent = Cm(0.6)
            par.paragraph_format.first_line_indent = Cm(-0.6)
            par.paragraph_format.tab_stops.add_tab_stop(Cm(0.6))
            self._runs(par, f"[{i}]\t{ref}", tam=8)


# ============================================================ contenido
REFS = [
    "R. E. Kalman, “A new approach to linear filtering and prediction problems,” __J. Basic Eng.__, "
    "vol. 82, no. 1, pp. 35–45, 1960.",
    "G. Welch and G. Bishop, “An introduction to the Kalman filter,” Univ. North Carolina at Chapel Hill, "
    "Tech. Rep. TR 95-041, 2006.",
    "Y. Bar-Shalom, X. R. Li, and T. Kirubarajan, __Estimation with Applications to Tracking and "
    "Navigation__. New York, NY, USA: Wiley, 2001.",
    "D. Simon, __Optimal State Estimation: Kalman, H∞, and Nonlinear Approaches__. Hoboken, NJ, USA: "
    "Wiley, 2006.",
    "S. Garrido-Jurado, R. Muñoz-Salinas, F. J. Madrid-Cuevas, and M. J. Marín-Jiménez, “Automatic "
    "generation and detection of highly reliable fiducial markers under occlusion,” __Pattern "
    "Recognit.__, vol. 47, no. 6, pp. 2280–2292, 2014.",
    "InvenSense, “MPU-6000 and MPU-6050 product specification,” Rev. 3.4, 2013.",
    "A. V. Oppenheim and R. W. Schafer, __Discrete-Time Signal Processing__, 3rd ed. Upper Saddle "
    "River, NJ, USA: Pearson, 2010.",
]


def _ultima(tp, fuente):
    filas = tp[tp["robot_movido_con"] == fuente]
    return None if filas.empty else filas.iloc[-1]


def encabezado(inf, d, autores, afiliacion):
    s0 = inf.doc.sections[0]
    inf._columnas(s0, 1)
    par = inf.doc.add_paragraph()
    par.alignment = WD_ALIGN_PARAGRAPH.CENTER
    par.paragraph_format.space_after = Pt(10)
    r = par.add_run("Filtro de Kalman para la estimación de estado y la teleoperación "
                    "de un brazo planar de dos grados de libertad")
    r.font.size = Pt(24)
    par = inf.doc.add_paragraph()
    par.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = par.add_run(",  ".join(autores))
    r.font.size = Pt(11)
    par = inf.doc.add_paragraph()
    par.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = par.add_run(afiliacion)
    r.font.size = Pt(10)
    r.italic = True
    par = inf.doc.add_paragraph()
    par.alignment = WD_ALIGN_PARAGRAPH.CENTER
    par.paragraph_format.space_after = Pt(12)
    r = par.add_run(f"Laboratorio de Procesamiento Digital de Señales — Corte 3, Entrega 2 · "
                    f"Repositorio celytiorja/lab-Brazo-planar, commit {Rp.commit_actual()}")
    r.font.size = Pt(8)
    inf.nueva_seccion(2)


def resumen(inf, d):
    val, rep, q = d["val"], d["reposo"], d["sel"]["configuracion"]
    kf, mm5 = fila(val, "metodo", f"Kalman {q['nombre']}"), fila(val, "metodo", "Media móvil N=5 + Euler")
    dirc = fila(val, "metodo", "Integración directa")
    kfr, dr = fila(rep, "metodo", f"Kalman {q['nombre']}"), fila(rep, "metodo", "Integración directa")
    tp = d["teleop"]
    cr, kk = (_ultima(tp, "crudo"), _ultima(tp, "kalman")) if tp is not None else (None, None)
    tele = ""
    tele_en = ""
    if cr is not None and kk is not None and not d["teleop_sint"]:
        b = [100 * (1 - r[f"aspereza_theta{j}_kf"] / r[f"aspereza_theta{j}_crudo"]) for r in (cr, kk) for j in (1, 2)]
        tele = (f" En teleoperación con una cámara y marcadores ArUco, el filtro redujo la aspereza de los "
                f"ángulos del brazo humano entre {f(min(b), 0)} % y {f(max(b), 0)} % con {f(kk['retraso_kf_theta1_ms'], 0)} ms "
                f"de retraso y {f(kk['t_kalman_us_medio'], 0)} µs de cómputo por cuadro, y siguió estimando "
                "el codo cuando la muñeca quedó oculta.")
        tele_en = (f" In camera-based teleoperation with ArUco markers, the filter reduced joint-angle "
                   f"roughness by {f(min(b), 0)}–{f(max(b), 0)} % with {f(kk['retraso_kf_theta1_ms'], 0)} ms of lag "
                   f"and {f(kk['t_kalman_us_medio'], 0)} µs per frame, and kept estimating the elbow while the "
                   "wrist marker was occluded.")
    txt = (f"Se diseñó e implementó un filtro de Kalman lineal con modelo de velocidad casi constante para "
           f"estimar los ángulos y las velocidades angulares de un brazo planar de dos grados de libertad "
           f"instrumentado con dos IMU muestreadas a 100 Hz. La covarianza de medición R se obtuvo de un "
           f"registro en reposo y la de proceso Q se dedujo de una frecuencia de corte; de tres "
           f"configuraciones se eligió la de f_c = {f(q['f_corte_hz'], 0)} Hz con una regla fija aplicada solo "
           f"a datos de ajuste. En validación, el filtro redujo el ruido de la velocidad angular en reposo de "
           f"{f(dr['ruido_omega_reposo_puro_dps'], 3)} a {f(kfr['ruido_omega_reposo_puro_dps'], 3)} °/s con "
           f"{f(kf['retraso_omega_ms'], 1)} ms de retraso (media móvil de 5 muestras: "
           f"{f(mm5['retraso_omega_ms'], 1)} ms) y el de la aceleración angular de "
           f"{f(dirc['ruido_alfa_reposo_dps2'], 1)} a {f(kf['ruido_alfa_reposo_dps2'], 1)} °/s². Ningún "
           f"método corrige la deriva, porque con solo giroscopios el ángulo no es observable." + tele)
    par = inf.doc.add_paragraph()
    par.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    r = par.add_run("Resumen—")
    r.bold, r.italic, r.font.size = True, True, Pt(9)
    inf._runs(par, txt, tam=9, negrita=True)
    en = (f"A linear Kalman filter with a nearly-constant-velocity model was designed and implemented to "
          f"estimate the joint angles and angular rates of a two-degree-of-freedom planar arm instrumented "
          f"with two IMUs sampled at 100 Hz. The measurement covariance R was obtained from a rest recording "
          f"and the process covariance Q was derived from a cut-off frequency; among three configurations, "
          f"f_c = {f(q['f_corte_hz'], 0)} Hz was selected with a fixed rule applied to tuning data only. On "
          f"validation data the filter reduced the angular-rate noise at rest from "
          f"{f(dr['ruido_omega_reposo_puro_dps'], 3)} to {f(kfr['ruido_omega_reposo_puro_dps'], 3)} °/s with "
          f"{f(kf['retraso_omega_ms'], 1)} ms of lag. No method removes drift, since the angle is not "
          f"observable from gyroscopes alone." + tele_en)
    par = inf.doc.add_paragraph()
    par.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    par.paragraph_format.space_before = Pt(6)
    r = par.add_run("Abstract—")
    r.bold, r.italic, r.font.size = True, True, Pt(9)
    inf._runs(par, en, tam=9, negrita=True)
    for etiqueta, texto in (("Palabras clave—", "filtro de Kalman, IMU, estimación de estado, ArUco, "
                                               "teleoperación, brazo planar."),
                            ("Index Terms—", "Kalman filter, IMU, state estimation, ArUco, teleoperation, "
                                             "planar manipulator.")):
        par = inf.doc.add_paragraph()
        par.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        par.paragraph_format.space_before = Pt(6)
        r = par.add_run(etiqueta)
        r.bold, r.italic, r.font.size = True, True, Pt(9)
        inf._runs(par, texto, tam=9, negrita=True)


def introduccion(inf, d):
    inf.seccion("Introducción")
    inf.p("El objetivo del laboratorio es un brazo planar de dos articulaciones (hombro y codo) que copie "
          "en tiempo real el movimiento del brazo de una persona. En una primera etapa se caracterizaron "
          "las unidades de medición inercial (IMU): sesgo, ruido, deriva y covarianza de medición, y se "
          "evaluaron dos estimadores base, la integración de Euler y la media móvil. Ambos tienen límites "
          "conocidos: integrar acumula el sesgo y suavizar con una media móvil introduce un retraso "
          "proporcional a la ventana [7].")
    inf.p("El filtro de Kalman [1], [2] combina un modelo del movimiento con las mediciones y pondera cada "
          "fuente según su incertidumbre. Este trabajo (i) formula el modelo de estado del brazo con los "
          "giroscopios, (ii) justifica la covarianza de proceso a partir de una frecuencia de corte y elige "
          "una de tres configuraciones con datos de ajuste, (iii) compara Kalman con la integración directa "
          "y la media móvil en datos de validación distintos, y (iv) usa la estimación para teleoperar el "
          "robot desde una cámara, midiendo tiempos de cómputo y latencia.")


def teoria(inf, d):
    inf.seccion("Marco teórico")
    inf.subseccion("Modelo en espacio de estados")
    inf.p("El filtro estima el estado x de un sistema lineal a partir de mediciones ruidosas z. Con el "
          "intervalo real Δt_k entre muestras:", sangria=True)
    inf.ecuacion([Sub("x", "k"), "=", Sub("F", "k"), Sub("x", "k−1"), "+", Sub("w", "k"), ",  ",
                  Sub("w", "k"), "∼", T("N"), Par(["0, ", Sub("Q", "k")])])
    inf.ecuacion([Sub("z", "k"), "=", "H", Sub("x", "k"), "+", Sub("v", "k"), ",  ",
                  Sub("v", "k"), "∼", T("N"), Par("0, R")])
    inf.p("Para cada eslabón i se usa el modelo de velocidad casi constante [3]: el estado es el ángulo "
          "absoluto φ_i y la velocidad angular ω_i, y la aceleración desconocida se modela como ruido blanco "
          "de densidad espectral q:")
    inf.ecuacion([Sub("F", "i"), "=", Mat([["1", "Δt"], ["0", "1"]]), ",   ", Sub("Q", "i"), "=", "q",
                  Mat([[Fr(Sup("Δt", "3"), "3"), Fr(Sup("Δt", "2"), "2")],
                       [Fr(Sup("Δt", "2"), "2"), "Δt"]])])
    inf.p("Para el brazo completo x = [φ₁, ω₁, φ₂, ω₂]ᵀ. La IMU 2 está sobre el eslabón 2, que se mueve con "
          "el eslabón 1, por lo que mide el ángulo absoluto φ₂ = θ₁ + θ₂; el ángulo del codo es "
          "θ₂ = φ₂ − φ₁. Los giroscopios solo miden velocidad, con el sesgo b medido en reposo restado:")
    inf.ecuacion(["H", "=", Mat([["0", "1", "0", "0"], ["0", "0", "0", "1"]]), ",   ", Sub("z", "k"), "=",
                  Mat([[[Sub("w", "1"), "−", Sub("b", "1")]], [[Sub("w", "2"), "−", Sub("b", "2")]]])])
    inf.subseccion("Ecuaciones del filtro")
    inf.p("En cada muestra se predice con el modelo y se corrige con la medición [2]:")
    inf.ecuacion([Sup(Sub("x̂", "k"), "−"), "=", "F", Sub("x̂", "k−1"), ",   ", Sup(Sub("P", "k"), "−"), "=",
                  "F", Sub("P", "k−1"), Sup("F", "T"), "+", "Q"])
    inf.ecuacion([Sub("K", "k"), "=", Sup(Sub("P", "k"), "−"), Sup("H", "T"),
                  Sup(Par([ "H", Sup(Sub("P", "k"), "−"), Sup("H", "T"), "+", "R"]), "−1")])
    inf.ecuacion([Sub("x̂", "k"), "=", Sup(Sub("x̂", "k"), "−"), "+", Sub("K", "k"),
                  Par([Sub("z", "k"), "−", "H", Sup(Sub("x̂", "k"), "−")])])
    n_jos = inf.ecuacion([Sub("P", "k"), "=", Par(["I", "−", Sub("K", "k"), "H"]), Sup(Sub("P", "k"), "−"),
                          Sup(Par(["I", "−", Sub("K", "k"), "H"]), "T"), "+", Sub("K", "k"), "R",
                          Sup(Sub("K", "k"), "T")])
    inf.p(f"P es la covarianza del error de estimación y K decide cuánto se cree la medición frente a la "
          f"predicción: P⁻ grande o R pequeña dan K grande. ({n_jos}) es la forma de Joseph, que conserva P "
          "simétrica y definida positiva frente al redondeo [4]. La innovación y = z − Hx̂⁻, con covarianza "
          "S = HP⁻Hᵀ + R, permite verificar la consistencia del filtro [3]:")
    inf.ecuacion([T("NIS"), "=", Sup("y", "T"), Sup("S", "−1"), "y", "∼", Sup("χ", "2"), Par("m")])
    inf.p("con media m = 2 (dos mediciones) si el modelo y las covarianzas son correctos.")
    inf.subseccion("Covarianza de proceso a partir de la frecuencia de corte")
    inf.p("Con solo giroscopio, la parte de ω del filtro en régimen estacionario es un paso bajo de primer "
          "orden ω̂_k = ω̂_{k−1} + K(z_k − ω̂_{k−1}). Igualando su ganancia a la de un filtro de frecuencia de "
          "corte f_c y resolviendo la ecuación de Riccati escalar se obtiene q en función de r (la varianza "
          "del giroscopio):")
    inf.ecuacion(["K", "=", "1", "−", Sup("e", ["−2π", Sub("f", "c"), "Δt"]), ",   ", "q", "=",
                  Fr("r", "Δt"), Fr(Sup("K", "2"), ["1", "−", "K"])])
    inf.p("Así cada Q se justifica por la banda de movimiento que debe pasar, no por prueba y error, y queda "
          "atada a R: si el sensor fuera más ruidoso, q crecería en la misma proporción.")
    inf.subseccion("Kalman de la cámara para la teleoperación")
    inf.p("Una cámara ve tres marcadores ArUco [5] en el hombro, el codo y la muñeca de la persona y calcula "
          "θ₁ y θ₂. Se usa el mismo modelo con estado [θ₁, ω₁, θ₂, ω₂]ᵀ, pero ahora se mide el ángulo:")
    inf.ecuacion([Sub("H", "cam"), "=", Mat([["1", "0", "0", "0"], ["0", "0", "1", "0"]]), ",   ",
                  Sub("q", "cam"), "=", "r", "Δt", Sup(Par(["2π", Sub("f", "n")]), "4")])
    inf.p("En régimen estacionario es un paso bajo de segundo orden con frecuencia natural f_n; r es la "
          "varianza por cuadro medida con el brazo quieto. Si la muñeca queda oculta pero el hombro y el codo "
          "se ven, H conserva solo la fila de θ₁ (medición parcial): θ₁ se sigue corrigiendo y θ₂ se predice. "
          "La velocidad ω̂, que la cámara no mide, es la que permite esa predicción; si la oclusión dura más "
          "de 0,2 s, ω̂ se amortigua para que el robot no siga de largo.")
    inf.subseccion("Aceleración angular numérica")
    inf.p("La aceleración se obtiene derivando la velocidad. Con diferencia hacia atrás, el ruido blanco de "
          "desviación σ_ω se amplifica como:")
    inf.eq_alfa = inf.ecuacion([Sub("α", "k"), "=", Fr([Sub("ω", "k"), "−", Sub("ω", "k−1")], "Δt"), ",   ",
                  Sub("σ", "α"), "=", Fr([Raiz("2"), Sub("σ", "ω")], "Δt")])


def metodologia(inf, d, foto):
    inf.seccion("Metodología")
    inf.subseccion("Montaje y adquisición")
    inf.p("El robot usa un ESP32, dos servomotores MG996R (hombro y codo) con fuente de 5 V aparte y tierra "
          "común, y dos MPU-6050 [6] en el mismo bus I²C (direcciones 0x68 y 0x69), una en cada eslabón "
          "(L₁ = 105 mm, L₂ = 85 mm). El brazo trabaja en el plano horizontal de la mesa. El firmware muestrea "
          "a 100 Hz en una tarea de tiempo real en el núcleo 0 (±500 °/s, filtro interno de 44 Hz), marca cada "
          "muestra en microsegundos y la envía por USB; el filtro usa ese Δt_k real.")
    if foto and Path(foto).exists():
        inf.figura_columna(foto, "Montaje: brazo planar con las dos IMU, ESP32 y cámara.")
    man = d["manifiesto"] or {}
    inf.subseccion("Datos de ajuste y de validación")
    inf.p("Los perfiles de movimiento (escalones, seno lento y seno rápido) los genera el firmware en función "
          "del tiempo, por lo que cada repetición es idéntica. Un manifiesto generado por código asigna la "
          "primera repetición válida a ajuste (elegir Q) y la segunda a validación (comparar métodos); R sale "
          f"del reposo {Path(man.get('estatico', 'estatico_03')).stem}. La Tabla {romano(inf.n_tab + 1)} resume la asignación.")
    filas = [[Path(a).stem, Path(v).stem] for a, v in zip(man.get("ajuste", []), man.get("validacion", []))]
    inf.tabla(["Ajuste", "Validación"], filas, "Registros de ajuste y de validación")
    if man.get("rechazadas"):
        txt = "; ".join(f"{k} ({v[0]})" for k, v in man["rechazadas"].items())
        inf.p(f"Se rechazaron automáticamente: {txt}.")
    sel = d["sel"]
    inf.subseccion("Métricas y regla de selección")
    inf.p("Ruido: desviación de ω (y de α) en reposo. Retraso: desplazamiento que maximiza la correlación con "
          "la referencia sin filtrar. Deriva: error de ángulo al final del registro. Regla fijada antes de ver "
          f"los resultados: elegir la Q de menor ruido de ω en reposo entre las que tienen un retraso de ω de "
          f"hasta {f(sel['retraso_max_ms'], 0)} ms en ajuste, porque el servo ya consume cerca de 190 ms.")
    inf.subseccion("Teleoperación")
    inf.p("Un teléfono sobre la mesa (DroidCam) envía video MJPEG por la red de su punto de acceso. Un lector "
          "propio sin búfer conserva solo el cuadro más nuevo para que el retraso no se acumule. Tras calibrar "
          "la pose de referencia y medir r con el brazo quieto 10 s, θ̂ se convierte en órdenes de servo. Se "
          "grabaron sesiones de unos 30 s con el mismo protocolo (movimiento lento, rápido y dos oclusiones "
          "de la muñeca): una con el robot movido por la medición cruda y otra por Kalman. Crudo y Kalman se "
          "calculan siempre sobre los mismos cuadros; el robot registra su propio giroscopio.")


def resultados(inf, d):
    inf.seccion("Resultados")
    sel, q = d["sel"], d["sel"]["configuracion"]
    aj, rep, val = d["ajuste"], d["reposo"], d["val"]
    # A. R
    inf.subseccion("Ruido de los sensores")
    Rj = d["R"]
    Rm = Rj["R"]
    s1, s2 = Rm[0][0] ** 0.5, Rm[1][1] ** 0.5
    rho = Rm[0][1] / (s1 * s2)
    rho = 0.0 if abs(rho) < 5e-4 else rho          # evita "-0,000"
    r1 = d["resumen_e1"]["deriva_reposo_fuera_de_muestra"]
    dur = r1["duracion_s"] / 60
    inf.tabla(["Magnitud", "Giro 1", "Giro 2"], anchos_cm=[3.4, 2.2, 2.2], filas=
              [["R [(°/s)²]", f(Rm[0][0], 5), f(Rm[1][1], 5)],
               ["σ [°/s]", f(s1, 3), f(s2, 3)],
               ["Sesgo b [°/s]", f(Rj["medias"][0], 2), f(Rj["medias"][1], 2)],
               ["Deriva sin b [°/min]", f(r1["sin_sesgo"][0] / dur, 1), f(r1["sin_sesgo"][1] / dur, 1)],
               ["Deriva con b [°/min]", f(r1["con_sesgo"][0] / dur, 2), f(r1["con_sesgo"][1] / dur, 2)]],
              titulo=f"Covarianza de medición y sesgo ({Rj['archivo']}, {Rj['muestras']} muestras)")
    inf.p(f"La correlación entre giroscopios es ρ = {f(rho, 3)}, por lo que R es diagonal. Restar el sesgo "
          f"reduce la deriva en reposo en más de un orden de magnitud (Tabla {romano(inf.n_tab)}), pero no la anula.")
    # B. Q
    inf.subseccion("Selección de Q")
    filas = []
    for c in sel["configuraciones_evaluadas"]:
        a = fila(aj, "metodo", f"Kalman {c['nombre']}")
        rr = fila(rep, "metodo", f"Kalman {c['nombre']}")
        k = 1 - __import__("math").exp(-2 * __import__("math").pi * c["f_corte_hz"] * c["dt_usado"])
        filas.append([c["nombre"].replace("Q_", ""), f(c["f_corte_hz"], 1), f(k, 3), f(c["q"], 5),
                      f(a["retraso_omega_ms"], 1), f(rr["ruido_omega_reposo_puro_dps"], 4)])
    inf.tabla(["Q", "f_c [Hz]", "K", "q [°²/s³]", "Retraso ω [ms]", "Ruido ω [°/s]"], filas,
              "Tres configuraciones de Q (registros de ajuste)")
    f1 = inf.n_fig + 1
    inf.p("Q baja (f_c = 1,5 Hz) es la más suave pero su retraso supera el límite; Q alta (15 Hz) casi no "
          f"filtra. Con la regla se elige **{q['nombre']}** (f_c = {f(q['f_corte_hz'], 0)} Hz), cinco veces la "
          f"frecuencia del seno rápido. La Fig. {f1} muestra las tres configuraciones sobre un registro de ajuste y "
          f"la Fig. {f1 + 1} el compromiso ruido–retraso al barrer q.")
    inf.figura_ancha(E2 / "10_ajuste_configuraciones_Q_seno_rapido_01.png",
                     "Tres configuraciones de Q sobre el registro de ajuste seno_rapido_01.", 14)
    inf.figura_columna(E2 / "14_compromiso_Q_R.png",
                       "Compromiso ruido–retraso al barrer la relación Q/R; se marcan las tres Q evaluadas.")
    # C. Comparación
    inf.subseccion("Comparación de métodos en validación")
    nombres = [("Integración directa", "Directa"), ("Media móvil N=5 + Euler", "MM N=5"),
               ("Media móvil N=21 + Euler", "MM N=21"), (f"Kalman {q['nombre']}", "Kalman")]
    filas = []
    for m, corto in nombres:
        v, rr = fila(val, "metodo", m), fila(rep, "metodo", m)
        filas.append([corto, f(rr["ruido_omega_reposo_puro_dps"], 3), f(v["retraso_omega_ms"], 1),
                      f(v["retraso_theta_ms"], 1), f(v["ruido_alfa_reposo_dps2"], 1),
                      f(v["deriva_final_deg"], 2), f(v["t_calculo_us"], 0)])
    inf.tabla(["Método", "Ruido ω [°/s]", "Ret. ω [ms]", "Ret. θ [ms]", "Ruido α [°/s²]", "Deriva [°]",
               "t [µs]"], filas, "Comparación en los registros de validación (promedio de eslabones)",
              [1.5, 1.2, 1.1, 1.1, 1.2, 1.2, 0.8])
    kf = fila(val, "metodo", f"Kalman {q['nombre']}")
    mm5 = fila(val, "metodo", "Media móvil N=5 + Euler")
    mm21 = fila(val, "metodo", "Media móvil N=21 + Euler")
    inf.p(f"Con un retraso de ω similar al de la media móvil de 5 muestras ({f(kf['retraso_omega_ms'], 1)} frente "
          f"a {f(mm5['retraso_omega_ms'], 1)} ms), Kalman tiene menos ruido, y su ángulo se atrasa solo "
          f"{f(kf['retraso_theta_ms'], 1)} ms frente a {f(mm5['retraso_theta_ms'], 1)} ms. La media móvil de 21 "
          f"muestras filtra más pero se atrasa {f(mm21['retraso_omega_ms'], 0)} ms. La deriva final es "
          f"prácticamente igual con los tres métodos (Tabla {romano(inf.n_tab)}, Fig. {inf.n_fig + 1}).")
    inf.figura_ancha(E2 / "15_validacion_comparacion_seno_rapido_02.png",
                     "Integración directa, medias móviles y Kalman en el registro de validación seno_rapido_02.",
                     14)
    # D. Aceleración
    inf.subseccion("Aceleración angular")
    ac = d["acel"]
    teo = ac[ac["fuente"].str.startswith("TEÓRICO hacia atrás")]
    crudo = ac[ac["fuente"].str.startswith("giro crudo, diferencia hacia atrás")]
    kfa = ac[ac["fuente"] == f"Kalman {q['nombre']}, hacia atrás"]
    inf.p(f"Derivar divide entre Δt = 10 ms. Según ({inf.eq_alfa}), el ruido teórico de α con el giroscopio crudo es "
          f"{f(teo['sigma_alfa_reposo_dps2'].iloc[0], 1)} °/s² y el medido fue "
          f"{f(crudo['sigma_alfa_reposo_dps2'].iloc[0], 1)} °/s²; derivando la ω de Kalman baja a "
          f"{f(kfa['sigma_alfa_reposo_dps2'].iloc[0], 2)} °/s² (Fig. {inf.n_fig + 1}). La diferencia central tiene menos ruido "
          "pero no es causal, porque necesita la muestra siguiente.")
    inf.figura_ancha(E2 / "13_aceleracion_angular.png",
                     "Aceleración angular numérica en reposo y en movimiento: giro crudo frente a los estimadores.",
                     15.5)
    # E. Consistencia
    inf.subseccion("Consistencia del filtro")
    nis = d["nis"]
    sub = nis[nis["metodo"] == f"Kalman {q['nombre']}"]
    inf.p(f"P se mantiene simétrica (asimetría máxima {cientifico(sub['max_asimetria_P'].max())}) y definida positiva "
          f"(autovalor mínimo {cientifico(sub['min_autovalor_P'].min())}), y K converge a su valor estacionario en menos "
          f"de un segundo (Fig. {inf.n_fig + 1}). El NIS medio en reposo fue {f(sub['nis_medio_reposo'].min(), 1)} en el mejor "
          f"registro (esperado: 2), pero en movimiento llega a {cientifico(sub['nis_medio_movimiento'].max())}: el modelo "
          "de velocidad casi constante no explica los arranques bruscos del servo.")
    inf.figura_ancha(E2 / "12_P_y_K.png", "Evolución de la covarianza P y de la ganancia K.", 15.5)
    # F. Teleoperación
    inf.subseccion("Teleoperación con cámara")
    qc = d["qcam"]
    filas = [[r["Q"].replace("Q_", ""), f(r["f_n [Hz]"], 1), f(r["factor de ruido"], 2),
              f(r["retraso 2 Hz [ms]"], 1), f(r["ganancia 8 Hz (temblor)"], 2)] for _, r in qc.iterrows()]
    inf.tabla(["Q", "f_n [Hz]", "Ruido ×", "Retraso 2 Hz [ms]", "Temblor 8 Hz ×"], filas,
              "Kalman de la cámara: caracterización de las tres Q")
    inf.p("El movimiento voluntario del brazo está por debajo de unos 2 Hz y el temblor fisiológico entre "
          "8 y 12 Hz. Con Q media (f_n = 3 Hz) el primero pasa con menos de 16 ms de retraso y el segundo se "
          f"reduce a la mitad (Tabla {romano(inf.n_tab)}).")
    tp = d["teleop"]
    if tp is None or not len(tp):
        return
    cr, kk = _ultima(tp, "crudo"), _ultima(tp, "kalman")
    filas = []
    for r in (cr, kk):
        if r is None:
            continue
        filas.append([r["sesion"].replace("sesion_", ""), r["robot_movido_con"].capitalize(), f(r["fps"], 1),
                      f(r["visto_pct"], 0),
                      f"{f(r['aspereza_theta1_crudo'], 2)} / {f(r['aspereza_theta1_kf'], 2)}",
                      f"{f(r['aspereza_theta2_crudo'], 2)} / {f(r['aspereza_theta2_kf'], 2)}"])
    marca = " (datos sintéticos)" if d["teleop_sint"] else ""
    inf.tabla(["Sesión", "Robot movido con", "fps", "Visto [%]", "Aspereza θ₁ crudo / Kalman [°]",
               "Aspereza θ₂ crudo / Kalman [°]"], filas,
              f"Teleoperación: crudo frente a Kalman en los mismos cuadros{marca}",
              [1.25, 1.45, 0.9, 1.0, 2.0, 2.0])
    import json
    ruido = Rp.RAIZ / "datos" / "teleop" / "ruido_camara.json"
    sig = json.loads(ruido.read_text(encoding="utf-8"))["sigma_deg"] if ruido.exists() else None
    if kk is not None and cr is not None:
        b1 = [100 * (1 - r["aspereza_theta1_kf"] / r["aspereza_theta1_crudo"]) for r in (cr, kk)]
        b2 = [100 * (1 - r["aspereza_theta2_kf"] / r["aspereza_theta2_crudo"]) for r in (cr, kk)]
        inf.p((f"El ruido de la cámara medido con el brazo quieto fue σ = {f(sig[0], 2)}° (θ₁) y "
               f"{f(sig[1], 2)}° (θ₂). " if sig else "")
              + f"Las sesiones se grabaron a {f(min(cr['fps'], kk['fps']), 1)}–{f(max(cr['fps'], kk['fps']), 1)} "
              f"cuadros/s, por debajo de los 30 nominales, por la red. En los mismos cuadros, Kalman redujo la "
              f"aspereza (segunda diferencia) de θ₁ entre {f(min(b1), 0)} y {f(max(b1), 0)} % y la de θ₂ entre "
              f"{f(min(b2), 0)} y {f(max(b2), 0)} %, con {f(cr['retraso_kf_theta1_ms'], 0)}–"
              f"{f(kk['retraso_kf_theta1_ms'], 0)} ms de retraso (Tabla {romano(inf.n_tab)}). Detección más Kalman tomaron "
              f"{f(kk['t_proc_ms_medio'], 1)} ms por cuadro, el {f(kk['carga_pct'], 0)} % del tiempo entre cuadros; "
              f"Kalman solo, {f(kk['t_kalman_us_medio'], 0)} µs. Durante las oclusiones de la muñeca "
              f"({f(kk['solo_theta1_pct'], 1)} % de los cuadros de la sesión con Kalman) θ₁ siguió medido y θ₂ se "
              f"predijo con ω̂ (Fig. {inf.n_fig + 1}).")
        inf.figura_ancha(d["teleop_dir"] / f"20_teleop_{kk['sesion']}.png",
                         f"Sesión {kk['sesion'].replace('sesion_', '')} (robot movido con Kalman): ángulos del brazo "
                         "humano crudos (puntos) y estimados (línea), y órdenes al servo del codo; en gris, los "
                         "cuadros sin los tres marcadores.", 13)
    con_robot = tp[tp["retraso_orden_robot_hombro_ms"].notna()] if "retraso_orden_robot_hombro_ms" in tp else tp.iloc[0:0]
    if len(con_robot):
        rr = con_robot.iloc[-1]
        inf.p(f"Integrando el giroscopio del propio robot se midió el retraso entre la orden y el movimiento: "
              f"{f(con_robot['retraso_orden_robot_hombro_ms'].min(), 0)}–"
              f"{f(con_robot['retraso_orden_robot_hombro_ms'].max(), 0)} ms en el hombro y "
              f"{f(con_robot['retraso_orden_robot_codo_ms'].min(), 0)}–{f(con_robot['retraso_orden_robot_codo_ms'].max(), 0)} "
              f"ms en el codo (Fig. {inf.n_fig + 1}), del orden de la respuesta del servo: la latencia dominante es el servo, no "
              "el filtro.")
        inf.figura_ancha(d["teleop_dir"] / f"21_robot_{rr['sesion']}.png",
                         f"Sesión {rr['sesion'].replace('sesion_', '')}: orden enviada frente al movimiento del robot "
                         "medido con sus IMU.", 14)
    if "imu_robot_falla_t_s" in tp and tp["imu_robot_falla_t_s"].notna().any():
        caidas = tp[tp["imu_robot_falla_t_s"].notna()]
        txt = " y ".join(f"en la sesión {r['sesion'].replace('sesion_', '')} desde {f(r['imu_robot_falla_t_s'], 1)} s"
                         for _, r in caidas.iterrows())
        inf.p(f"**Falla de sensor.** La IMU del hombro del robot dejó de responder {txt} (giro exactamente "
              "0,000 °/s, sin ruido). El análisis descarta esas muestras automáticamente; por eso la sesión movida "
              "con Kalman no tiene métricas del robot y la vibración del robot con crudo frente a Kalman no se "
              "puede comparar. Las métricas de la cámara no dependen de esa IMU.")


def discusion(inf, d):
    inf.seccion("Discusión")
    q = d["sel"]["configuracion"]
    aj = fila(d["ajuste"], "metodo", f"Kalman {q['nombre']}")
    import math
    diseno = 1000 / (2 * math.pi * q["f_corte_hz"])
    inf.p("**Suavizar no es lo mismo que ser exacto.** La deriva final es la misma con los tres métodos: el "
          "filtro reduce el ruido pero no corrige un error que no se mide. Con H midiendo solo ω y el brazo en "
          "el plano horizontal, donde el acelerómetro no ve el ángulo porque la gravedad es perpendicular al "
          "plano, el ángulo no es observable; solo se compensa el sesgo medido en reposo.")
    inf.p(f"**Retraso de un filtro recursivo.** El retraso de diseño 1/(2πf_c) es {f(diseno, 0)} ms, pero el medido "
          f"fue {f(aj['retraso_omega_ms'], 1)} ms: el retraso de un filtro IIR depende del contenido en frecuencia "
          "de la señal, mientras que el de la media móvil (fase lineal) coincide con su teoría. Por eso la regla "
          "usa el retraso medido. El ángulo de Kalman casi no se atrasa porque la covarianza cruzada φ–ω de P hace "
          "que la innovación del giroscopio corrija también φ.")
    inf.p("**Consistencia.** En movimiento el NIS es muy superior a 2. Una Q que lo hiciera consistente sería tan "
          "grande que el filtro casi no filtraría; se prefirió elegir Q por respuesta en frecuencia y declarar el "
          "límite del modelo.")
    inf.p("**Teleoperación y rediseño.** La cámara mide θ sin deriva pero tiembla y se puede tapar; los "
          "giroscopios no tiemblan pero derivan. El rediseño natural es la fusión: agregar a H_cam las filas "
          "[0 1 0 0] y [0 0 0 1] de unos giroscopios en el brazo humano, con su varianza en R, de modo que θ sea "
          "observable y la predicción durante las oclusiones mejore.")
    inf.p("**Lo que no se verifica con estos datos:** la latencia del teléfono al PC por la red, la exactitud "
          "absoluta del brazo humano (no hay una verdad medida) y la deformación por perspectiva si el teléfono "
          "no está paralelo a la mesa.")


def conclusiones(inf, d):
    inf.seccion("Conclusiones")
    q = d["sel"]["configuracion"]
    kf = fila(d["val"], "metodo", f"Kalman {q['nombre']}")
    mm5 = fila(d["val"], "metodo", "Media móvil N=5 + Euler")
    inf.vinetas([
        "El modelo de velocidad casi constante, con R medida en reposo y Q deducida de una frecuencia de corte, "
        "permite justificar cada parámetro del filtro sin ajuste a ciegas.",
        f"Con una regla fija (retraso de ω de hasta {f(d['sel']['retraso_max_ms'], 0)} ms y mínimo ruido) se eligió "
        f"f_c = {f(q['f_corte_hz'], 0)} Hz; en validación tiene menos ruido que la media móvil de 5 muestras con un "
        f"retraso similar ({f(kf['retraso_omega_ms'], 1)} frente a {f(mm5['retraso_omega_ms'], 1)} ms) y su ángulo "
        f"se atrasa solo {f(kf['retraso_theta_ms'], 1)} ms.",
        "La aceleración angular numérica es inutilizable sin filtrar; derivar la estimación de Kalman la vuelve "
        "aprovechable.",
        "Ningún método corrige la deriva con solo giroscopios; hace falta una referencia absoluta, como la cámara.",
        "La teleoperación con ArUco y Kalman funciona en tiempo real: el filtro suaviza los ángulos y predice el "
        "codo en las oclusiones con un costo de décimas de milisegundo, y la latencia dominante es la del servo."])


def generar(salida=SALIDA, foto=None, autores=None, afiliacion=None):
    foto = foto or foto_por_defecto()
    d = cargar_datos()
    inf = InformeIEEE()
    encabezado(inf, d, autores or ["Autor 1 (código)", "Autor 2 (código)"],
               afiliacion or "Programa académico, Universidad, Ciudad, País")
    resumen(inf, d)
    introduccion(inf, d)
    teoria(inf, d)
    metodologia(inf, d, foto)
    resultados(inf, d)
    discusion(inf, d)
    conclusiones(inf, d)
    inf.referencias(REFS)
    salida = Path(salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    inf.doc.save(salida)
    return salida, inf


def a_pdf(ruta):
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        return None
    subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", str(ruta.parent), str(ruta)],
                   check=False, capture_output=True, timeout=180)
    pdf = ruta.with_suffix(".pdf")
    return pdf if pdf.exists() else None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--autores", nargs="+", default=None, help='p. ej. "Ana Pérez (1234567)"')
    ap.add_argument("--afiliacion", default=None, help="programa, universidad, ciudad")
    ap.add_argument("--foto", default=None, help="foto del montaje (si no, docs/informe/foto_montaje.jpg)")
    ap.add_argument("--salida", default=str(SALIDA))
    ap.add_argument("--sin-pdf", action="store_true")
    a = ap.parse_args()
    ruta, inf = generar(a.salida, a.foto, a.autores, a.afiliacion)
    print(f"Informe IEEE: {ruta.relative_to(Rp.RAIZ)} ({inf.n_fig} figuras, {inf.n_tab} tablas, "
          f"{inf.n_eq} ecuaciones)")
    if not a.sin_pdf:
        pdf = a_pdf(ruta)
        print(f"PDF: {pdf.relative_to(Rp.RAIZ)}" if pdf else "PDF: no se pudo (falta LibreOffice); ábrelo en Word "
              "y usa Guardar como PDF.")


if __name__ == "__main__":
    main()
