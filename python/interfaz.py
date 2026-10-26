"""Interfaz gráfica: mueve el brazo REAL desde el PC.

Es el simulador + una conexión con el ESP32. Cada vez que el brazo del dibujo
cambia, se traducen θ1, θ2 a ángulos de servo y se envía "h <..>, c <..>".

Requisito: el ESP32 debe tener cargado firmware/prueba_servos y el Monitor Serie
de Arduino debe estar CERRADO (un puerto COM solo puede usarlo un programa a la vez).

Ejecutar:  python python/interfaz.py           (detecta el puerto solo)
           python python/interfaz.py COM5      (o le dices cuál)
"""
import sys

import matplotlib.pyplot as plt
from matplotlib.widgets import Button, TextBox
from serial import SerialException

from conexion import ConexionESP32, detectar_puerto, puertos_disponibles
from servos import modelo_a_servo, servo_a_modelo
from simulador import VistaBrazo

PERIODO_MS = 40      # cada cuánto se revisa si hay que enviar algo (25 veces/s)
LINEAS_REGISTRO = 14


class Interfaz:
    def __init__(self, puerto_inicial=""):
        self.conexion = ConexionESP32()
        self.objetivo = None   # (servo_hombro, servo_codo) que pide el dibujo
        self.enviado = None    # lo último que de verdad se envió al ESP32
        self.registro = []

        self.fig = plt.figure(figsize=(13, 7))
        self.fig.canvas.manager.set_window_title("Brazo planar 2 GDL - interfaz")

        # Panel derecho: conexión, ángulos de servo y lo que responde el ESP32.
        x0 = 0.66
        self.fig.text(x0, 0.94, "Conexión con el ESP32", fontsize=12, weight="bold")
        self.caja_puerto = TextBox(self.fig.add_axes([x0 + 0.06, 0.87, 0.10, 0.04]),
                                   "Puerto ", initial=puerto_inicial)
        self.boton_conectar = Button(self.fig.add_axes([x0 + 0.18, 0.87, 0.12, 0.04]),
                                     "Conectar")
        self.boton_conectar.on_clicked(self.al_pulsar_conectar)
        self.estado = self.fig.text(x0, 0.83, "Desconectado", color="tab:red")

        self.texto_servos = self.fig.text(x0, 0.74, "", family="monospace", fontsize=10)
        self.boton_inicio = Button(self.fig.add_axes([x0, 0.66, 0.30, 0.04]),
                                   "Ir a posición de inicio (servos 90°, 90°)")
        self.boton_inicio.on_clicked(self.al_pulsar_inicio)

        self.fig.text(x0, 0.61, "Lo que responde el ESP32:", weight="bold")
        self.texto_registro = self.fig.text(x0, 0.59, "", family="monospace",
                                            fontsize=8, va="top")

        # El dibujo del brazo ocupa el 64 % izquierdo. Arranca en servos (90°, 90°),
        # que es donde el ESP32 deja los servos al encender.
        self.vista = VistaBrazo(self.fig, izquierda=0.0, ancho=0.64,
                                theta_inicial=servo_a_modelo(90, 90),
                                al_mover=self.al_mover_brazo)

        # Reloj: cada PERIODO_MS revisa si hay algo que enviar o leer.
        self.reloj = self.fig.canvas.new_timer(interval=PERIODO_MS)
        self.reloj.add_callback(self.cada_periodo)
        self.reloj.start()

    # ---------- Eventos de la ventana ----------
    def al_mover_brazo(self, theta1, theta2):
        # Solo se ANOTA el objetivo. El envío lo hace cada_periodo(): si arrastras
        # un slider se generan cientos de eventos, pero al ESP32 le llega como
        # máximo una orden cada 40 ms.
        self.objetivo = modelo_a_servo(theta1, theta2)
        self.texto_servos.set_text(
            f"Modelo:  θ1 = {theta1:7.2f}°   θ2 = {theta2:7.2f}°\n"
            f"Servos:  hombro = {self.objetivo[0]:3d}°   codo = {self.objetivo[1]:3d}°"
        )

    def al_pulsar_conectar(self, _):
        if self.conexion.conectado:
            self.conexion.desconectar()
            self.boton_conectar.label.set_text("Conectar")
            self.poner_estado("Desconectado", "tab:red")
            return
        puerto = self.caja_puerto.text.strip()
        if not puerto:
            disponibles = ", ".join(p for p, _ in puertos_disponibles()) or "ninguno"
            self.poner_estado(f"Escribe el puerto. Disponibles: {disponibles}", "tab:red")
            return
        try:
            self.conexion.conectar(puerto)
        except SerialException as error:
            self.poner_estado(f"No se pudo abrir {puerto}. ¿Monitor Serie abierto?",
                              "tab:red")
            self.anotar(f"[error] {error}")
            return
        self.enviado = None   # al terminar el reinicio se enviará la posición actual
        self.boton_conectar.label.set_text("Desconectar")
        self.poner_estado(f"Conectado a {puerto} (esperando reinicio del ESP32...)",
                          "tab:orange")

    def al_pulsar_inicio(self, _):
        self.vista.mover_a(*servo_a_modelo(90, 90))

    # ---------- Bucle periódico ----------
    def cada_periodo(self):
        if not self.conexion.conectado:
            return
        try:
            for linea in self.conexion.leer_lineas():
                self.anotar(linea)
            if self.conexion.listo:
                if self.estado.get_color() != "tab:green":
                    self.poner_estado(f"Conectado y listo", "tab:green")
                if self.objetivo is not None and self.objetivo != self.enviado:
                    self.conexion.enviar_servos(*self.objetivo)
                    self.enviado = self.objetivo
        except (SerialException, OSError) as error:
            # Típico: se desconectó el cable USB.
            self.conexion.desconectar()
            self.boton_conectar.label.set_text("Conectar")
            self.poner_estado("Conexión perdida", "tab:red")
            self.anotar(f"[error] {error}")

    # ---------- Ayudantes ----------
    def poner_estado(self, mensaje, color):
        self.estado.set_text(mensaje)
        self.estado.set_color(color)
        self.fig.canvas.draw_idle()

    def anotar(self, linea):
        self.registro = (self.registro + [linea])[-LINEAS_REGISTRO:]
        self.texto_registro.set_text("\n".join(self.registro))
        self.fig.canvas.draw_idle()


if __name__ == "__main__":
    puerto = sys.argv[1] if len(sys.argv) > 1 else (detectar_puerto() or "")
    interfaz = Interfaz(puerto)
    plt.show()
