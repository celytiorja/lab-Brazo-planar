"""Dibujo rápido con "blitting".

Redibujar una figura completa de matplotlib (ejes, números, botones, leyendas)
tarda ~200 ms. Pero en cada cuadro solo cambian unas pocas líneas. La idea:

  1. Dibujar la figura completa UNA vez, sin las líneas que se mueven
     (marcadas como "animadas"), y guardar esa imagen como fondo.
  2. En cada cuadro: pegar el fondo guardado, dibujar encima SOLO las líneas
     animadas y mostrar el resultado ("blit" = copiar un bloque de píxeles).

Si algo obliga a redibujar todo (cambiar el tamaño de la ventana, mover un
slider, cambiar la escala de un eje), matplotlib emite un "draw_event" y aquí
se vuelve a guardar el fondo automáticamente.
"""


class Blitter:
    def __init__(self, canvas, artistas=()):
        self.canvas = canvas
        self.fondo = None
        self.artistas = []
        for a in artistas:
            self.agregar(a)
        canvas.mpl_connect("draw_event", self._al_redibujar_todo)

    def agregar(self, artista):
        artista.set_animated(True)       # el dibujo normal lo omite: lo pinta el blitter
        self.artistas.append(artista)

    def _al_redibujar_todo(self, _evento):
        self.fondo = self.canvas.copy_from_bbox(self.canvas.figure.bbox)
        self._pintar_animados()

    def _pintar_animados(self):
        fig = self.canvas.figure
        for a in self.artistas:
            fig.draw_artist(a)

    def actualizar(self):
        """Muestra el estado actual de los artistas animados (rápido)."""
        if self.fondo is None:            # aún no hay fondo: primer dibujo completo
            self.canvas.draw_idle()
            return
        self.canvas.restore_region(self.fondo)
        self._pintar_animados()
        self.canvas.blit(self.canvas.figure.bbox)
