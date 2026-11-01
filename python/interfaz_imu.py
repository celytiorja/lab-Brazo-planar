"""INTERFAZ CON IMU — ver las MPU en vivo, mover el brazo y grabar capturas.

Requiere: ESP32 con firmware/adquisicion (460800 baudios) y el Monitor Serie de
Arduino CERRADO.

    python python/interfaz_imu.py            (detecta el puerto)
    python python/interfaz_imu.py COM5

Qué hay en la ventana:
  IZQUIERDA  el brazo: azul = lo que pides (sliders/clic), negro punteado = la
             consigna que el ESP32 está aplicando, y las tres ESTIMACIONES hechas
             con las IMU: gris = integración directa, naranja = media móvil,
             verde = Kalman.
  CENTRO     últimos 10 s: velocidad angular (giroscopio vs Kalman) y θ1, θ2.
  DERECHA    botones: conectar, calibrar el sesgo, grabar capturas para las
             entregas, y elegir con qué se mueve el brazo (teleoperación).

Uso típico:
  1. Conectar.  2. Brazo quieto -> "Calibrar sesgo".  3. Grabar reposo 40 s.
  4. Perfil 1, 2 y 3 (dos veces cada uno: la 1.ª es AJUSTE y la 2.ª VALIDACIÓN).
  5. python python/analisis_e1.py   y   python python/analisis_e2.py
"""
import sys
import time

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import Button, RadioButtons, TextBox
from serial import SerialException

import config_imu as C
from cinematica import cinematica_directa
from conexion import ConexionESP32, detectar_puerto, puertos_disponibles
from grabador import Grabacion, parsear_linea_datos
from servos import modelo_a_servo, servo_a_modelo
from simulador import L1, L2, VistaBrazo
from tiempo_real import HISTORIA_S, ProcesadorTiempoReal

PERIODO_MS = 50                 # refresco de pantalla (20 por segundo)
PERIODO_ORDENES_S = 0.05        # máximo 20 órdenes por segundo a los servos
DURACION_REPOSO_S = 40.0        # la guía pide al menos 30 s
FUENTES = ("Sliders (consigna)", "Integración directa", "Media móvil", "Kalman")
COLOR = {"dir": "0.45", "mm": "tab:orange", "kf": "tab:green", "cmd": "k"}


class InterfazIMU:
    def __init__(self, puerto_inicial=""):
        self.conexion = ConexionESP32()
        self.proc = ProcesadorTiempoReal()
        self.cfg_firmware = ""
        self.grabacion = None
        self.grabacion_perfil = 0
        self.grabacion_limite_s = None
        self.transmitiendo = False
        self.perfil_activo = 0
        self.objetivo_sliders = None
        self.ultimo_envio = None
        self.t_ultimo_envio = 0.0
        self.mensajes = []

        self.fig = plt.figure(figsize=(16, 9))
        self.fig.canvas.manager.set_window_title("Brazo planar 2 GDL - IMU en vivo")

        # ---------------- Izquierda: brazo ----------------
        self.vista = VistaBrazo(self.fig, izquierda=0.0, ancho=0.40,
                                theta_inicial=servo_a_modelo(90, 90),
                                al_mover=self.al_mover_sliders)
        ax = self.vista.ax
        self.brazos = {k: ax.plot([], [], "-o", lw=2.5, ms=4, color=COLOR[k], alpha=0.85)[0]
                       for k in ("dir", "mm", "kf")}
        self.brazos["cmd"] = ax.plot([], [], "--", lw=1.5, color="k")[0]

        # ---------------- Centro: señales ----------------
        x0, ancho = 0.45, 0.31
        self.ax_w = self.fig.add_axes([x0, 0.72, ancho, 0.23])
        self.ax_t1 = self.fig.add_axes([x0, 0.46, ancho, 0.23], sharex=self.ax_w)
        self.ax_t2 = self.fig.add_axes([x0, 0.20, ancho, 0.23], sharex=self.ax_w)
        self.lineas = {
            "w1": self.ax_w.plot([], [], lw=0.7, color="tab:blue", label="giro 1 (−sesgo)")[0],
            "w2": self.ax_w.plot([], [], lw=0.7, color="tab:purple", label="giro 2 (−sesgo)")[0],
            "wk1": self.ax_w.plot([], [], lw=1.4, color="tab:green", label="Kalman ω1")[0],
            "wk2": self.ax_w.plot([], [], lw=1.4, color="lime", label="Kalman ω2")[0],
        }
        for j, axj in ((1, self.ax_t1), (2, self.ax_t2)):
            self.lineas[f"cmd{j}"] = axj.plot([], [], "k--", lw=1, label="consigna")[0]
            self.lineas[f"dir{j}"] = axj.plot([], [], color=COLOR["dir"], lw=1, label="directa")[0]
            self.lineas[f"mm{j}"] = axj.plot([], [], color=COLOR["mm"], lw=1,
                                             label=f"media móvil N={self.proc.media.ventana}")[0]
            self.lineas[f"kf{j}"] = axj.plot([], [], color=COLOR["kf"], lw=1.4, label="Kalman")[0]
            axj.set_ylabel(f"θ{j} [°]")
            axj.grid(alpha=0.3)
            axj.legend(fontsize=7, loc="upper left", ncol=2)
        self.ax_w.set_ylabel("ω [°/s]")
        self.ax_w.grid(alpha=0.3)
        self.ax_w.legend(fontsize=7, loc="upper left", ncol=2)
        self.ax_t2.set_xlabel("t [s]")
        self.texto_estado = self.fig.text(x0, 0.015, "", family="monospace", fontsize=8.5,
                                          va="bottom")

        # ---------------- Derecha: controles ----------------
        xc, wc = 0.79, 0.20

        def boton(y, texto, accion):
            b = Button(self.fig.add_axes([xc, y, wc, 0.035]), texto)
            b.on_clicked(accion)
            return b

        self.fig.text(xc, 0.965, "Conexión (firmware adquisicion)", weight="bold")
        self.caja_puerto = TextBox(self.fig.add_axes([xc + 0.04, 0.915, 0.07, 0.035]),
                                   "Puerto ", initial=puerto_inicial)
        self.boton_conectar = Button(self.fig.add_axes([xc + 0.12, 0.915, 0.08, 0.035]),
                                     "Conectar")
        self.boton_conectar.on_clicked(self.al_conectar)
        self.b_calibrar = boton(0.865, "Calibrar sesgo (brazo QUIETO 3 s)", self.al_calibrar)
        self.fig.text(xc, 0.83, "Grabar capturas (datos/crudos/)", weight="bold")
        self.b_reposo = boton(0.785, f"Grabar reposo {DURACION_REPOSO_S:.0f} s", self.al_grabar_reposo)
        self.b_p1 = boton(0.745, "Perfil 1: escalones (26 s)", lambda _: self.al_perfil(1))
        self.b_p2 = boton(0.705, "Perfil 2: seno lento (26 s)", lambda _: self.al_perfil(2))
        self.b_p3 = boton(0.665, "Perfil 3: seno rápido (16 s)", lambda _: self.al_perfil(3))
        self.b_libre = boton(0.625, "Grabar libre (iniciar / detener)", self.al_grabar_libre)

        self.fig.text(xc, 0.585, "Mover el brazo con:", weight="bold")
        self.radio_fuente = RadioButtons(self.fig.add_axes([xc, 0.44, wc, 0.14]), FUENTES)
        self.fig.text(xc, 0.415, "Q del Kalman:", weight="bold")
        nombres_q = [c["nombre"] for c in self.proc.configs]
        self.radio_q = RadioButtons(self.fig.add_axes([xc, 0.305, wc, 0.105]), nombres_q,
                                    active=nombres_q.index(self.proc.config_q["nombre"]))
        self.radio_q.on_clicked(self.al_cambiar_q)
        self.texto_msg = self.fig.text(xc, 0.29, "", family="monospace", fontsize=7.5, va="top")

        self.reloj = self.fig.canvas.new_timer(interval=PERIODO_MS)
        self.reloj.add_callback(self.cada_periodo)
        self.reloj.start()
        self.anotar("Escribe el puerto y pulsa Conectar." if not puerto_inicial
                    else f"Puerto detectado: {puerto_inicial}. Pulsa Conectar.")

    # ================= Eventos =================
    def al_mover_sliders(self, theta1, theta2):
        self.objetivo_sliders = modelo_a_servo(theta1, theta2)

    def al_conectar(self, _):
        if self.conexion.conectado:
            self._detener_grabacion("desconectado")
            self.conexion.desconectar()
            self.transmitiendo = False
            self.boton_conectar.label.set_text("Conectar")
            self.anotar("Desconectado.")
            return
        puerto = self.caja_puerto.text.strip()
        if not puerto:
            disp = ", ".join(p for p, _ in puertos_disponibles()) or "ninguno"
            self.anotar(f"Escribe el puerto. Disponibles: {disp}")
            return
        try:
            self.conexion.conectar(puerto, C.BAUDIOS_ADQUISICION)
        except SerialException as e:
            self.anotar(f"No se pudo abrir {puerto}. ¿Monitor Serie abierto? {e}")
            return
        self.boton_conectar.label.set_text("Desconectar")
        self.anotar(f"Conectado a {puerto}. Esperando reinicio del ESP32...")

    def al_calibrar(self, _):
        if not self.transmitiendo:
            self.anotar("Primero conecta.")
            return
        self.proc.empezar_calibracion()
        self.anotar("Calibrando: NO muevas el brazo 3 s...")

    def al_grabar_reposo(self, _):
        if self._puede_grabar():
            self.grabacion = Grabacion("estatico", "estatico", 0, self.cfg_firmware)
            self.grabacion_perfil = 0
            self.grabacion_limite_s = DURACION_REPOSO_S
            self.anotar(f"Grabando {self.grabacion.nombre}: brazo QUIETO {DURACION_REPOSO_S:.0f} s")

    def al_perfil(self, n):
        if not self._puede_grabar():
            return
        self.conexion.enviar(f"p {n}")
        self.perfil_activo = n
        self.grabacion = Grabacion(C.PERFILES[n], "perfil", n, self.cfg_firmware)
        self.grabacion_perfil = n
        self.grabacion_limite_s = None
        self.anotar(f"Perfil {n} ({C.PERFILES[n]}) -> {self.grabacion.nombre}")

    def al_grabar_libre(self, _):
        if self.grabacion is not None and self.grabacion_perfil == -1:
            self._detener_grabacion()
            return
        if self._puede_grabar():
            self.grabacion = Grabacion("libre", "libre", 0, self.cfg_firmware)
            self.grabacion_perfil = -1
            self.grabacion_limite_s = None
            self.anotar(f"Grabando {self.grabacion.nombre} (pulsa otra vez para detener)")

    def al_cambiar_q(self, nombre):
        self.proc.cambiar_q(nombre)
        self.anotar(f"Kalman: {nombre} (q = {self.proc.config_q['q']:.3g})")

    # ================= Bucle =================
    def cada_periodo(self):
        if self.conexion.conectado:
            try:
                self._leer()
                self._enviar_ordenes()
            except (SerialException, OSError) as e:
                self._detener_grabacion("conexión perdida")
                self.conexion.desconectar()
                self.transmitiendo = False
                self.boton_conectar.label.set_text("Conectar")
                self.anotar(f"Conexión perdida: {e}")
        self._dibujar()

    def _leer(self):
        if not self.transmitiendo and self.conexion.listo:
            self.conexion.enviar("s 1")
            self.conexion.enviar("?")
            self.transmitiendo = True
            self.anotar("Recibiendo datos. Brazo quieto y pulsa 'Calibrar sesgo'.")
        estaba_calibrando = self.proc.calibrando
        for linea in self.conexion.leer_lineas():
            if linea.startswith("#"):
                self._mensaje_firmware(linea)
                continue
            v = parsear_linea_datos(linea)
            if v is None:
                continue
            if self.grabacion is not None:
                # En un perfil solo se guardan sus muestras (no las de antes de empezar).
                if self.grabacion_perfil <= 0 or v[3] == self.grabacion_perfil:
                    self.grabacion.agregar(v)
            self.proc.procesar(v)
        if estaba_calibrando and not self.proc.calibrando:
            self.anotar("Calibrado. Ángulos reiniciados a la consigna.")
        if self.grabacion is not None and self.grabacion_limite_s is not None \
                and self.grabacion.duracion_s >= self.grabacion_limite_s:
            self._detener_grabacion()

    def _mensaje_firmware(self, linea):
        if linea.startswith("# cfg"):
            self.cfg_firmware = linea[2:]
            ok = "imu1_ok=1" in linea and "imu2_ok=1" in linea
            self.anotar("Firmware OK, IMU1 e IMU2 responden" if ok
                        else f"¡Revisa las IMU! {linea[2:80]}")
        elif linea.startswith("# fin_perfil"):
            self.perfil_activo = 0
            self._detener_grabacion()
            self.conexion.enviar("s 1")       # el firmware deja de transmitir al terminar
        elif linea.startswith("# error_i2c"):
            self.anotar(linea[2:])

    def _enviar_ordenes(self):
        if not self.conexion.listo or self.perfil_activo:
            return
        ahora = time.monotonic()
        fuente = self.radio_fuente.value_selected
        if fuente == FUENTES[0]:
            objetivo = self.objetivo_sliders
        else:
            if not self.proc.calibrado or self.proc.ultimo is None:
                return
            clave = {FUENTES[1]: "dir", FUENTES[2]: "mm", FUENTES[3]: "kf"}[fuente]
            objetivo = modelo_a_servo(*self.proc.ultimo[clave])
        if objetivo is None or objetivo == self.ultimo_envio:
            return
        if ahora - self.t_ultimo_envio < PERIODO_ORDENES_S:
            return
        self.conexion.enviar_servos(*objetivo)
        self.ultimo_envio = objetivo
        self.t_ultimo_envio = ahora

    # ================= Ayudantes =================
    def _puede_grabar(self):
        if not self.transmitiendo:
            self.anotar("Primero conecta.")
            return False
        if self.grabacion is not None:
            self.anotar("Ya hay una grabación en curso.")
            return False
        if not self.proc.calibrado:
            self.anotar("Aviso: aún no calibraste el sesgo (la captura se guarda igual).")
        return True

    def _detener_grabacion(self, nota=""):
        if self.grabacion is None:
            return
        g, self.grabacion = self.grabacion, None
        ruta = g.cerrar(nota)
        self.anotar(f"Guardado {ruta.name} ({g.muestras} muestras)" if ruta
                    else "Grabación vacía: no se guardó")

    def anotar(self, texto):
        self.mensajes = (self.mensajes + [texto])[-9:]
        self.texto_msg.set_text("\n".join(f"· {m[:46]}" for m in self.mensajes))

    def _dibujar(self):
        h = self.proc.hist
        if h["t"]:
            t = np.array(h["t"])
            for k, linea in self.lineas.items():
                linea.set_data(t, np.array(h[k]))
            t_fin = t[-1]
            self.ax_w.set_xlim(max(0, t_fin - HISTORIA_S), max(HISTORIA_S, t_fin))
            for axj, claves in ((self.ax_w, ("w1", "w2", "wk1", "wk2")),
                                (self.ax_t1, ("cmd1", "dir1", "mm1", "kf1")),
                                (self.ax_t2, ("cmd2", "dir2", "mm2", "kf2"))):
                y = np.concatenate([np.array(h[k]) for k in claves])
                lo, hi = np.nanmin(y), np.nanmax(y)
                margen = max(2.0, 0.1 * (hi - lo))
                axj.set_ylim(lo - margen, hi + margen)
            u = self.proc.ultimo
            for clave in ("dir", "mm", "kf"):
                (x, y), (xc, yc) = cinematica_directa(*u[clave], L1, L2)
                self.brazos[clave].set_data([0, xc, x], [0, yc, y])
            (x, y), (xc, yc) = cinematica_directa(*u["theta_cmd"], L1, L2)
            self.brazos["cmd"].set_data([0, xc, x], [0, yc, y])

        e = self.proc.estadisticas()
        grab = ""
        if self.grabacion is not None:
            grab = f"  ● GRABANDO {self.grabacion.nombre}: {self.grabacion.duracion_s:5.1f} s"
        b = self.proc.bias
        estado = "CALIBRANDO..." if self.proc.calibrando else \
            (f"sesgo = [{b[0]:+.3f}, {b[1]:+.3f}] °/s" if self.proc.calibrado else "SIN CALIBRAR")
        self.texto_estado.set_text(
            f"fs real {e['fs']:6.2f} Hz  jitter {e['jitter_us']:5.0f} µs  perdidas {e['perdidas']}"
            f"  |  Kalman {e['t_kalman_us']:5.0f} µs/muestra (máx {e['t_kalman_max_us']:4.0f})\n"
            f"{estado}  |  R: {self.proc.origen_R}  |  {self.proc.config_q['nombre']} "
            f"q={self.proc.config_q['q']:.3g}{grab}")
        self.fig.canvas.draw_idle()


if __name__ == "__main__":
    puerto = sys.argv[1] if len(sys.argv) > 1 else (detectar_puerto() or "")
    interfaz = InterfazIMU(puerto)
    plt.show()
