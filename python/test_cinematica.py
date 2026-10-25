"""Pruebas automáticas de la cinemática. Ejecutar con:  python -m pytest python/

Una prueba es una afirmación que el código debe cumplir siempre. Si mañana
cambias cinematica.py y rompes algo, estas pruebas te avisan.
"""
import numpy as np
import pytest

from cinematica import cinematica_directa, cinematica_inversa

L1, L2 = 10.0, 8.0


def test_ejemplo_a_mano():
    # El mismo ejemplo resuelto a mano en docs/01_cinematica.md
    (x, y), _ = cinematica_directa(30, 45, L1, L2)
    assert x == pytest.approx(10.731, abs=1e-3)
    assert y == pytest.approx(12.727, abs=1e-3)


def test_brazo_estirado():
    (x, y), _ = cinematica_directa(0, 0, L1, L2)
    assert (x, y) == pytest.approx((L1 + L2, 0))


@pytest.mark.parametrize("codo", ["abajo", "arriba"])
def test_ida_y_vuelta(codo):
    # Directa(Inversa(p)) debe devolver p, para muchos puntos al azar.
    rng = np.random.default_rng(0)
    r = rng.uniform(abs(L1 - L2) + 0.1, L1 + L2 - 0.1, 200)
    a = rng.uniform(-np.pi, np.pi, 200)
    x, y = r * np.cos(a), r * np.sin(a)

    t1, t2 = cinematica_inversa(x, y, L1, L2, codo=codo)
    (xr, yr), _ = cinematica_directa(t1, t2, L1, L2)
    np.testing.assert_allclose(xr, x, atol=1e-9)
    np.testing.assert_allclose(yr, y, atol=1e-9)


def test_inversa_recupera_angulos():
    (x, y), _ = cinematica_directa(30, 45, L1, L2)
    t1, t2 = cinematica_inversa(x, y, L1, L2, codo="abajo")
    assert (t1, t2) == pytest.approx((30, 45))


def test_fuera_de_alcance():
    with pytest.raises(ValueError):
        cinematica_inversa(L1 + L2 + 1, 0, L1, L2)
