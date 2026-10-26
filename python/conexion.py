"""Comunicación con el ESP32 por el cable USB (puerto serie).

Habla el mismo "idioma" que firmware/prueba_servos: líneas de texto como
"h 90, c 120\n". Es exactamente lo que tú escribías en el Monitor Serie.
"""
import time

import serial
from serial.tools import list_ports

BAUDIOS = 115200          # debe coincidir con Serial.begin(115200) del ESP32
ESPERA_ARRANQUE_S = 2.0   # al abrir el puerto, el ESP32 se reinicia; hay que esperarlo


def orden_servos(servo_hombro, servo_codo):
    """Texto que entiende el ESP32 para mover ambos servos a la vez."""
    return f"h {servo_hombro}, c {servo_codo}\n"


def puertos_disponibles():
    """Lista de (puerto, descripción), p. ej. ("COM5", "Silicon Labs CP210x ...")."""
    return [(p.device, p.description) for p in list_ports.comports()]


def detectar_puerto():
    """Adivina el puerto del ESP32 por el chip USB-serie que suele traer la placa."""
    pistas = ("CP210", "CH340", "CH910", "USB-SERIAL", "USB SERIAL", "UART")
    for puerto, descripcion in puertos_disponibles():
        if any(p in descripcion.upper() for p in pistas):
            return puerto
    return None


class ConexionESP32:
    def __init__(self):
        self._serial = None
        self._pendiente = ""      # texto recibido que aún no completa una línea
        self._t_apertura = 0.0

    @property
    def conectado(self):
        return self._serial is not None and self._serial.is_open

    @property
    def listo(self):
        """True cuando ya pasó el reinicio del ESP32 y puede recibir órdenes."""
        return self.conectado and time.monotonic() - self._t_apertura > ESPERA_ARRANQUE_S

    def conectar(self, puerto):
        # timeout=0 -> leer nunca se queda esperando: devuelve lo que haya y sigue.
        self._serial = serial.Serial(puerto, BAUDIOS, timeout=0)
        self._t_apertura = time.monotonic()
        self._pendiente = ""

    def desconectar(self):
        if self._serial is not None:
            self._serial.close()
        self._serial = None

    def enviar_servos(self, servo_hombro, servo_codo):
        self._serial.write(orden_servos(servo_hombro, servo_codo).encode("ascii"))

    def leer_lineas(self):
        """Devuelve las líneas COMPLETAS que el ESP32 haya enviado desde la última vez."""
        if not self.conectado or self._serial.in_waiting == 0:
            return []
        datos = self._serial.read(self._serial.in_waiting)
        return self._separar_lineas(datos)

    def _separar_lineas(self, datos):
        # Los bytes llegan "a pedazos": una línea puede venir partida en dos
        # lecturas. Se guarda el trozo final incompleto para la próxima vez.
        self._pendiente += datos.decode("utf-8", errors="replace")
        *completas, self._pendiente = self._pendiente.split("\n")
        return [linea.strip() for linea in completas if linea.strip()]
