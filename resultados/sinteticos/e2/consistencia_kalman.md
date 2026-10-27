# Consistencia del filtro (innovaciones y covarianza)

| archivo | metodo | nis_medio | nis_esperado | nis_medio_reposo | nis_medio_movimiento | frac_nis_en_95 | autocorr_innov_lag1 | banda_blancura_95 | max_asimetria_P | min_autovalor_P |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| escalones_01 | Kalman Q_baja | 8.53e+05 | 2 | 1.707 | 1.082e+06 | 0.6351 | 0.8952 | 0.03845 | 6.776e-20 | 0.0003198 |
| escalones_01 | Kalman Q_media | 3.253e+05 | 2 | 1.508 | 4.124e+05 | 0.7725 | 0.766 | 0.03845 | 5.929e-20 | 0.0009564 |
| escalones_01 | Kalman Q_alta | 9.107e+04 | 2 | 1.004 | 1.155e+05 | 0.8075 | 0.4663 | 0.03845 | 7.115e-20 | 0.002156 |
| seno_lento_01 | Kalman Q_baja | 3.773e+04 | 2 | 12.48 | 4.664e+04 | 0.188 | 0.5247 | 0.03847 | 6.099e-20 | 0.0003198 |
| seno_lento_01 | Kalman Q_media | 1.464e+04 | 2 | 1.718 | 1.81e+04 | 0.203 | -0.01076 | 0.03847 | 5.76e-20 | 0.0009562 |
| seno_lento_01 | Kalman Q_alta | 8562 | 2 | 1.128 | 1.058e+04 | 0.2076 | -0.2964 | 0.03847 | 8.132e-20 | 0.002157 |
| seno_rapido_01 | Kalman Q_baja | 6.521e+05 | 2 | 43.99 | 9.478e+05 | 0.3083 | 0.9782 | 0.04902 | 6.099e-20 | 0.0003198 |
| seno_rapido_01 | Kalman Q_media | 8.65e+04 | 2 | 1.509 | 1.257e+05 | 0.3308 | 0.8517 | 0.04902 | 4.743e-20 | 0.0009563 |
| seno_rapido_01 | Kalman Q_alta | 1.418e+04 | 2 | 1.026 | 2.061e+04 | 0.3358 | 0.4199 | 0.04902 | 2.88e-20 | 0.002156 |

NIS = yᵀS⁻¹y ~ χ²(2) si el modelo es correcto: media ≈ 2 y ~95 % de las muestras dentro de la banda. autocorr_innov_lag1 ≈ 0 si las innovaciones son blancas. P debe ser simétrica (asimetría ≈ 0) y positiva (autovalor mínimo > 0).

Generado por código · commit 379fa91+cambios_sin_commit · manifiesto datos/sinteticos/manifiesto.json
