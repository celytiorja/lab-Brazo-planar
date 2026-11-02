# Consistencia del filtro (innovaciones y covarianza)

| archivo | metodo | nis_medio | nis_esperado | nis_medio_reposo | nis_medio_movimiento | frac_nis_en_95 | autocorr_innov_lag1 | banda_blancura_95 | max_asimetria_P | min_autovalor_P |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| escalones_01 | Kalman Q_baja | 2.481e+06 | 2 | 286.1 | 3.024e+06 | 0.3086 | 0.953 | 0.03922 | 1.186e-20 | 8.376e-05 |
| escalones_01 | Kalman Q_media | 8.181e+05 | 2 | 217 | 9.974e+05 | 0.4604 | 0.8896 | 0.03922 | 6.776e-21 | 0.0002497 |
| escalones_01 | Kalman Q_alta | 1.872e+05 | 2 | 98.27 | 2.282e+05 | 0.5929 | 0.7238 | 0.03922 | 3.388e-21 | 0.0005575 |
| seno_lento_01 | Kalman Q_baja | 5.358e+05 | 2 | 2332 | 6.365e+05 | 0.09284 | 0.9068 | 0.03921 | 1.186e-20 | 8.376e-05 |
| seno_lento_01 | Kalman Q_media | 2.832e+05 | 2 | 1452 | 3.364e+05 | 0.1269 | 0.8625 | 0.03921 | 6.776e-21 | 0.0002498 |
| seno_lento_01 | Kalman Q_alta | 7.802e+04 | 2 | 475.7 | 9.267e+04 | 0.1433 | 0.7779 | 0.03921 | 5.082e-21 | 0.0005582 |
| seno_rapido_01 | Kalman Q_baja | 2.528e+06 | 2 | 51.69 | 3.436e+06 | 0.2248 | 0.9647 | 0.05062 | 1.355e-20 | 8.376e-05 |
| seno_rapido_01 | Kalman Q_media | 6.405e+05 | 2 | 3.683 | 8.705e+05 | 0.2542 | 0.889 | 0.05062 | 6.776e-21 | 0.0002498 |
| seno_rapido_01 | Kalman Q_alta | 1.486e+05 | 2 | 2.156 | 2.019e+05 | 0.2809 | 0.7854 | 0.05062 | 5.082e-21 | 0.0005582 |

NIS = yᵀS⁻¹y ~ χ²(2) si el modelo es correcto: media ≈ 2 y ~95 % de las muestras dentro de la banda. autocorr_innov_lag1 ≈ 0 si las innovaciones son blancas. P debe ser simétrica (asimetría ≈ 0) y positiva (autovalor mínimo > 0).

Generado por código · commit 54720e5+cambios_sin_commit · manifiesto datos/crudos/manifiesto.json
