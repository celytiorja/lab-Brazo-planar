# Capturas descartadas (se conservan como evidencia)

| Archivo | Motivo |
|---|---|
| `seno_lento_01` | Muestreo irregular: fs real ≈ 54 Hz, Δt de 1 a 40 ms (nominal 10 ms) |
| `seno_rapido_01` | Muestreo irregular: fs real ≈ 56 Hz, Δt de 1 a 40 ms (nominal 10 ms) |

**Causa encontrada con estos mismos datos** (firmware `adquisicion-1.0`): cada
`servo.write()` bloqueaba al ESP32 unos 15 ms cuando se llamaba antes de que
terminara el pulso anterior (20 ms). En los perfiles seno la consigna cambia en
casi cada muestra, así que el muestreo se atrasaba:

| Escrituras a servos entre dos muestras | Δt medio |
|---|---|
| 0 | ≈ 8 ms |
| 1 | ≈ 26 ms |
| 2 | ≈ 40 ms |

En los escalones (una escritura cada 2 s) el muestreo salió perfecto (100.00 Hz).
`python/validar_datos.py` detecta el problema automáticamente (chequeo
"fs real dentro de ±2 %").

**Solución** (firmware `adquisicion-1.1`): la lectura de las IMU corre en una
tarea propia en el núcleo 0 del ESP32 con período fijo (`vTaskDelayUntil`), y
los servos se escriben como máximo cada 20 ms desde el núcleo 1.

## Segunda iteración: firmware 1.1 (`*_fw1.1`)

| Archivo | fs real | Δt mín–máx | Muestras perdidas | Lectura I2C de IMU1 (t2 − t1) |
|---|---|---|---|---|
| `seno_lento_01_fw1.1` | 96.6 Hz | 1.1–39.8 ms | 89 | mediana 520 µs, **máx 39 286 µs** |
| `seno_rapido_01_fw1.1` | 99.1 Hz | 1.1–39.8 ms | 14 | mediana 520 µs, **máx 39 286 µs** |

Mejoró mucho (de ~55 Hz a ~97–99 Hz), pero la propia lectura I2C seguía tardando
hasta 40 ms SOLO en la fase de movimiento de los senos (en `escalones_02`, con la
misma versión, el máximo fue 522 µs). Causa: `Wire.begin()` se llamaba en
`setup()` (núcleo 1), así que la interrupción del I2C quedaba en el núcleo de los
servos; cuando `servo.write()` lo ocupaba, la lectura en el núcleo 0 esperaba.

**Solución** (firmware `adquisicion-1.2`): `Wire.begin()` e inicialización de
las IMU se hacen dentro de la tarea de muestreo (núcleo 0).
