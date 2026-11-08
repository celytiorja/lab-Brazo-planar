"""Pantalla de la teleoperación: video + panel de estado con gráficas EN VIVO.

    ┌──────────── video (640×480) ────────────┬──── panel (300×480) ────┐
    │ marcadores enmarcados, brazo en amarillo │ cámara: fps, tiempos    │
    │ REC 12.3 s  + guía de la grabación       │ marcadores H C M        │
    │                                          │ θ crudo vs Kalman       │
    │                                          │ gráfica θ1 (6 s)        │
    │                                          │ gráfica θ2 (6 s)        │
    │ mensaje temporal                         │ robot, Kalman, teclas   │
    └──────────────────────────────────────────┴─────────────────────────┘

Las gráficas son la "visualización comparativa" de la E8: puntos naranjas = lo que mide
la cámara (crudo), línea azul = Kalman, franjas grises = cuadros sin los 3 marcadores.

Rápido: lo que no cambia (títulos, marcos, teclas) se dibuja UNA vez en una imagen base;
en cada cuadro solo se copia esa base y se dibuja lo que cambió (~1 ms).
Sin tildes en los textos: OpenCV 4 no las dibuja.
"""
import time
from collections import deque

import cv2
import numpy as np

import config_camara as CC

ANCHO_PANEL = 300
FUENTE = cv2.FONT_HERSHEY_SIMPLEX
AA = cv2.LINE_AA
VENTANA_GRAFICA_S = 6.0

# Colores (BGR)
FONDO = (32, 30, 28)
TITULO = (110, 70, 25)
BLANCO = (235, 235, 235)
GRIS = (150, 150, 150)
GRIS_OSCURO = (70, 68, 66)
VERDE = (90, 200, 90)
AMARILLO = (40, 200, 240)
ROJO = (70, 70, 235)
NARANJA = (40, 150, 255)          # crudo
AZUL = (255, 170, 40)             # Kalman
COLOR_MARCADOR = {"hombro": (255, 120, 0), "codo": (0, 200, 0), "muneca": (0, 0, 255)}
LETRA = {"hombro": "H", "codo": "C", "muneca": "M"}

# Posiciones (y) de cada bloque del panel
Y_CAMARA, Y_MARCAS, Y_ANG = 46, 70, 96
GRAF1 = (12, 162, ANCHO_PANEL - 24, 62)       # x, y, ancho, alto
GRAF2 = (12, 250, ANCHO_PANEL - 24, 62)
Y_ROBOT, Y_KALMAN, Y_TECLAS = 340, 390, 436


def texto(img, s, org, escala=0.45, color=BLANCO, grosor=1):
    cv2.putText(img, s, org, FUENTE, escala, color, grosor, AA)


def texto_con_fondo(img, s, org, escala=0.5, color=BLANCO, fondo=(0, 0, 0)):
    (an, al), base = cv2.getTextSize(s, FUENTE, escala, 1)
    x, y = org
    cv2.rectangle(img, (x - 4, y - al - 4), (x + an + 4, y + base + 2), fondo, -1)
    texto(img, s, org, escala, color)


class Panel:
    def __init__(self, alto=480):
        self.alto = alto
        self.historia = deque(maxlen=600)       # (t, crudo1, crudo2, kf1, kf2, visto)
        self._rango = {0: [60.0, 120.0], 1: [-30.0, 30.0]}
        self._msg, self._t_msg = "", 0.0
        self.base = self._dibujar_base()

    # ------------------------------------------------------------ mensajes
    def mensaje(self, s, duracion_s=4.0):
        """Mensaje temporal abajo del video (se borra solo)."""
        self._msg, self._t_msg = s, time.perf_counter() + duracion_s

    def agregar(self, t, proc):
        c, k = proc.theta_crudo, proc.theta_kf
        self.historia.append((t,
                              c[0] if (c is not None and proc.visto) else np.nan,
                              c[1] if (c is not None and proc.visto) else np.nan,
                              k[0] if k is not None else np.nan,
                              k[1] if k is not None else np.nan,
                              proc.visto))

    # ------------------------------------------------------------ parte fija
    def _dibujar_base(self):
        p = np.full((self.alto, ANCHO_PANEL, 3), FONDO, np.uint8)
        cv2.rectangle(p, (0, 0), (ANCHO_PANEL, 26), TITULO, -1)
        texto(p, "TELEOPERACION  -  brazo 2 GDL", (10, 18), 0.5, BLANCO)
        texto(p, "ANGULOS [deg]", (12, Y_ANG), 0.42, GRIS)
        texto(p, "crudo", (150, Y_ANG), 0.42, NARANJA)
        texto(p, "Kalman", (220, Y_ANG), 0.42, AZUL)
        for (x, y, w, h), nombre in ((GRAF1, "t1 hombro"), (GRAF2, "t2 codo")):
            cv2.rectangle(p, (x, y), (x + w, y + h), GRIS_OSCURO, 1)
            texto(p, nombre, (x, y - 5), 0.4, GRIS)
            texto(p, f"ultimos {VENTANA_GRAFICA_S:.0f} s", (x + w - 78, y - 5), 0.35, GRIS)
        cv2.line(p, (10, Y_ROBOT - 18), (ANCHO_PANEL - 10, Y_ROBOT - 18), GRIS_OSCURO, 1)
        cv2.line(p, (10, Y_TECLAS - 16), (ANCHO_PANEL - 10, Y_TECLAS - 16), GRIS_OSCURO, 1)
        return p

    # ------------------------------------------------------------ cada cuadro
    def dibujar(self, video, proc, estado):
        """Devuelve la imagen completa (video con anotaciones + panel)."""
        self._anotar_video(video, proc, estado)
        p = self.base.copy()
        self._bloque_camara(p, proc, estado)
        self._bloque_angulos(p, proc)
        self._grafica(p, GRAF1, 0)
        self._grafica(p, GRAF2, 1)
        self._bloque_robot(p, proc, estado)
        self._bloque_kalman(p, proc)
        self._bloque_teclas(p, proc)
        return np.hstack([video, p])

    def _anotar_video(self, img, proc, estado):
        det = proc.detector
        if det.modo == "aruco":
            if estado.get("diagnostico") and len(det.rechazados):
                # Cuadros que "parecen" marcador pero no se leen: pequeños, borrosos,
                # doblados o sin margen blanco.
                cv2.polylines(img, [np.int32(c).reshape(-1, 1, 2) for c in det.rechazados],
                              True, ROJO, 1, AA)
            for n, c in det.esquinas.items():
                cv2.polylines(img, [np.int32(c).reshape(-1, 1, 2)], True, COLOR_MARCADOR[n], 2, AA)
        pts = []
        for n in CC.MARCADORES:
            q = proc.pos.get(n)
            if q is None:
                continue
            q = (int(q[0]), int(q[1]))
            pts.append(q)
            memoria = n == "hombro" and proc.hombro_recordado
            cv2.circle(img, q, 6, COLOR_MARCADOR[n], 1 if memoria else -1, AA)
        if len(pts) >= 2 and proc.pos.get("hombro") is not None and proc.pos.get("codo") is not None:
            cv2.polylines(img, [np.array(pts)], False, AMARILLO, 2, AA)
        # Grabación: banda roja arriba con el tiempo y qué hacer
        if estado.get("sesion") is not None:
            dur, guia, nombre = estado["sesion"]
            cv2.rectangle(img, (0, 0), (img.shape[1], 28), (40, 40, 200), -1)
            cv2.circle(img, (14, 14), 6, BLANCO, -1, AA)
            texto(img, f"REC {nombre}  {dur:4.1f} s   {guia}", (26, 19), 0.5, BLANCO)
        # Midiendo R: barra de progreso
        if proc.midiendo_ruido:
            frac = proc.progreso_ruido
            y = img.shape[0] - 46
            cv2.rectangle(img, (10, y), (img.shape[1] - 10, y + 14), (60, 60, 60), -1)
            cv2.rectangle(img, (10, y), (10 + int((img.shape[1] - 20) * frac), y + 14), AMARILLO, -1)
            texto(img, "Midiendo R de la camara: brazo QUIETO", (14, y - 6), 0.5, AMARILLO)
        if self._msg and time.perf_counter() < self._t_msg:
            texto_con_fondo(img, self._msg, (10, img.shape[0] - 14), 0.52)
        elif estado.get("pista"):
            texto_con_fondo(img, estado["pista"], (10, img.shape[0] - 14), 0.5, AMARILLO)

    def _bloque_camara(self, p, proc, estado):
        fps = estado.get("fps", 0.0)
        color = VERDE if fps >= 20 else (AMARILLO if fps >= 10 else ROJO)
        texto(p, f"{fps:4.1f} fps", (12, Y_CAMARA), 0.5, color)
        texto(p, f"proceso {proc.t_proc_ms:4.1f} ms   KF {proc.t_calc_us:4.0f} us",
              (100, Y_CAMARA), 0.42, GRIS)
        x = 12
        for n in CC.MARCADORES:
            visto = proc.pos.get(n) is not None
            dudoso = (n == "hombro" and proc.hombro_recordado) or n in getattr(proc.detector, "seguidos", ())
            c = (AMARILLO if dudoso else VERDE) if visto else ROJO
            cv2.circle(p, (x + 6, Y_MARCAS - 5), 6, c, -1, AA)
            texto(p, LETRA[n], (x + 16, Y_MARCAS), 0.45, BLANCO)
            x += 40
        if proc.visto:
            s, c = "VISTO", VERDE
        elif proc.solo_theta1:
            s, c = "SOLO t1 (t2 predicho)", AMARILLO
        else:
            s, c = "NO VISTO: Kalman predice", ROJO
        texto(p, s, (132, Y_MARCAS), 0.42, c)

    def _bloque_angulos(self, p, proc):
        for j, nombre in enumerate(("t1", "t2")):
            y = Y_ANG + 20 + 18 * j
            texto(p, nombre, (12, y), 0.45, BLANCO)
            texto(p, _num(proc.theta_crudo, j), (150, y), 0.5, NARANJA)
            texto(p, _num(proc.theta_kf, j), (220, y), 0.5, AZUL)

    def _grafica(self, p, caja, j):
        x0, y0, w, h = caja
        if not self.historia:
            return
        datos = np.array(self.historia, dtype=float)
        t_fin = datos[-1, 0]
        datos = datos[datos[:, 0] >= t_fin - VENTANA_GRAFICA_S]
        crudo, kf, visto = datos[:, 1 + j], datos[:, 3 + j], datos[:, 5] > 0.5
        lo, hi = self._escala(j, np.concatenate([crudo, kf]))
        xs = (x0 + (datos[:, 0] - (t_fin - VENTANA_GRAFICA_S)) / VENTANA_GRAFICA_S * w).astype(int)

        def a_y(v):
            return (y0 + h - (v - lo) / (hi - lo) * h).astype(int)
        # Franjas grises: sin los 3 marcadores
        sin_ver = np.flatnonzero(~visto)
        for k in sin_ver:
            cv2.line(p, (xs[k], y0 + 1), (xs[k], y0 + h - 1), GRIS_OSCURO, 2)
        # Primero los puntos crudos y ENCIMA la línea de Kalman (así se ven las dos).
        okc = np.isfinite(crudo)
        for xx, yy in zip(xs[okc], a_y(crudo[okc])):
            p[max(yy - 1, y0):min(yy + 2, y0 + h), max(xx - 1, x0):min(xx + 2, x0 + w)] = NARANJA
        ok = np.isfinite(kf)
        if ok.sum() > 1:
            cv2.polylines(p, [np.column_stack([xs[ok], a_y(kf[ok])]).reshape(-1, 1, 2)],
                          False, AZUL, 1, AA)
        texto(p, f"{hi:.0f}", (x0 + 3, y0 + 12), 0.33, GRIS)
        texto(p, f"{lo:.0f}", (x0 + 3, y0 + h - 4), 0.33, GRIS)

    def _escala(self, j, v):
        """Escala vertical estable: crece si los datos se salen, se achica despacio."""
        v = v[np.isfinite(v)]
        lo, hi = self._rango[j]
        if len(v):
            dmin, dmax = float(v.min()), float(v.max())
            centro = (dmin + dmax) / 2
            mitad = max(10.0, (dmax - dmin) / 2 * 1.25)
            if dmin < lo or dmax > hi or (hi - lo) > 4 * mitad:
                lo, hi = centro - mitad, centro + mitad
                self._rango[j] = [lo, hi]
        return lo, hi

    def _bloque_robot(self, p, proc, estado):
        robot = estado.get("robot")
        texto(p, "ROBOT", (12, Y_ROBOT), 0.42, GRIS)
        if robot is None:
            texto(p, "sin robot  (--puerto COMx)", (70, Y_ROBOT), 0.45, GRIS)
            return
        s, c = robot.estado()
        texto(p, s, (70, Y_ROBOT), 0.45, c)
        if estado.get("enviando"):
            texto(p, f"mueve: {proc.fuente.upper()}", (12, Y_ROBOT + 20), 0.45,
                  AZUL if proc.fuente == "kalman" else NARANJA)
        else:
            texto(p, "PAUSA  (R para enviar)", (12, Y_ROBOT + 20), 0.45, AMARILLO)
        if robot.ultimo_cmd is not None:
            texto(p, f"servo h={robot.ultimo_cmd[0]:3d} c={robot.ultimo_cmd[1]:3d}",
                  (170, Y_ROBOT + 20), 0.4, GRIS)

    def _bloque_kalman(self, p, proc):
        cfg = proc.config
        texto(p, f"KALMAN  {cfg['nombre']}  f_n = {cfg['f_n_hz']:g} Hz", (12, Y_KALMAN), 0.42, BLANCO)
        sig = np.sqrt(proc.r_camara)
        medido = proc.origen_r.startswith("medido")
        texto(p, f"R: sigma = {sig[0]:.2f} / {sig[1]:.2f} deg  " + ("(medida)" if medido else "(falta N)"),
              (12, Y_KALMAN + 19), 0.4, VERDE if medido else AMARILLO)

    def _bloque_teclas(self, p, proc):
        extra = "L colores" if proc.detector.modo == "color" else "D diagnostico"
        texto(p, "C pose   N medir R   R robot   F fuente", (12, Y_TECLAS), 0.4, GRIS)
        texto(p, f"G grabar   1/2/3 Q   M espejo   {extra}", (12, Y_TECLAS + 18), 0.4, GRIS)
        texto(p, "Q / Esc salir", (12, Y_TECLAS + 36), 0.4, GRIS)


def _num(v, j):
    return "  --" if v is None else f"{v[j]:6.1f}"
