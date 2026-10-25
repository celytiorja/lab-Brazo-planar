"""Simulador interactivo del brazo 2 GDL.

  - Mueve los sliders θ1 y θ2  -> CINEMÁTICA DIRECTA (ves dónde queda la punta).
  - Haz clic en el área gris   -> CINEMÁTICA INVERSA (el brazo calcula cómo llegar).
  - Cambia "codo arriba/abajo" -> ves las dos soluciones para el mismo punto.

Ejecutar:  python python/simulador.py
"""
import matplotlib.pyplot as plt
import numpy as np
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

(linea_brazo,) = ax.plot([], [], "-o", lw=6, ms=10, color="tab:blue")
(rastro,) = ax.plot([], [], ".", ms=2, color="tab:orange")
texto = ax.text(0.02, 0.98, "", transform=ax.transAxes, va="top", family="monospace")
historial = []

s1 = Slider(fig.add_axes([0.12, 0.12, 0.6, 0.03]), "θ1 [°]",
            P.THETA1_MIN, P.THETA1_MAX, valinit=30)
s2 = Slider(fig.add_axes([0.12, 0.06, 0.6, 0.03]), "θ2 [°]",
            P.THETA2_MIN, P.THETA2_MAX, valinit=45)
radio = RadioButtons(fig.add_axes([0.80, 0.45, 0.17, 0.12]), ("abajo", "arriba"))
fig.text(0.80, 0.58, "Codo:")


def dibujar(_=None):
    (x, y), (xc, yc) = cinematica_directa(s1.val, s2.val, L1, L2)
    linea_brazo.set_data([0, xc, x], [0, yc, y])
    historial.append((x, y))
    rastro.set_data(*zip(*historial[-300:]))
    texto.set_text(f"θ1 = {s1.val:7.2f}°   θ2 = {s2.val:7.2f}°\n"
                   f"x  = {x:7.2f} mm  y  = {y:7.2f} mm")
    fig.canvas.draw_idle()


def al_hacer_clic(evento):
    if evento.inaxes is not ax:
        return
    x, y = evento.xdata, evento.ydata
    if not alcanzable(x, y, L1, L2):
        texto.set_text("Punto fuera de alcance")
        fig.canvas.draw_idle()
        return
    t1, t2 = cinematica_inversa(x, y, L1, L2, codo=radio.value_selected)
    # -90° y 270° son la misma dirección; se expresa θ1 en [0, 360) para compararlo
    # con los límites de la articulación.
    t1 = float(t1) % 360
    if not (P.THETA1_MIN <= t1 <= P.THETA1_MAX and P.THETA2_MIN <= t2 <= P.THETA2_MAX):
        texto.set_text(f"Alcanzable, pero fuera de los límites de las articulaciones\n"
                       f"(θ1={t1:.1f}°, θ2={float(t2):.1f}°). Prueba el otro codo.")
        fig.canvas.draw_idle()
        return
    s1.set_val(t1)   # set_val dispara dibujar() automáticamente
    s2.set_val(float(t2))


s1.on_changed(dibujar)
s2.on_changed(dibujar)
fig.canvas.mpl_connect("button_press_event", al_hacer_clic)
dibujar()
plt.show()
