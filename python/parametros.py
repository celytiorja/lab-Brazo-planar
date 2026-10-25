"""Parámetros físicos del brazo. Todo el código lee de aquí, así un cambio
de medida se hace en UN solo lugar."""

# Longitud de cada eslabón, de centro de rotación a centro de rotación [mm].
# ⚠️ PROVISIONALES: reemplazar con las medidas del modelo / del brazo real.
L1_MM = 100.0   # hombro -> codo
L2_MM = 80.0    # codo -> punta

# Rango permitido de cada articulación [grados] (se ajustará al calibrar servos).
THETA1_MIN, THETA1_MAX = 0.0, 180.0
THETA2_MIN, THETA2_MAX = -90.0, 90.0
