"""Simulador interactivo del brazo 2 GDL.

  - Mueve los sliders θ1 y θ2  -> CINEMÁTICA DIRECTA (ves dónde queda la punta).
  - Haz clic en el área gris   -> CINEMÁTICA INVERSA (el brazo calcula cómo llegar).
  - Brazo azul = solución actual. Brazo gris punteado = la OTRA solución que llega
    al mismo punto (espejo sobre la línea roja hombro-punta).
  - Botones "abajo / arriba"   -> el brazo salta a la otra solución sin mover la punta.

Ejecutar:  python python/simulador.py

La clase VistaBrazo también la usa interfaz.py: es el mismo dibujo, pero allí
cada movimiento se envía además al brazo real.
"""
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.widgets import RadioButtons, Slider

import parametros as P
from cinematica import alcanzable, cinematica_directa, cinematica_inversa

L1, L2 = P.L1_MM, P.L2_MM


def nombre_codo(theta2):
    """θ2 > 0 -> codo abajo ; θ2 < 0 -> codo arriba (ver docs/01_cinematica.md)."""
    return "abajo" if theta2 >= 0 else "arriba"


def dentro_de_limites(t1, t2):
    return P.THETA1_MIN <= t1 <= P.THETA1_MAX and P.THETA2_MIN <= t2 <= P.THETA2_MAX


def resolver(x, y, codo):
    """Cinemática inversa con θ1 expresado en [0, 360) para compararlo con los límites."""
    t1, t2 = cinematica_inversa(x, y, L1, L2, codo=codo)
    return float(t1) % 360, float(t2)


class VistaBrazo:
    """Dibujo del brazo + sliders + selector de codo, dentro de una figura.

    izquierda, ancho: franja horizontal de la figura que ocupa (fracción 0..1).
    al_mover(θ1, θ2): función opcional que se llama cada vez que el brazo cambia.
    """

    def __init__(self, fig, izquierda=0.0, ancho=1.0, theta_inicial=(30, 45),
                 al_mover=None):
        self.fig = fig
        self.al_mover = al_mover
        self.historial = []

        def caja(u, y, du, dy):   # u, du: posición relativa dentro de la franja
            return fig.add_axes([izquierda + u * ancho, y, du * ancho, dy])

        alcance = L1 + L2
        ax = self.ax = caja(0.08, 0.25, 0.70, 0.70)
        ax.set_aspect("equal")
        ax.set_xlim(-alcance * 1.1, alcance * 1.1)
        ax.set_ylim(-alcance * 1.1, alcance * 1.1)
        ax.grid(alpha=0.3)
        ax.set_xlabel("x [mm]")
        ax.set_ylabel("y [mm]")

        # Espacio de trabajo: anillo entre |L1-L2| y L1+L2.
        ax.add_patch(Circle((0, 0), L1 + L2, color="0.9", zorder=0))
        ax.add_patch(Circle((0, 0), abs(L1 - L2), color="white", zorder=0))

        (self.linea_espejo,) = ax.plot([], [], ":", lw=1.5, color="tab:red")
        (self.linea_fantasma,) = ax.plot([], [], "--o", lw=3, ms=7, color="0.55")
        (self.linea_brazo,) = ax.plot([], [], "-o", lw=6, ms=10, color="tab:blue")
        (self.rastro,) = ax.plot([], [], ".", ms=2, color="tab:orange")
        self.texto = ax.text(0.02, 0.98, "", transform=ax.transAxes, va="top",
                             family="monospace", fontsize=9)
        self.aviso = ax.text(0.02, 0.02, "", transform=ax.transAxes, va="bottom",
                             color="tab:red", fontsize=9)

        self.s1 = Slider(caja(0.15, 0.12, 0.60, 0.03), "θ1 [°]",
                         P.THETA1_MIN, P.THETA1_MAX, valinit=theta_inicial[0])
        self.s2 = Slider(caja(0.15, 0.06, 0.60, 0.03), "θ2 [°]",
                         P.THETA2_MIN, P.THETA2_MAX, valinit=theta_inicial[1])
        fig.text(izquierda + 0.80 * ancho, 0.58, "Codo:")
        self.radio = RadioButtons(caja(0.80, 0.45, 0.18, 0.12), ("abajo", "arriba"))

        self.s1.on_changed(self.dibujar)
        self.s2.on_changed(self.dibujar)
        self.radio.on_clicked(self.al_cambiar_codo)
        fig.canvas.mpl_connect("button_press_event", self.al_hacer_clic)
        self.dibujar()

    @property
    def theta(self):
        return self.s1.val, self.s2.val

    def mover_a(self, t1, t2):
        """Pone los dos sliders y redibuja UNA sola vez (sin pasos intermedios)."""
        self.s1.eventson = False
        self.s1.set_val(t1)
        self.s1.eventson = True
        self.s2.set_val(t2)   # este sí dispara dibujar()

    def dibujar(self, _=None):
        t1, t2 = self.theta
        (x, y), (xc, yc) = cinematica_directa(t1, t2, L1, L2)
        self.linea_brazo.set_data([0, xc, x], [0, yc, y])
        self.linea_espejo.set_data([0, x], [0, y])

        # La otra solución para la MISMA punta: el codo reflejado.
        actual = nombre_codo(t2)
        otro = "arriba" if actual == "abajo" else "abajo"
        t1_o, t2_o = resolver(x, y, otro)
        _, (xc_o, yc_o) = cinematica_directa(t1_o, t2_o, L1, L2)
        self.linea_fantasma.set_data([0, xc_o, x], [0, yc_o, y])

        self.historial.append((x, y))
        self.rastro.set_data(*zip(*self.historial[-300:]))
        self.texto.set_text(
            f"AZUL (codo {actual:6s}): θ1 = {t1:7.2f}°  θ2 = {t2:7.2f}°\n"
            f"GRIS (codo {otro:6s}): θ1 = {t1_o:7.2f}°  θ2 = {t2_o:7.2f}°\n"
            f"Punta:  x = {x:7.2f} mm   y = {y:7.2f} mm"
        )
        # Mantener los botones de acuerdo con lo que se ve, sin disparar su evento.
        if self.radio.value_selected != actual:
            self.radio.eventson = False
            self.radio.set_active(0 if actual == "abajo" else 1)
            self.radio.eventson = True
        if self.al_mover is not None:
            self.al_mover(t1, t2)
        self.fig.canvas.draw_idle()

    def ir_a_punto(self, x, y, codo):
        if not alcanzable(x, y, L1, L2):
            self.aviso.set_text("Punto fuera de alcance (fuera del anillo gris)")
            self.fig.canvas.draw_idle()
            return
        t1, t2 = resolver(x, y, codo)
        if not dentro_de_limites(t1, t2):
            self.aviso.set_text(f"Codo {codo}: necesitaría θ1={t1:.0f}°, θ2={t2:.0f}°, "
                                f"fuera de los límites de los servos")
            self.fig.canvas.draw_idle()
            return
        self.aviso.set_text("")
        self.mover_a(t1, t2)

    def al_hacer_clic(self, evento):
        if evento.inaxes is self.ax:
            self.ir_a_punto(evento.xdata, evento.ydata, self.radio.value_selected)

    def al_cambiar_codo(self, codo):
        # Misma punta, otra forma de doblar el brazo.
        (x, y), _ = cinematica_directa(*self.theta, L1, L2)
        self.ir_a_punto(x, y, codo)
        self.dibujar()   # por si no se pudo cambiar: los botones vuelven a la solución actual


if __name__ == "__main__":
    figura = plt.figure(figsize=(8, 7))
    vista = VistaBrazo(figura)
    plt.show()
