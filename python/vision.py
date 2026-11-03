"""Seguimiento de 3 marcadores (hombro, codo, muñeca) y cálculo de los ángulos del brazo.

Hay DOS formas de encontrar los marcadores (config_camara.MODO_DETECCION):

A) "aruco" (RECOMENDADA): cuadros impresos en blanco y negro, como un QR pequeñito.
   1. Se pasa la imagen a grises y se umbraliza de forma ADAPTATIVA (cada zona con su
      propio umbral): funciona con luz fuerte, débil o desigual.
   2. Se buscan contornos de 4 lados (cuadriláteros) con borde negro.
   3. Se "endereza" cada cuadrilátero y se leen sus 4×4 casillas blanco/negro: eso es un
      número (el ID). El diccionario tiene bits de sobra para CORREGIR errores, así que
      una mancha, la piel o la madera nunca se confunden con un marcador.
   4. El centro del marcador = promedio de sus 4 esquinas (precisión de sub-píxel).
   Por qué es más robusto que el color: el contraste blanco/negro existe con cualquier
   luz (el color "azul claro" se vuelve gris con poca luz o blanco con mucha), y el ID
   dice CUÁL marcador es sin depender de dónde estaba antes.

B) "color" (respaldo): marcadores de papel de color, aprendidos con un clic.
  1. Pasar la imagen de RGB a HSV: H = tono (el "color"), S = saturación, V = brillo.
     El tono cambia poco con la iluminación; por eso se segmenta por H.
  2. Umbral: quedarse con los píxeles cuyo H, S, V están cerca del color aprendido.
  3. Limpiar la máscara (apertura morfológica: borra puntitos sueltos).
  4. Buscar la mancha más grande cerca de donde estaba el marcador antes.
  5. Su centro (centroide) es la posición del marcador.
"""
import math

import cv2
import numpy as np

import config_camara as CC


class Marcador:
    def __init__(self, nombre):
        self.nombre = nombre
        self.hsv = None          # color aprendido (H, S, V)
        self.pos = None          # última posición vista (x, y) en píxeles

    @property
    def calibrado(self):
        return self.hsv is not None

    def aprender(self, imagen_bgr, x, y):
        """Aprende el color promediando un cuadrito de 7×7 píxeles alrededor del clic."""
        hsv = cv2.cvtColor(imagen_bgr, cv2.COLOR_BGR2HSV)
        r = 3
        trozo = hsv[max(0, y - r):y + r + 1, max(0, x - r):x + r + 1].reshape(-1, 3)
        self.hsv = np.median(trozo, axis=0).astype(int)
        self.pos = (x, y)

    def mascara(self, hsv):
        h, s, v = (int(c) for c in self.hsv)
        bajo_s, alto_s = max(CC.SAT_MIN, s - CC.TOL_SAT), min(255, s + CC.TOL_SAT)
        bajo_v, alto_v = max(30, v - CC.TOL_VAL), min(255, v + CC.TOL_VAL)
        # El tono es CIRCULAR (0 y 179 son ambos rojo): puede haber que unir dos rangos.
        rangos = [(h - CC.TOL_TONO, h + CC.TOL_TONO)]
        if rangos[0][0] < 0:
            rangos = [(0, rangos[0][1]), (180 + rangos[0][0], 179)]
        elif rangos[0][1] > 179:
            rangos = [(rangos[0][0], 179), (0, rangos[0][1] - 180)]
        m = None
        for lo, hi in rangos:
            parte = cv2.inRange(hsv, (lo, bajo_s, bajo_v), (hi, alto_s, alto_v))
            m = parte if m is None else cv2.bitwise_or(m, parte)
        nucleo = np.ones((3, 3), np.uint8)
        return cv2.morphologyEx(m, cv2.MORPH_OPEN, nucleo)

    def buscar(self, hsv):
        """Devuelve (x, y) del marcador o None si no se ve en este cuadro."""
        if not self.calibrado:
            return None
        contornos, _ = cv2.findContours(self.mascara(hsv), cv2.RETR_EXTERNAL,
                                        cv2.CHAIN_APPROX_SIMPLE)
        mejor, mejor_area = None, CC.AREA_MIN_PX
        for c in contornos:
            area = cv2.contourArea(c)
            if area < mejor_area:
                continue
            m = cv2.moments(c)
            if m["m00"] == 0:
                continue
            centro = (m["m10"] / m["m00"], m["m01"] / m["m00"])
            if self.pos is not None and math.dist(centro, self.pos) > CC.RADIO_BUSQUEDA_PX:
                continue                    # demasiado lejos: probablemente es otra cosa
            mejor, mejor_area = centro, area
        if mejor is None and self.pos is not None:
            # Lo perdimos cerca: se busca en toda la imagen la próxima vez.
            self.pos = None
            return None
        if mejor is not None:
            self.pos = mejor
        return mejor


class DetectorColor:
    """Modo "color": un Marcador de color por articulación (hay que aprenderlos con clic)."""
    modo = "color"

    def __init__(self):
        self.marcadores = {n: Marcador(n) for n in CC.MARCADORES}

    @property
    def listo(self):
        return all(m.calibrado for m in self.marcadores.values())

    def buscar(self, imagen_bgr):
        """{nombre: (x, y) o None} para hombro, codo y muñeca."""
        hsv = cv2.cvtColor(imagen_bgr, cv2.COLOR_BGR2HSV)
        return {n: m.buscar(hsv) for n, m in self.marcadores.items()}


class DetectorAruco:
    """Modo "aruco": cada articulación lleva un cuadro impreso con su número (ID).

    Los cuadros se imprimen con  python python/generar_marcadores.py
    (crea docs/marcadores_aruco.pdf; imprimir a TAMAÑO REAL).
    """
    modo = "aruco"
    listo = True                                    # no hay nada que aprender

    def __init__(self):
        diccionario = cv2.aruco.getPredefinedDictionary(
            getattr(cv2.aruco, CC.ARUCO_DICCIONARIO))
        parametros = cv2.aruco.DetectorParameters()
        # Afinar las esquinas a sub-píxel: el centro tiembla menos (menos R).
        parametros.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX
        self._detector = cv2.aruco.ArucoDetector(diccionario, parametros)
        self._nombre_de_id = {i: n for n, i in CC.ARUCO_IDS.items()}
        self.esquinas = {}              # {nombre: 4 esquinas} del último cuadro (para dibujar)
        self.rechazados = []            # cuadriláteros que parecían marcador pero no se leyeron

    def buscar(self, imagen_bgr):
        """{nombre: (x, y) o None}: el centro de cada marcador encontrado."""
        gris = cv2.cvtColor(imagen_bgr, cv2.COLOR_BGR2GRAY)
        esquinas, ids, rechazados = self._detector.detectMarkers(gris)
        self.rechazados = rechazados
        self.esquinas = {}
        pos = {n: None for n in CC.MARCADORES}
        if ids is not None:
            for c, i in zip(esquinas, ids.flatten()):
                nombre = self._nombre_de_id.get(int(i))
                if nombre is None or pos[nombre] is not None:
                    continue                # ID ajeno o repetido: se ignora
                c = c.reshape(4, 2)
                self.esquinas[nombre] = c
                pos[nombre] = (float(c[:, 0].mean()), float(c[:, 1].mean()))
        return pos


def crear_detector(modo=None):
    modo = modo or CC.MODO_DETECCION
    if modo == "aruco":
        return DetectorAruco()
    if modo == "color":
        return DetectorColor()
    raise ValueError(f"Modo de detección desconocido: {modo!r} (use 'aruco' o 'color')")


def angulos_brazo(hombro, codo, muneca):
    """Posiciones en píxeles -> (θ1, θ2) en grados, con la convención del robot.

    La imagen tiene el eje y hacia ABAJO; se invierte para que "arriba en la
    imagen" sea +y (como en el dibujo del robot):  θ1 = 90° es el brazo hacia arriba.
    """
    v1 = (codo[0] - hombro[0], -(codo[1] - hombro[1]))
    v2 = (muneca[0] - codo[0], -(muneca[1] - codo[1]))
    a1 = math.degrees(math.atan2(v1[1], v1[0]))
    a2 = math.degrees(math.atan2(v2[1], v2[0]))
    theta2 = (a2 - a1 + 180) % 360 - 180          # ángulo relativo, en (−180, 180]
    theta1 = a1 % 360
    if theta1 > 270:                               # deja θ1 cerca del rango del robot
        theta1 -= 360
    return theta1, theta2
