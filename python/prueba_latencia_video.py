"""¿Por qué la cámara "se trababa"? Medición del retraso con y sin el lector nuevo.

    python python/prueba_latencia_video.py

Crea un DroidCam FALSO en el PC (un servidor que manda video MJPEG a 30 cuadros/s,
como el teléfono) y un programa que tarda 45 ms en procesar cada cuadro (más que los
33 ms entre cuadros). Cada cuadro lleva su número dibujado (12 cuadritos blanco/negro),
así se sabe CUÁNDO se envió y se mide su "edad" al usarlo.

Resultado típico:
    cv2.VideoCapture (antes)   edad del cuadro: inicio 74 ms, final 2221 ms   <- crece sin parar
    LectorVideo (ahora)        edad del cuadro: inicio 17 ms, final 17 ms     <- constante

Antes: OpenCV guarda los cuadros en una fila y entrega el más viejo; si el programa es
más lento que la cámara, la fila crece y el retraso se acumula. Ahora: se usa siempre el
cuadro más nuevo y los demás se botan sin decodificar (video_rapido.py).
No incluye la WiFi: eso se mide con  ping <IP del teléfono>.
"""
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import cv2
import numpy as np

from video_rapido import LectorVideo

FPS = 30
T_ENVIO = {}                       # número de cuadro -> hora en que el servidor lo envió


def cuadro_numerado(i):
    img = np.full((480, 640, 3), 128, np.uint8)
    for b in range(12):
        img[0:32, b * 32:(b + 1) * 32] = 255 if (i >> b) & 1 else 0
    return cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 80])[1].tobytes()


def numero_del_cuadro(img):
    return sum(1 << b for b in range(12) if img[16, b * 32 + 16].mean() > 128)


class DroidCamFalso(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "multipart/x-mixed-replace;boundary=dcmjpeg")
        self.end_headers()
        i, t0 = 0, time.perf_counter()
        try:
            while True:
                jpg = cuadro_numerado(i)
                T_ENVIO[i] = time.perf_counter()
                self.wfile.write(b"--dcmjpeg\r\nContent-Type: image/jpeg\r\nContent-Length: %d\r\n\r\n"
                                 % len(jpg) + jpg + b"\r\n")
                i += 1
                time.sleep(max(0.0, t0 + i / FPS - time.perf_counter()))
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass


def iniciar_servidor(puerto=8765):
    srv = ThreadingHTTPServer(("127.0.0.1", puerto), DroidCamFalso)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{puerto}/video"


def medir_edades(leer, trabajo_s=0.045, duracion_s=8.0):
    """Usa cuadros durante `duracion_s`, tardando `trabajo_s` en cada uno. Edades en ms."""
    edades = []
    t_fin = time.perf_counter() + duracion_s
    while time.perf_counter() < t_fin:
        ok, img = leer()
        if not ok:
            continue
        edades.append((time.perf_counter() - T_ENVIO[numero_del_cuadro(img)]) * 1e3)
        time.sleep(trabajo_s)                       # "procesar" el cuadro
    return np.array(edades)


def main():
    srv, url = iniciar_servidor()
    cap = cv2.VideoCapture(url)
    e1 = medir_edades(cap.read)
    cap.release()
    time.sleep(0.5)

    lector = LectorVideo(url)

    def leer_nuevo():
        ok, img, _ = lector.leer(0.2)
        return ok, img
    e2 = medir_edades(leer_nuevo)
    lector.cerrar()
    srv.shutdown()

    for nombre, e in (("cv2.VideoCapture (antes)", e1), ("LectorVideo (ahora)", e2)):
        print(f"{nombre:26s} cuadros usados {len(e):3d}   edad del cuadro: "
              f"inicio {e[:10].mean():5.0f} ms, final {e[-10:].mean():5.0f} ms")
    print(f"El lector nuevo botó {lector.descartados} de {lector.recibidos} cuadros por viejos "
          f"(el programa tarda 45 ms y llegan cada {1000 / FPS:.0f} ms).")


if __name__ == "__main__":
    main()
