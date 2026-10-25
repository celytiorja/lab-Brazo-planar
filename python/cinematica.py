"""Cinemática directa e inversa de un brazo planar de 2 GDL.

Convención (ver docs/01_cinematica.md):
  - θ1: ángulo del eslabón 1 medido desde el eje +x (antihorario positivo).
  - θ2: ángulo del eslabón 2 medido RELATIVO al eslabón 1 (0° = brazo estirado).
  - Ángulos en grados, longitudes en las unidades que uses (aquí mm).

Las funciones aceptan números o arreglos de numpy, así sirven tanto para un
punto como para una trayectoria completa.
"""
import numpy as np


def cinematica_directa(theta1_deg, theta2_deg, L1, L2):
    """Ángulos -> posición. Devuelve (x, y) de la punta y (xc, yc) del codo.

    Idea: sumar dos flechas. La 1.ª apunta con θ1; la 2.ª con θ1+θ2,
    porque el codo va montado ENCIMA del eslabón 1 y hereda su giro.
    """
    t1 = np.radians(theta1_deg)
    t12 = t1 + np.radians(theta2_deg)

    xc = L1 * np.cos(t1)          # punta de la 1.ª flecha = codo
    yc = L1 * np.sin(t1)
    x = xc + L2 * np.cos(t12)     # + la 2.ª flecha = punta
    y = yc + L2 * np.sin(t12)
    return (x, y), (xc, yc)


def cinematica_inversa(x, y, L1, L2, codo="abajo"):
    """Posición -> ángulos (θ1, θ2) en grados.

    codo="abajo" -> θ2 >= 0 ;  codo="arriba" -> θ2 <= 0.
    (Con el brazo apuntando hacia +y, "abajo" deja el codo a la derecha de la
    línea hombro-punta.) Lanza ValueError si el punto no es alcanzable.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)

    # 1) Ley de cosenos en el triángulo hombro-codo-punta -> ángulo del codo.
    r2 = x**2 + y**2
    c2 = (r2 - L1**2 - L2**2) / (2 * L1 * L2)

    # Si |cos θ2| > 1 no existe triángulo: el punto está fuera de alcance.
    # (Se tolera un error numérico mínimo para los puntos justo en el borde.)
    if np.any(np.abs(c2) > 1 + 1e-9):
        raise ValueError(
            f"Punto fuera de alcance: r debe estar entre {abs(L1 - L2):.1f} "
            f"y {L1 + L2:.1f}"
        )
    c2 = np.clip(c2, -1.0, 1.0)

    signo = 1.0 if codo == "abajo" else -1.0
    s2 = signo * np.sqrt(1 - c2**2)
    t2 = np.arctan2(s2, c2)

    # 2) θ1 = (ángulo hacia la punta) − (desvío que provoca el eslabón 2).
    t1 = np.arctan2(y, x) - np.arctan2(L2 * s2, L1 + L2 * c2)

    return np.degrees(t1), np.degrees(t2)


def alcanzable(x, y, L1, L2):
    """True si (x, y) está dentro del anillo de trabajo |L1−L2| <= r <= L1+L2."""
    r = np.hypot(x, y)
    return (r >= abs(L1 - L2)) & (r <= L1 + L2)
