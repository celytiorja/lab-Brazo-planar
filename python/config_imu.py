"""Configuración de adquisición y montaje de las IMU.

Todo lo que describe CÓMO se tomaron los datos vive aquí y se copia dentro del
.json que acompaña cada captura (trazabilidad: dentro de un año se puede saber
con qué escalas, montaje y calibración se grabó cada archivo).
"""

# ---------- Firmware firmware/adquisicion ----------
VERSION_FIRMWARE = "adquisicion-1.0"
BAUDIOS_ADQUISICION = 460800
FS_HZ = 100.0                 # frecuencia de muestreo nominal
DLPF_HZ = 44                  # filtro paso bajo interno de la MPU-6050 (antialias)
GYRO_LSB_POR_DPS = 65.5       # rango ±500 °/s
ACC_LSB_POR_G = 16384.0       # rango ±2 g

COLUMNAS_CRUDAS = [
    "seq", "t1_us", "t2_us", "perfil", "fase", "cmd_h", "cmd_c",
    "ax1", "ay1", "az1", "gx1", "gy1", "gz1",
    "ax2", "ay2", "az2", "gx2", "gy2", "gz2",
]

PERFILES = {1: "escalones", 2: "seno_lento", 3: "seno_rapido"}
FASES = {-1: "manual", 0: "reposo_inicial", 1: "movimiento", 2: "reposo_final"}

# ---------- Correspondencia sensor / eje / articulación ----------
# IMU1 (0x68) va sobre el eslabón 1 -> mide φ1 = θ1             (ángulo absoluto)
# IMU2 (0x69) va sobre el eslabón 2 -> mide φ2 = θ1 + θ2        (ángulo absoluto)
# El ángulo del codo se obtiene como θ2 = φ2 − φ1.
#
# EJE_GIRO: qué canal del giroscopio es perpendicular al plano del brazo y con
# qué signo, para que "+" signifique giro ANTIHORARIO (igual que θ en el modelo).
# ⚠️ VERIFICAR al montar las IMU con firmware/prueba_hardware (girar a mano el
# eslabón en sentido antihorario: el canal elegido debe dar valores POSITIVOS).
EJE_GIRO = {1: ("gz", +1), 2: ("gz", +1)}

# ¿El brazo se mueve en un plano VERTICAL? Entonces la gravedad está dentro del
# plano y el acelerómetro da una segunda medida del ángulo (inclinación) que NO
# deriva. Si el plano es HORIZONTAL (sobre la mesa), la gravedad es perpendicular
# al plano y el acelerómetro no ve el ángulo: solo queda el giroscopio.
PLANO_VERTICAL = False

# Solo se usan si PLANO_VERTICAL = True. Ejes del acelerómetro que quedan dentro
# del plano: φ_acel = atan2(signo_a · a, signo_b · b) + offset.
# Con el eje x del módulo a lo largo del eslabón y el y perpendicular (en el plano),
# en reposo a_x = g·sin φ y a_y = g·cos φ  ->  φ = atan2(a_x, a_y).
EJES_INCLINACION = {1: (("ax", +1), ("ay", +1)), 2: (("ax", +1), ("ay", +1))}
OFFSET_INCLINACION_DEG = {1: 0.0, 2: 0.0}


def instantanea():
    """Copia de esta configuración para guardarla junto a cada captura."""
    return {
        "version_firmware": VERSION_FIRMWARE,
        "baudios": BAUDIOS_ADQUISICION,
        "fs_hz": FS_HZ,
        "dlpf_hz": DLPF_HZ,
        "gyro_lsb_por_dps": GYRO_LSB_POR_DPS,
        "acc_lsb_por_g": ACC_LSB_POR_G,
        "eje_giro": {str(k): list(v) for k, v in EJE_GIRO.items()},
        "plano_vertical": PLANO_VERTICAL,
        "ejes_inclinacion": {str(k): [list(e) for e in v] for k, v in EJES_INCLINACION.items()},
        "offset_inclinacion_deg": {str(k): v for k, v in OFFSET_INCLINACION_DEG.items()},
    }
