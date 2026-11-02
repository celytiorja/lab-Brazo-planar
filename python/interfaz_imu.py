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
import traceback

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import Button, RadioButtons, TextBox
from serial import SerialException

import config_imu as C
import parametros as P
from blit import Blitter
from cinematica import cinematica_directa
from conexion import ConexionESP32, detectar_puerto, puertos_disponibles
from grabador import Grabacion, parsear_linea_datos
from servos import modelo_a_servo, servo_a_modelo
from simulador import L1, L2, VistaBrazo
from tiempo_real import HISTORIA_S, ProcesadorTiempoReal

PERIODO_MS = 40                 # leer el puerto y enviar órdenes: 25 veces por segundo
DIBUJAR_CADA = 2                # dibujar 1 de cada 2 ciclos (12.5 cuadros/s: fluido al ojo)
PASO_GRAFICA = 3                # en las gráficas se dibuja 1 de cada 3 muestras
PERIODO_ESCALAS_S = 1.0         # cada cuánto se revisa si hay que cambiar la escala
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
        self._ciclo = 0
        self.n_lineas = 0          # todo lo que llega por el puerto
        self.n_datos = 0           # solo las líneas de datos "D,..." válidas

        self.fig = plt.figure(figsize=(16, 9))
        self.fig.canvas.manager.set_window_title("Brazo planar 2 GDL - IMU en vivo")

        # ---------------- Izquierda: brazo ----------------
        # redibujar=False: el brazo y los sliders se pintan con blitting (rápido).
        self.vista = VistaBrazo(self.fig, izquierda=0.0, ancho=0.40,
                                theta_inicial=servo_a_modelo(90, 90),
                                al_mover=self.al_mover_sliders, redibujar=False)
        for s in (self.vista.s1, self.vista.s2):
            s.drawon = False                 # el slider no pide redibujar TODA la figura
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
        # Eje de tiempo FIJO ("hace cuántos segundos"): así no hay que redibujar los
        # números del eje en cada cuadro; solo se mueven las líneas.
        self.ax_w.set_xlim(-HISTORIA_S, 0)
        self.ax_t2.set_xlabel("segundos atrás  (0 = ahora)")
        self.ax_w.set_ylim(-60, 60)
        self.ax_t1.set_ylim(P.THETA1_MIN - 10, P.THETA1_MAX + 10)
        self.ax_t2.set_ylim(P.THETA2_MIN - 10, P.THETA2_MAX + 10)
        self._t_escalas = 0.0
        self.texto_estado = self.fig.text(x0, 0.01, "", family="monospace", fontsize=8.5,
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
        self.b_inicio = boton(0.870, "Ir a posición de inicio (servos 90°, 90°)", self.al_ir_a_inicio)
        self.b_calibrar = boton(0.830, "Calibrar sesgo (brazo QUIETO 3 s)", self.al_calibrar)
        self.fig.text(xc, 0.795, "Grabar capturas (datos/crudos/)", weight="bold")
        self.b_reposo = boton(0.750, f"Grabar reposo {DURACION_REPOSO_S:.0f} s", self.al_grabar_reposo)
        self.b_p1 = boton(0.710, "Perfil 1: escalones (26 s)", lambda _: self.al_perfil(1))
        self.b_p2 = boton(0.670, "Perfil 2: seno lento (26 s)", lambda _: self.al_perfil(2))
        self.b_p3 = boton(0.630, "Perfil 3: seno rápido (16 s)", lambda _: self.al_perfil(3))
        self.b_libre = boton(0.590, "Grabar libre (iniciar / detener)", self.al_grabar_libre)

        self.fig.text(xc, 0.555, "Mover el brazo con:", weight="bold")
        self.radio_fuente = RadioButtons(self.fig.add_axes([xc, 0.415, wc, 0.135]), FUENTES)
        self.fig.text(xc, 0.39, "Q del Kalman:", weight="bold")
        nombres_q = [c["nombre"] for c in self.proc.configs]
        self.radio_q = RadioButtons(self.fig.add_axes([xc, 0.285, wc, 0.1]), nombres_q,
                                    active=nombres_q.index(self.proc.config_q["nombre"]))
        self.radio_q.on_clicked(self.al_cambiar_q)
        self.texto_msg = self.fig.text(xc, 0.27, "", family="monospace", fontsize=8.5, va="top",
                                       color="tab:blue")

        # Todo lo que cambia en cada cuadro se dibuja con blitting.
        self.blit = Blitter(self.fig.canvas, list(self.lineas.values()) +
                            list(self.brazos.values()) + self.vista.artistas_dinamicos() +
                            [self.texto_estado, self.texto_msg])

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
            self._texto_boton_conectar("Conectar")
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
        self._texto_boton_conectar("Desconectar")
        self.anotar(f"Conectado a {puerto}. Esperando reinicio del ESP32...")

    def al_ir_a_inicio(self, _):
        if self.perfil_activo:
            self.anotar("Hay un perfil en curso: espera a que termine.")
            return
        self.radio_fuente.set_active(0)        # mover con los sliders
        self.vista.mover_a(*servo_a_modelo(90, 90))
        self.anotar("Yendo a la posición de inicio (90°, 90°).")

    def al_calibrar(self, _):
        if not self.conexion.conectado:
            self.anotar("No estás conectado: pulsa 'Conectar' primero.")
            return
        if not self.transmitiendo or self.n_datos == 0:
            self.anotar("Conectado, pero aún no llegan datos de las IMU. Espera unos "
                        "segundos; si sigue igual, copia lo que dice la terminal.")
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
        # Todo va dentro de try: si algo falla, se muestra el error y el reloj
        # SIGUE funcionando (si no, la ventana se "congela" sin avisar).
        try:
            if self.conexion.conectado:
                try:
                    self._leer()
                    self._enviar_ordenes()
                except (SerialException, OSError) as e:
                    self._detener_grabacion("conexión perdida")
                    self.conexion.desconectar()
                    self.transmitiendo = False
                    self._texto_boton_conectar("Conectar")
                    self.anotar(f"Conexión perdida: {e}")
            # Leer y enviar en CADA ciclo (la teleoperación no espera al dibujo);
            # dibujar solo en algunos: dibujar es lo más caro.
            self._ciclo += 1
            if self._ciclo % DIBUJAR_CADA == 0:
                self._dibujar()
        except Exception as e:
            traceback.print_exc()
            self.anotar(f"ERROR interno: {type(e).__name__}: {e}")
            self.fig.canvas.draw_idle()

    def _leer(self):
        if not self.transmitiendo and self.conexion.listo:
            self.conexion.enviar("s 1")
            self.conexion.enviar("?")
            self.transmitiendo = True
            self.anotar("Recibiendo datos. Brazo quieto y pulsa 'Calibrar sesgo'.")
        estaba_calibrando = self.proc.calibrando
        for linea in self.conexion.leer_lineas():
            self.n_lineas += 1
            if linea.startswith("#"):
                self._mensaje_firmware(linea)
                continue
            v = parsear_linea_datos(linea)
            if v is None:
                if self.n_lineas <= 5:
                    self.anotar(f"Línea no reconocida: {linea[:40]!r}")
                continue
            self.n_datos += 1
            if self.n_datos == 1:
                self.anotar("Llegó la primera muestra de las IMU.")
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
        else:
            self.anotar(f"ESP32: {linea[2:60]}")

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

    def _texto_boton_conectar(self, texto):
        self.boton_conectar.label.set_text(texto)
        self.fig.canvas.draw_idle()   # el botón no es animado: pasa poco, se redibuja todo

    def anotar(self, texto):
        print(f"[interfaz] {texto}", flush=True)     # también en la terminal
        self.mensajes = (self.mensajes + [texto])[-9:]
        self.texto_msg.set_text("\n".join(f"· {m[:42]}" for m in self.mensajes))

    def _dibujar(self):
        h = self.proc.hist
        if h["t"]:
            t = np.array(h["t"])
            t = t[::-1][::PASO_GRAFICA][::-1]          # 1 de cada PASO, terminando en "ahora"
            t_rel = t - t[-1]
            datos = {k: np.array(h[k])[::-1][::PASO_GRAFICA][::-1] for k in self.lineas}
            for k, linea in self.lineas.items():
                linea.set_data(t_rel, datos[k])
            if time.monotonic() - self._t_escalas > PERIODO_ESCALAS_S:
                self._t_escalas = time.monotonic()
                self._ajustar_escalas(datos)
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
        if not self.conexion.conectado:
            conexion = "DESCONECTADO"
        elif not self.conexion.listo:
            conexion = "conectando..."
        else:
            conexion = f"recibidas {self.n_lineas} líneas ({self.n_datos} de datos)"
        self.texto_estado.set_text(
            f"{conexion}\n"
            f"fs real {e['fs']:6.2f} Hz  jitter {e['jitter_us']:5.0f} µs  perdidas {e['perdidas']}"
            f"  |  Kalman {e['t_kalman_us']:5.0f} µs/muestra (máx {e['t_kalman_max_us']:4.0f})\n"
            f"{estado}  |  R: {self.proc.origen_R}  |  {self.proc.config_q['nombre']} "
            f"q={self.proc.config_q['q']:.3g}{grab}")
        self.blit.actualizar()

    def _ajustar_escalas(self, datos):
        """Cambia la escala vertical SOLO si los datos se salen o quedan muy chicos.
        Cambiar la escala obliga a redibujar todo (lento), por eso se hace poco."""
        cambio = False
        for axj, claves, minimo in ((self.ax_w, ("w1", "w2", "wk1", "wk2"), 20.0),
                                    (self.ax_t1, ("cmd1", "dir1", "mm1", "kf1"), 10.0),
                                    (self.ax_t2, ("cmd2", "dir2", "mm2", "kf2"), 10.0)):
            y = np.concatenate([datos[k] for k in claves])
            y = y[np.isfinite(y)]
            if len(y) == 0:
                continue
            lo, hi = float(y.min()), float(y.max())
            centro, mitad = (lo + hi) / 2, max(minimo, hi - lo) / 2
            a, b = axj.get_ylim()
            se_sale = lo < a or hi > b
            muy_grande = (b - a) > 4 * (2 * mitad * 1.2)
            if se_sale or muy_grande:
                axj.set_ylim(centro - 1.2 * mitad, centro + 1.2 * mitad)
                cambio = True
        if cambio:
            self.fig.canvas.draw_idle()       # redibujo completo -> el blitter guarda el nuevo fondo


if __name__ == "__main__":
    puerto = sys.argv[1] if len(sys.argv) > 1 else (detectar_puerto() or "")
    interfaz = InterfazIMU(puerto)
    plt.show()
