# Muestreo y alineación temporal

| archivo | muestras | duracion_s | fs_real_hz | dt_medio_ms | dt_desv_us | dt_min_ms | dt_max_ms | perdidas | desfase_imu2_imu1_us | llegada_pc_jitter_ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| estatico_03 | 4074 | 40.73 | 100 | 10 | 1.866e-09 | 10 | 10 | 0 | 520 | 101.6 |
| escalones_01 | 2499 | 24.98 | 100 | 10 | 4.018 | 9.94 | 10.06 | 0 | 535.6 | 78.46 |

Δt sale de los timestamps del ESP32 (micros()). desfase_imu2_imu1: la IMU2 se lee justo después de la IMU1 en cada muestra.
