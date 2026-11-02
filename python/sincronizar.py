"""Subida AUTOMÁTICA de las capturas a GitHub (lo mismo que harías a mano).

Después de cada captura, la interfaz llama a subir_capturas(), que ejecuta:

    git add datos/crudos                    (1) preparar las capturas nuevas
    git commit -m "Captura: ..."            (2) guardarlas en tu historial local
    git pull --no-rebase --no-edit -X ours  (3) traer lo que haya en GitHub (y unir)
    (rehacer el manifiesto)                 (4) por si llegaron capturas o reglas nuevas
    git push                                (5) subir

¿Por qué "-X ours" en el pull? El único archivo que podemos tocar los dos es
datos/crudos/manifiesto.json, y ese archivo se REHACE solo en el paso (4). Si
choca, se queda tu versión y enseguida se regenera: el conflicto desaparece.
Las capturas nunca chocan: cada una tiene un nombre nuevo.

Si no hay internet, los commits quedan en tu PC y se suben en la próxima captura.
"""
import subprocess
import threading

import reporte as Rp

_candado = threading.Lock()


def _git(*args):
    r = subprocess.run(["git", *args], cwd=Rp.RAIZ, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return r.returncode, (r.stdout + r.stderr).strip()


def subir_capturas(mensaje, avisar=print, rutas=("datos/crudos",)):
    """Hace add → commit → pull → manifiesto → push. `avisar(texto)` informa cada paso."""
    if not _candado.acquire(blocking=False):
        avisar("Ya se está subiendo una captura; esta irá en la próxima subida.")
        return False
    try:
        codigo, _ = _git("--version")
        if codigo != 0:
            avisar("Git no está disponible: las capturas quedan solo en tu PC.")
            return False
        _git("add", *rutas)
        codigo, salida = _git("commit", "-m", mensaje)
        if codigo != 0 and "nothing to commit" not in salida and "nada para hacer commit" not in salida:
            avisar(f"git commit falló: {salida[-120:]}")
            return False

        codigo, salida = _git("pull", "--no-rebase", "--no-edit", "-X", "ours")
        if codigo != 0:
            avisar(f"git pull falló (¿sin internet?): {salida[-120:]}. Se reintentará luego.")
            return False

        import grabador                     # aquí para evitar importaciones circulares
        grabador.actualizar_manifiesto()
        _git("add", "datos/crudos/manifiesto.json")
        _git("commit", "-m", "Manifiesto actualizado")   # si no cambió, no hace nada

        codigo, salida = _git("push")
        if codigo != 0:
            avisar(f"git push falló (¿sin internet?): {salida[-120:]}. Queda en tu PC.")
            return False
        avisar("Subido a GitHub ✓")
        return True
    finally:
        _candado.release()


def subir_en_segundo_plano(mensaje, avisar=print, rutas=("datos/crudos",)):
    """Igual que subir_capturas, pero sin congelar la ventana (la red puede tardar)."""
    hilo = threading.Thread(target=subir_capturas, args=(mensaje, avisar, rutas), daemon=True)
    hilo.start()
    return hilo
