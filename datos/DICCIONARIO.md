# Diccionario de datos (evidencia E1)

Cada captura son **dos archivos con el mismo nombre**, en `datos/crudos/`:

- `nombre.csv`: datos **crudos**, exactamente como los envió el ESP32 (cuentas enteras), más
  la hora de llegada al PC.
- `nombre.json`: **configuración de la captura**: fecha, firmware, escalas, montaje de las IMU,
  calibración de los servos y commit de Git.

Los datos de prueba en `datos/sinteticos/` tienen el mismo formato, pero su `.json` dice
`"sintetico": true`. **No son mediciones.**

## Configuración de adquisición

| Parámetro | Valor | Dónde se fija |
|---|---|---|
| Frecuencia de muestreo nominal fs | 100 Hz (Δt = 10 ms) | `firmware/adquisicion` (`PERIODO_US`), `config_imu.FS_HZ` |
| Base de tiempo | `micros()` del ESP32 (µs, se desborda cada ~71,6 min) | firmware |
| Filtro paso bajo interno (DLPF) | ~44 Hz (registro CONFIG = 0x03), antialias por debajo de fs/2 = 50 Hz | firmware |
| Rango del giroscopio | ±500 °/s → **65,5 cuentas por °/s** | GYRO_CONFIG = 0x08 |
| Rango del acelerómetro | ±2 g → **16384 cuentas por g** | ACCEL_CONFIG = 0x00 |
| Resolución (1 cuenta) | 0,0153 °/s y 0,061 mg | — |
| Bus | I2C a 400 kHz: IMU1 0x68 (AD0 a GND), IMU2 0x69 (AD0 a 3,3 V) | firmware |
| Enlace al PC | USB serie, 460800 baudios, texto CSV | firmware, `config_imu.BAUDIOS_ADQUISICION` |
| Servos | MG996R, pulso 500–2500 µs ≈ 0–180°, resolución 1° | firmware |

## Columnas del CSV

| Columna | Tipo | Unidad | Sensor / origen | Significado |
|---|---|---|---|---|
| `seq` | entero | — | ESP32 | Número de muestra. Si salta, se perdieron muestras. |
| `t1_us` | entero | µs | ESP32 | `micros()` justo **antes** de leer la IMU1. Es la base de tiempo: Δt_k = t1_k − t1_{k−1}. |
| `t2_us` | entero | µs | ESP32 | `micros()` justo antes de leer la IMU2 (≈ t1 + 0,4 ms: lectura secuencial). |
| `perfil` | entero | — | ESP32 | 0 = manual/reposo, 1 = escalones, 2 = seno lento, 3 = seno rápido. |
| `fase` | entero | — | ESP32 | −1 = manual, 0 = reposo inicial (3 s), 1 = movimiento, 2 = reposo final (3 s). |
| `cmd_h` | entero | ° de servo | ESP32 | Consigna enviada al servo del hombro (0–180). **No es una medición.** |
| `cmd_c` | entero | ° de servo | ESP32 | Consigna enviada al servo del codo (0–180). **No es una medición.** |
| `ax1`, `ay1`, `az1` | entero | cuentas (÷16384 → g) | IMU1 (0x68), eslabón 1 | Aceleración específica en los ejes x, y, z del módulo. |
| `gx1`, `gy1`, `gz1` | entero | cuentas (÷65,5 → °/s) | IMU1 (0x68), eslabón 1 | Velocidad angular en los ejes x, y, z del módulo. |
| `ax2`, `ay2`, `az2` | entero | cuentas (÷16384 → g) | IMU2 (0x69), eslabón 2 | Ídem para la IMU2. |
| `gx2`, `gy2`, `gz2` | entero | cuentas (÷65,5 → °/s) | IMU2 (0x69), eslabón 2 | Ídem para la IMU2. |
| `t_pc_s` | decimal | s | PC | Momento de llegada al PC desde el inicio de la grabación (para estudiar la latencia; **no** se usa para integrar). |

## Correspondencia sensor – eje – articulación

| | IMU1 (0x68) | IMU2 (0x69) |
|---|---|---|
| Montada sobre | eslabón 1 (hombro → codo) | eslabón 2 (codo → punta) |
| Eje del giroscopio que mide el giro en el plano | `EJE_GIRO[1]` en `python/config_imu.py` (por defecto `gz`, signo +1) | `EJE_GIRO[2]` (por defecto `gz`, +1) |
| Mide | φ1 = θ1 | φ2 = θ1 + θ2 |
| Variable física | ω1 = θ̇1 | ω2 = θ̇1 + θ̇2 |

**Marco de referencia (importante):** cada IMU mide el giro de **su** eslabón **respecto al marco
fijo** (el mundo), no respecto al eslabón anterior. La IMU2 viaja sobre el eslabón 1, así que
también siente el giro del hombro. Por eso:

```
θ1 = φ1          θ2 = φ2 − φ1          (y en velocidad: θ̇2 = ω2 − ω1)
```

**Signo:** el canal se multiplica por el signo de `EJE_GIRO`, de modo que "+" sea **antihorario**,
igual que θ en el modelo cinemático (`docs/01_cinematica.md`). Esto se verifica al montar las IMU
(`docs/04_captura_y_entregas.md`, paso 3).

**Inclinación con el acelerómetro:** solo si el brazo se mueve en un **plano vertical**
(`PLANO_VERTICAL = True`): φ_acel = atan2(a_x, a_y) + offset. En un plano horizontal la gravedad
es perpendicular al plano y el acelerómetro no ve el ángulo.

## Archivo JSON de cada captura

| Clave | Contenido |
|---|---|
| `sintetico` | `false` en datos reales; `true` en datos de prueba |
| `fecha`, `modo`, `perfil`, `perfil_nombre` | Cuándo y qué se grabó (`estatico`, `perfil`, `libre`) |
| `duracion_s`, `muestras`, `perdidas` | Resumen de la captura |
| `firmware` | Línea `# cfg ...` que el ESP32 envió al arrancar (versión, escalas, IMU que respondieron) |
| `config_imu` | Copia de `python/config_imu.py`: escalas, `eje_giro`, `plano_vertical`, ejes de inclinación |
| `calibracion` | Offsets y signos de los servos, y L1/L2, vigentes al grabar. El análisis usa **estos**, aunque luego se recalibre. |
| `commit` | Commit de Git con el que se grabó (trazabilidad) |

## Manifiesto (`manifiesto.json`)

Dice qué archivo cumple cada papel. La interfaz lo arma sola.

| Clave | Archivo |
|---|---|
| `estatico` | Reposo ≥ 30 s: media, varianza, R |
| `dinamico_e1` | Registro dinámico de la Entrega 1 (escalones) |
| `ajuste` | Repetición `_01` de cada perfil: para elegir Q (Entrega 2) |
| `validacion` | Repetición `_02` de cada perfil: validación independiente |
| `verificacion_cinematica` | (opcional) Hoja de medidas de la verificación cinemática |
