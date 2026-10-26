"""Simulador interactivo del brazo 2 GDL.

  - Mueve los sliders θ1 y θ2  -> CINEMÁTICA DIRECTA (ves dónde queda la punta).
  - Haz clic en el área gris   -> CINEMÁTICA INVERSA (el brazo calcula cómo llegar).
  - Brazo azul = solución actual. Brazo gris punteado = la OTRA solución que llega
    al mismo punto (espejo sobre la línea roja hombro-punta).
  - Botones "abajo / arriba"   -> el brazo salta a la otra solución sin mover la punta.

Ejecutar:  python python/simulador.py
"""
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.widgets import RadioButtons, Slider

import parametros as P
from cinematica import alcanzable, cinematica_directa, cinematica_inversa

L1, L2 = P.L1_MM, P.L2_MM
alcance = L1 + L2

fig, ax = plt.subplots(figsize=(8, 7))
fig.subplots_adjust(bottom=0.25, right=0.78)
ax.set_aspect("equal")
ax.set_xlim(-alcance * 1.1, alcance * 1.1)
ax.set_ylim(-alcance * 1.1, alcance * 1.1)
ax.grid(alpha=0.3)
ax.set_xlabel("x [mm]")
ax.set_ylabel("y [mm]")

# Espacio de trabajo: anillo entre |L1-L2| y L1+L2.
ax.add_patch(Circle((0, 0), L1 + L2, color="0.9", zorder=0))
ax.add_patch(Circle((0, 0), abs(L1 - L2), color="white", zorder=0))

(linea_espejo,) = ax.plot([], [], ":", lw=1.5, color="tab:red")
(linea_fantasma,) = ax.plot([], [], "--o", lw=3, ms=7, color="0.55")
(linea_brazo,) = ax.plot([], [], "-o", lw=6, ms=10, color="tab:blue")
(rastro,) = ax.plot([], [], ".", ms=2, color="tab:orange")
texto = ax.text(0.02, 0.98, "", transform=ax.transAxes, va="top", family="monospace")
aviso = ax.text(0.02, 0.02, "", transform=ax.transAxes, va="bottom", color="tab:red")
historial = []

s1 = Slider(fig.add_axes([0.12, 0.12, 0.6, 0.03]), "θ1 [°]",
            P.THETA1_MIN, P.THETA1_MAX, valinit=30)
s2 = Slider(fig.add_axes([0.12, 0.06, 0.6, 0.03]), "θ2 [°]",
            P.THETA2_MIN, P.THETA2_MAX, valinit=45)
fig.text(0.80, 0.58, "Codo:")
radio = RadioButtons(fig.add_axes([0.80, 0.45, 0.17, 0.12]), ("abajo", "arriba"))


def nombre_codo(theta2):
    """θ2 > 0 -> codo abajo ; θ2 < 0 -> codo arriba (ver docs/01_cinematica.md)."""
    return "abajo" if theta2 >= 0 else "arriba"


def dentro_de_limites(t1, t2):
    return P.THETA1_MIN <= t1 <= P.THETA1_MAX and P.THETA2_MIN <= t2 <= P.THETA2_MAX


def resolver(x, y, codo):
    """Cinemática inversa con θ1 expresado en [0, 360) para compararlo con los límites."""
    t1, t2 = cinematica_inversa(x, y, L1, L2, codo=codo)
    return float(t1) % 360, float(t2)


def mover_a(t1, t2):
    """Pone los dos sliders y redibuja UNA sola vez (sin pasos intermedios)."""
    s1.eventson = False
    s1.set_val(t1)
    s1.eventson = True
    s2.set_val(t2)   # este sí dispara dibujar()


def dibujar(_=None):
    (x, y), (xc, yc) = cinematica_directa(s1.val, s2.val, L1, L2)
    linea_brazo.set_data([0, xc, x], [0, yc, y])
    linea_espejo.set_data([0, x], [0, y])

    # La otra solución para la MISMA punta: el codo reflejado.
    actual = nombre_codo(s2.val)
    otro = "arriba" if actual == "abajo" else "abajo"
    t1_o, t2_o = resolver(x, y, otro)
    _, (xc_o, yc_o) = cinematica_directa(t1_o, t2_o, L1, L2)
    linea_fantasma.set_data([0, xc_o, x], [0, yc_o, y])

    historial.append((x, y))
    rastro.set_data(*zip(*historial[-300:]))
    texto.set_text(
        f"AZUL (codo {actual:6s}): θ1 = {s1.val:7.2f}°  θ2 = {s2.val:7.2f}°\n"
        f"GRIS (codo {otro:6s}): θ1 = {t1_o:7.2f}°  θ2 = {t2_o:7.2f}°\n"
        f"Punta:  x = {x:7.2f} mm   y = {y:7.2f} mm"
    )
    # Mantener los botones de acuerdo con lo que se ve, sin disparar su evento.
    if radio.value_selected != actual:
        radio.eventson = False
        radio.set_active(0 if actual == "abajo" else 1)
        radio.eventson = True
    fig.canvas.draw_idle()


def ir_a_punto(x, y, codo):
    if not alcanzable(x, y, L1, L2):
        aviso.set_text("Punto fuera de alcance (fuera del anillo gris)")
        fig.canvas.draw_idle()
        return
    t1, t2 = resolver(x, y, codo)
    if not dentro_de_limites(t1, t2):
        aviso.set_text(f"Codo {codo}: necesitaría θ1={t1:.0f}°, θ2={t2:.0f}°, "
                       f"fuera de los límites de los servos")
        fig.canvas.draw_idle()
        return
    aviso.set_text("")
    mover_a(t1, t2)


def al_hacer_clic(evento):
    if evento.inaxes is ax:
        ir_a_punto(evento.xdata, evento.ydata, radio.value_selected)


def al_cambiar_codo(codo):
    # Misma punta, otra forma de doblar el brazo.
    (x, y), _ = cinematica_directa(s1.val, s2.val, L1, L2)
    ir_a_punto(x, y, codo)
    dibujar()   # por si no se pudo cambiar: los botones vuelven a la solución actual


s1.on_changed(dibujar)
s2.on_changed(dibujar)
radio.on_clicked(al_cambiar_codo)
fig.canvas.mpl_connect("button_press_event", al_hacer_clic)
dibujar()

if __name__ == "__main__":
    plt.show()
