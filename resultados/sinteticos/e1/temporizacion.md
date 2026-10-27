# Muestreo y alineación temporal

| archivo | muestras | duracion_s | fs_real_hz | dt_medio_ms | dt_desv_us | dt_min_ms | dt_max_ms | perdidas | desfase_imu2_imu1_us | llegada_pc_jitter_ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| estatico_01 | 3999 | 39.99 | 99.97 | 10 | 161.5 | 9.913 | 20.06 | 1 | 410.1 | 1.019 |
| escalones_01 | 2599 | 25.99 | 99.96 | 10 | 198.3 | 9.912 | 20.01 | 1 | 410.1 | 1.01 |

Δt sale de los timestamps del ESP32 (micros()). desfase_imu2_imu1: la IMU2 se lee justo después de la IMU1 en cada muestra.
