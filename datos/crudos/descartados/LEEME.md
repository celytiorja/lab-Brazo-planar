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
