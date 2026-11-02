# Consistencia del filtro (innovaciones y covarianza)

| archivo | metodo | nis_medio | nis_esperado | nis_medio_reposo | nis_medio_movimiento | frac_nis_en_95 | autocorr_innov_lag1 | banda_blancura_95 | max_asimetria_P | min_autovalor_P |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| escalones_01 | Kalman Q_baja | 8.875e+05 | 2 | 1.737 | 1.081e+06 | 0.6219 | 0.8952 | 0.03922 | 6.946e-20 | 0.0003198 |
| escalones_01 | Kalman Q_media | 3.384e+05 | 2 | 1.54 | 4.122e+05 | 0.7665 | 0.766 | 0.03922 | 4.743e-20 | 0.0009564 |
| escalones_01 | Kalman Q_alta | 9.475e+04 | 2 | 1.029 | 1.154e+05 | 0.8026 | 0.4663 | 0.03922 | 5.59e-20 | 0.002156 |
| seno_lento_01 | Kalman Q_baja | 3.926e+04 | 2 | 15.22 | 4.666e+04 | 0.1551 | 0.5247 | 0.03924 | 4.743e-20 | 0.0003198 |
| seno_lento_01 | Kalman Q_media | 1.524e+04 | 2 | 1.794 | 1.811e+04 | 0.1719 | -0.01076 | 0.03924 | 6.607e-20 | 0.0009562 |
| seno_lento_01 | Kalman Q_alta | 8908 | 2 | 1.187 | 1.059e+04 | 0.1784 | -0.2964 | 0.03924 | 8.47e-20 | 0.002157 |
| seno_rapido_01 | Kalman Q_baja | 6.956e+05 | 2 | 54.64 | 9.478e+05 | 0.2642 | 0.9782 | 0.05062 | 5.421e-20 | 0.0003198 |
| seno_rapido_01 | Kalman Q_media | 9.227e+04 | 2 | 1.548 | 1.257e+05 | 0.2875 | 0.8517 | 0.05062 | 2.711e-20 | 0.0009563 |
| seno_rapido_01 | Kalman Q_alta | 1.512e+04 | 2 | 1.057 | 2.061e+04 | 0.2942 | 0.4199 | 0.05062 | 3.558e-20 | 0.002156 |

NIS = yᵀS⁻¹y ~ χ²(2) si el modelo es correcto: media ≈ 2 y ~95 % de las muestras dentro de la banda. autocorr_innov_lag1 ≈ 0 si las innovaciones son blancas. P debe ser simétrica (asimetría ≈ 0) y positiva (autovalor mínimo > 0).

Generado por código · commit 54720e5+cambios_sin_commit · manifiesto datos/sinteticos/manifiesto.json
