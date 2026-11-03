"""Genera la hoja de marcadores ArUco para imprimir (teleoperación con cámara).

    python python/generar_marcadores.py

Crea  docs/marcadores_aruco.pdf  (y .png). IMPRIMIR A TAMAÑO REAL (100 %, sin
"ajustar a la página") y comprobar con una regla la línea de 10 cm de la hoja.

Cada cuadro es un número en "código de barras 2D": borde negro + 4×4 casillas.
  ID 0 -> HOMBRO     ID 1 -> CODO     ID 2 -> MUÑECA   (config_camara.ARUCO_IDS)

Reglas para que se detecten bien:
  - Deja el MARGEN BLANCO alrededor del cuadro (al menos 1 casilla): el detector
    necesita ver dónde termina el borde negro.
  - Pégalo sobre cartón para que quede PLANO (un cuadro doblado no se lee).
  - Papel mate; si brilla con la lámpara, se "borra" una parte.

¿Sin impresora? Al final se imprime en la terminal el dibujo de cada cuadro para
hacerlo a mano en papel cuadriculado (6×6 casillas, rellenas con marcador negro).
"""
import cv2
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import config_camara as CC  # noqa: E402
import reporte as Rp  # noqa: E402

CM_POR_PULGADA = 2.54
ANCHO_CM, ALTO_CM = 21.0, 29.7          # hoja carta/A4 (cabe en las dos)
NOMBRES = {"hombro": "HOMBRO", "codo": "CODO", "muneca": "MUÑECA"}


def imagen_marcador(id_marcador, casillas_px=1):
    """Matriz 6×6 (0 = negro, 255 = blanco) del marcador, una casilla por píxel."""
    dic = cv2.aruco.getPredefinedDictionary(getattr(cv2.aruco, CC.ARUCO_DICCIONARIO))
    return cv2.aruco.generateImageMarker(dic, id_marcador, 6 * casillas_px)


def generar(ruta_pdf=None, lado_cm=CC.ARUCO_LADO_CM, lado_pequeno_cm=4.0):
    ruta_pdf = ruta_pdf or Rp.RAIZ / "docs" / "marcadores_aruco.pdf"
    fig = plt.figure(figsize=(ANCHO_CM / CM_POR_PULGADA, ALTO_CM / CM_POR_PULGADA))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, ANCHO_CM)
    ax.set_ylim(ALTO_CM, 0)                         # y hacia abajo, en cm desde arriba
    ax.axis("off")
    ax.text(1.5, 1.4, "Marcadores ArUco: teleoperación con cámara", fontsize=13, weight="bold")
    ax.text(1.5, 2.1, f"Imprimir a TAMAÑO REAL. Grandes: {lado_cm:g} cm (usar estos). "
            f"Pequeños: {lado_pequeno_cm:g} cm (repuesto).", fontsize=8.5)
    ax.text(1.5, 2.6, "Recorta por la línea gris (deja el margen blanco), pega sobre cartón.",
            fontsize=8.5)
    # Regla de 10 cm para comprobar la escala de impresión
    ax.plot([1.5, 11.5], [3.2, 3.2], "k-", lw=1)
    for x in (1.5, 11.5):
        ax.plot([x, x], [3.0, 3.4], "k-", lw=1)
    ax.text(12.0, 3.35, "← debe medir 10 cm", fontsize=8)

    margen = 1.0                                    # blanco alrededor del cuadro (cm)
    grandes = [(2.5, 4.8), (12.5, 4.8), (2.5, 14.0)]                 # esquina sup. izq.
    pequenos = [(2.3, 23.3), (8.8, 23.3), (15.3, 23.3)]
    for (nombre, idm), g, pq in zip(CC.ARUCO_IDS.items(), grandes, pequenos):
        for (x0, y0), lado in ((g, lado_cm), (pq, lado_pequeno_cm)):
            ax.imshow(imagen_marcador(idm), cmap="gray", vmin=0, vmax=255,
                      interpolation="nearest", extent=(x0, x0 + lado, y0 + lado, y0))
            ax.add_patch(plt.Rectangle((x0 - margen, y0 - margen), lado + 2 * margen,
                                       lado + 2 * margen, fill=False, ec="0.6", lw=0.6, ls="--"))
            ax.text(x0 - margen, y0 + lado + margen + 0.5, f"ID {idm}: {NOMBRES[nombre]}",
                    fontsize=9, weight="bold" if lado == lado_cm else "normal")
    ayuda = ("Dónde va cada uno (vista desde arriba):\n"
             "• HOMBRO: sobre el hombro\n"
             "• CODO: sobre el codo\n"
             "• MUÑECA: sobre la muñeca\n\n"
             "Planos, mirando a la cámara,\n"
             "con el margen blanco completo.")
    ax.text(11.5, 14.0, ayuda, fontsize=9, va="top", linespacing=1.6)
    ax.set_xlim(0, ANCHO_CM)
    ax.set_ylim(ALTO_CM, 0)
    ruta_pdf.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(ruta_pdf)
    fig.savefig(ruta_pdf.with_suffix(".png"), dpi=150)
    plt.close(fig)
    return ruta_pdf


def dibujo_texto(id_marcador):
    """El cuadro como texto: '██' negro, '  ' blanco (para dibujarlo a mano)."""
    m = imagen_marcador(id_marcador)
    return "\n".join("".join("██" if v == 0 else "··" for v in fila) for fila in m)


if __name__ == "__main__":
    ruta = generar()
    print(f"Hoja creada: {ruta.relative_to(Rp.RAIZ)}  (y .png)")
    print("Ábrela e imprime a TAMAÑO REAL (100 %). Mide la línea de 10 cm.\n")
    print("Para dibujar a mano (6×6 casillas; ██ = negro, ·· = blanco):")
    for nombre, idm in CC.ARUCO_IDS.items():
        print(f"\nID {idm} -> {NOMBRES[nombre]}")
        print(dibujo_texto(idm))
