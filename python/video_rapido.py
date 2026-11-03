"""Lectura del video con el MENOR retraso posible (para la teleoperación).

EL PROBLEMA (por qué "se traba"):
  DroidCam manda ~30 imágenes JPEG por segundo, una detrás de otra (MJPEG). OpenCV
  (cv2.VideoCapture) las guarda en una FILA y entrega siempre la más VIEJA. Si el
  programa tarda un poco más que lo que tarda en llegar una imagen, la fila crece y lo
  que ves (y lo que copia el robot) va cada vez más atrasado: 1 s, 2 s, 5 s...

LA SOLUCIÓN:
  Un HILO (un "trabajador" en paralelo) lee el video sin parar y solo guarda la imagen
  MÁS NUEVA. Las que nadie alcanzó a usar se botan SIN decodificarlas (decodificar un
  JPEG es lo que cuesta). El programa principal siempre toma la última: el retraso ya
  no se acumula.

  Para DroidCam (http://...) se lee el chorro MJPEG directamente: se buscan los bytes
  FF D8 (inicio de un JPEG) y FF D9 (fin). Si eso falla, se usa cv2.VideoCapture con
  la opción de "sin búfer". Para una webcam (0, 1...) o un archivo, también OpenCV.

Lo que NO se arregla con código: el retraso de la WiFi. Si el ping al teléfono da
cientos de ms, usa el HOTSPOT del teléfono (el PC se conecta a la red del teléfono).
"""
import os
import threading
import time
import urllib.request

import cv2
import numpy as np

INICIO_JPEG = b"\xff\xd8"
FIN_JPEG = b"\xff\xd9"
ANCHO_MAX_SIN_REDUCIR = 1000      # imágenes más anchas se decodifican a la mitad (más rápido)


class LectorVideo:
    """leer() -> (ok, imagen BGR, hora de LLEGADA al PC) del cuadro más nuevo no usado."""

    def __init__(self, fuente, timeout_s=4.0):
        self.fuente = fuente
        self.es_red = isinstance(fuente, str) and fuente.startswith(("http://", "https://"))
        self.es_archivo = isinstance(fuente, str) and not self.es_red
        self.metodo = ""
        self.descartados = 0              # cuadros que llegaron y se botaron por viejos
        self.recibidos = 0
        self._dato, self._t, self._id, self._usado = None, 0.0, 0, 0
        self._cond = threading.Condition()
        self._vivo = True
        self._hilo = None
        self._cam = None
        self._resp = None
        self._reducir = None
        if self.es_archivo:
            self._abrir_opencv()
            fps = self._cam.get(cv2.CAP_PROP_FPS)
            self._periodo = 1.0 / fps if fps and fps > 0 else 1 / 30
            self._t_archivo = None
            return
        if self.es_red:
            try:
                self._resp = urllib.request.urlopen(fuente, timeout=timeout_s)
                self.metodo = "MJPEG directo (sin búfer)"
                objetivo = self._bucle_mjpeg
            except Exception:
                self._resp = None
        if self._resp is None:
            self._abrir_opencv()
            objetivo = self._bucle_opencv
        if self.abierto():
            self._hilo = threading.Thread(target=objetivo, daemon=True)
            self._hilo.start()

    # ------------------------------------------------------------ apertura
    def _abrir_opencv(self):
        if self.es_red:
            # Pedirle a FFmpeg que no guarde cuadros (menos retraso).
            os.environ.setdefault("OPENCV_FFMPEG_CAPTURE_OPTIONS", "fflags;nobuffer|flags;low_delay")
        self._cam = cv2.VideoCapture(self.fuente)
        try:
            self._cam.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        except Exception:
            pass
        self.metodo = self.metodo or "OpenCV"

    def abierto(self):
        return self._resp is not None or (self._cam is not None and self._cam.isOpened())

    # ------------------------------------------------------------ hilos lectores
    def _guardar(self, dato, t):
        with self._cond:
            self.recibidos += 1
            if self._id > self._usado:
                self.descartados += 1            # el anterior nadie lo alcanzó a usar
            self._dato, self._t = dato, t
            self._id += 1
            self._cond.notify_all()

    def _bucle_mjpeg(self):
        buf = b""
        leer = getattr(self._resp, "read1", None) or self._resp.read
        while self._vivo:
            try:
                trozo = leer(65536)
            except Exception:
                trozo = b""
            if not trozo:
                time.sleep(0.05)
                continue
            buf += trozo
            fin = buf.rfind(FIN_JPEG)
            if fin == -1:
                if len(buf) > 4_000_000:          # basura: empezar de nuevo
                    buf = b""
                continue
            ini = buf.rfind(INICIO_JPEG, 0, fin)
            if ini != -1:
                # Si en este trozo venían varias imágenes completas, solo vale la última.
                viejas = buf.count(FIN_JPEG, 0, ini)
                if viejas:
                    with self._cond:
                        self.descartados += viejas
                        self.recibidos += viejas
                self._guardar(buf[ini:fin + 2], time.perf_counter())
            buf = buf[fin + 2:]

    def _bucle_opencv(self):
        while self._vivo:
            ok, img = self._cam.read()
            if not ok:
                time.sleep(0.05)
                continue
            self._guardar(img, time.perf_counter())

    # ------------------------------------------------------------ uso
    def _decodificar(self, dato):
        if isinstance(dato, np.ndarray):
            return dato
        arr = np.frombuffer(dato, np.uint8)
        if self._reducir is None:                 # 1.er cuadro: ¿es muy grande?
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            self._reducir = img is not None and img.shape[1] > ANCHO_MAX_SIN_REDUCIR
            if not self._reducir:
                return img
        return cv2.imdecode(arr, cv2.IMREAD_REDUCED_COLOR_2 if self._reducir else cv2.IMREAD_COLOR)

    def leer(self, espera_max_s=0.05):
        """Espera a lo sumo `espera_max_s` por un cuadro NUEVO (la ventana no se congela)."""
        if self.es_archivo:
            ok, img = self._cam.read()
            ahora = time.perf_counter()
            if self._t_archivo is None:
                self._t_archivo = ahora
            else:
                self._t_archivo += self._periodo
                time.sleep(max(0.0, self._t_archivo - ahora))      # a la velocidad real
            return ok, img, self._t_archivo
        with self._cond:
            self._cond.wait_for(lambda: self._id > self._usado, timeout=espera_max_s)
            if self._id <= self._usado:
                return False, None, None
            self._usado = self._id
            dato, t = self._dato, self._t
        img = self._decodificar(dato)
        return img is not None, img, t

    def segundos_sin_cuadro(self):
        return time.perf_counter() - self._t if self._t else float("inf")

    def cerrar(self):
        self._vivo = False
        if self._resp is not None:
            try:
                self._resp.close()
            except Exception:
                pass
        if self._hilo is not None:
            self._hilo.join(timeout=1.0)
        if self._cam is not None:
            self._cam.release()
