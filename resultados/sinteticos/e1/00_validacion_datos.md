# Validación automática de los datos crudos

| archivo | chequeo | resultado | detalle |
| --- | --- | --- | --- |
| estatico_01 | existe el JSON de configuración | OK | estatico_01.json |
| estatico_01 | columnas esperadas | OK | 19 columnas |
| estatico_01 | sin valores vacíos (NaN) | OK | 0 vacíos |
| estatico_01 | valores enteros (cuentas crudas) | OK | int |
| estatico_01 | seq creciente | OK | 0 retrocesos |
| estatico_01 | muestras perdidas (huecos en seq) | AVISO | 1 perdidas de 4000 (0.025 %) |
| estatico_01 | timestamps monótonos (con desborde de micros) | OK | 0 no crecientes |
| estatico_01 | fs real dentro de ±2 % | OK | 100.000 Hz (nominal 100) |
| estatico_01 | jitter de Δt < 1000 µs | OK | σ(Δt) = 28.1 µs |
| estatico_01 | desfase IMU2−IMU1 entre 0 y 5 ms | OK | media 410 µs |
| estatico_01 | reposo ≥ 30 s | OK | 40.0 s |
| estatico_01 | sin saturación (|cuentas| < 32760) | OK | ninguna |
| estatico_01 | ninguna IMU congelada (σ > 0 en cada canal) | OK | todos varían |
| estatico_01 | perfil/fase de reposo (0 / −1) | OK | perfiles {np.int64(0)} |
| escalones_01 | existe el JSON de configuración | OK | escalones_01.json |
| escalones_01 | columnas esperadas | OK | 19 columnas |
| escalones_01 | sin valores vacíos (NaN) | OK | 0 vacíos |
| escalones_01 | valores enteros (cuentas crudas) | OK | int |
| escalones_01 | seq creciente | OK | 0 retrocesos |
| escalones_01 | muestras perdidas (huecos en seq) | AVISO | 1 perdidas de 2600 (0.038 %) |
| escalones_01 | timestamps monótonos (con desborde de micros) | OK | 0 no crecientes |
| escalones_01 | fs real dentro de ±2 % | OK | 100.000 Hz (nominal 100) |
| escalones_01 | jitter de Δt < 1000 µs | OK | σ(Δt) = 27.7 µs |
| escalones_01 | desfase IMU2−IMU1 entre 0 y 5 ms | OK | media 410 µs |
| escalones_01 | duración | OK | 26.0 s |
| escalones_01 | sin saturación (|cuentas| < 32760) | OK | ninguna |
| escalones_01 | ninguna IMU congelada (σ > 0 en cada canal) | OK | todos varían |
| escalones_01 | un solo perfil y fases 0→1→2 en orden | OK | perfiles {np.int64(1)}, fases [np.int64(0), np.int64(1), np.int64(2)] |
| escalones_01 | el brazo medido sigue a la consigna | OK | amplitud medida/consigna = 1.00, 0.99 |
| seno_lento_01 | existe el JSON de configuración | OK | seno_lento_01.json |
| seno_lento_01 | columnas esperadas | OK | 19 columnas |
| seno_lento_01 | sin valores vacíos (NaN) | OK | 0 vacíos |
| seno_lento_01 | valores enteros (cuentas crudas) | OK | int |
| seno_lento_01 | seq creciente | OK | 0 retrocesos |
| seno_lento_01 | muestras perdidas (huecos en seq) | AVISO | 3 perdidas de 2600 (0.115 %) |
| seno_lento_01 | timestamps monótonos (con desborde de micros) | OK | 0 no crecientes |
| seno_lento_01 | fs real dentro de ±2 % | OK | 100.000 Hz (nominal 100) |
| seno_lento_01 | jitter de Δt < 1000 µs | OK | σ(Δt) = 28.0 µs |
| seno_lento_01 | desfase IMU2−IMU1 entre 0 y 5 ms | OK | media 410 µs |
| seno_lento_01 | duración | OK | 26.0 s |
| seno_lento_01 | sin saturación (|cuentas| < 32760) | OK | ninguna |
| seno_lento_01 | ninguna IMU congelada (σ > 0 en cada canal) | OK | todos varían |
| seno_lento_01 | un solo perfil y fases 0→1→2 en orden | OK | perfiles {np.int64(2)}, fases [np.int64(0), np.int64(1), np.int64(2)] |
| seno_lento_01 | el brazo medido sigue a la consigna | OK | amplitud medida/consigna = 0.99, 0.99 |
| seno_rapido_01 | existe el JSON de configuración | OK | seno_rapido_01.json |
| seno_rapido_01 | columnas esperadas | OK | 19 columnas |
| seno_rapido_01 | sin valores vacíos (NaN) | OK | 0 vacíos |
| seno_rapido_01 | valores enteros (cuentas crudas) | OK | int |
| seno_rapido_01 | seq creciente | OK | 0 retrocesos |
| seno_rapido_01 | muestras perdidas (huecos en seq) | OK | 0 perdidas de 1600 (0.000 %) |
| seno_rapido_01 | timestamps monótonos (con desborde de micros) | OK | 0 no crecientes |
| seno_rapido_01 | fs real dentro de ±2 % | OK | 100.000 Hz (nominal 100) |
| seno_rapido_01 | jitter de Δt < 1000 µs | OK | σ(Δt) = 29.5 µs |
| seno_rapido_01 | desfase IMU2−IMU1 entre 0 y 5 ms | OK | media 410 µs |
| seno_rapido_01 | duración | OK | 16.0 s |
| seno_rapido_01 | sin saturación (|cuentas| < 32760) | OK | ninguna |
| seno_rapido_01 | ninguna IMU congelada (σ > 0 en cada canal) | OK | todos varían |
| seno_rapido_01 | un solo perfil y fases 0→1→2 en orden | OK | perfiles {np.int64(3)}, fases [np.int64(0), np.int64(1), np.int64(2)] |
| seno_rapido_01 | el brazo medido sigue a la consigna | OK | amplitud medida/consigna = 0.98, 0.95 |
| escalones_02 | existe el JSON de configuración | OK | escalones_02.json |
| escalones_02 | columnas esperadas | OK | 19 columnas |
| escalones_02 | sin valores vacíos (NaN) | OK | 0 vacíos |
| escalones_02 | valores enteros (cuentas crudas) | OK | int |
| escalones_02 | seq creciente | OK | 0 retrocesos |
| escalones_02 | muestras perdidas (huecos en seq) | AVISO | 1 perdidas de 2600 (0.038 %) |
| escalones_02 | timestamps monótonos (con desborde de micros) | OK | 0 no crecientes |
| escalones_02 | fs real dentro de ±2 % | OK | 100.000 Hz (nominal 100) |
| escalones_02 | jitter de Δt < 1000 µs | OK | σ(Δt) = 28.9 µs |
| escalones_02 | desfase IMU2−IMU1 entre 0 y 5 ms | OK | media 410 µs |
| escalones_02 | duración | OK | 26.0 s |
| escalones_02 | sin saturación (|cuentas| < 32760) | OK | ninguna |
| escalones_02 | ninguna IMU congelada (σ > 0 en cada canal) | OK | todos varían |
| escalones_02 | un solo perfil y fases 0→1→2 en orden | OK | perfiles {np.int64(1)}, fases [np.int64(0), np.int64(1), np.int64(2)] |
| escalones_02 | el brazo medido sigue a la consigna | OK | amplitud medida/consigna = 1.00, 0.99 |
| seno_lento_02 | existe el JSON de configuración | OK | seno_lento_02.json |
| seno_lento_02 | columnas esperadas | OK | 19 columnas |
| seno_lento_02 | sin valores vacíos (NaN) | OK | 0 vacíos |
| seno_lento_02 | valores enteros (cuentas crudas) | OK | int |
| seno_lento_02 | seq creciente | OK | 0 retrocesos |
| seno_lento_02 | muestras perdidas (huecos en seq) | AVISO | 3 perdidas de 2600 (0.115 %) |
| seno_lento_02 | timestamps monótonos (con desborde de micros) | OK | 0 no crecientes |
| seno_lento_02 | fs real dentro de ±2 % | OK | 100.000 Hz (nominal 100) |
| seno_lento_02 | jitter de Δt < 1000 µs | OK | σ(Δt) = 29.3 µs |
| seno_lento_02 | desfase IMU2−IMU1 entre 0 y 5 ms | OK | media 410 µs |
| seno_lento_02 | duración | OK | 26.0 s |
| seno_lento_02 | sin saturación (|cuentas| < 32760) | OK | ninguna |
| seno_lento_02 | ninguna IMU congelada (σ > 0 en cada canal) | OK | todos varían |
| seno_lento_02 | un solo perfil y fases 0→1→2 en orden | OK | perfiles {np.int64(2)}, fases [np.int64(0), np.int64(1), np.int64(2)] |
| seno_lento_02 | el brazo medido sigue a la consigna | OK | amplitud medida/consigna = 0.99, 0.99 |
| seno_rapido_02 | existe el JSON de configuración | OK | seno_rapido_02.json |
| seno_rapido_02 | columnas esperadas | OK | 19 columnas |
| seno_rapido_02 | sin valores vacíos (NaN) | OK | 0 vacíos |
| seno_rapido_02 | valores enteros (cuentas crudas) | OK | int |
| seno_rapido_02 | seq creciente | OK | 0 retrocesos |
| seno_rapido_02 | muestras perdidas (huecos en seq) | OK | 0 perdidas de 1600 (0.000 %) |
| seno_rapido_02 | timestamps monótonos (con desborde de micros) | OK | 0 no crecientes |
| seno_rapido_02 | fs real dentro de ±2 % | OK | 100.000 Hz (nominal 100) |
| seno_rapido_02 | jitter de Δt < 1000 µs | OK | σ(Δt) = 27.9 µs |
| seno_rapido_02 | desfase IMU2−IMU1 entre 0 y 5 ms | OK | media 410 µs |
| seno_rapido_02 | duración | OK | 16.0 s |
| seno_rapido_02 | sin saturación (|cuentas| < 32760) | OK | ninguna |
| seno_rapido_02 | ninguna IMU congelada (σ > 0 en cada canal) | OK | todos varían |
| seno_rapido_02 | un solo perfil y fases 0→1→2 en orden | OK | perfiles {np.int64(3)}, fases [np.int64(0), np.int64(1), np.int64(2)] |
| seno_rapido_02 | el brazo medido sigue a la consigna | OK | amplitud medida/consigna = 0.98, 0.95 |

Resumen: {'OK': 99, 'AVISO': 5}. Generado por código · commit 54720e5+cambios_sin_commit · manifiesto datos/sinteticos/manifiesto.json
