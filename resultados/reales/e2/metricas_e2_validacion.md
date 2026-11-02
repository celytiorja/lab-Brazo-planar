# VALIDACIÓN final (Q elegida: Q_media)

| archivo | metodo | eslabon | ruido_omega_reposo_dps | retraso_omega_ms | retraso_theta_ms | error_estacionario_rms_deg | deriva_final_deg | ruido_alfa_reposo_dps2 | t_calculo_us |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| escalones_03 | Integración directa | 1 | 0.1876 | 0 | 0 | 1.536 | 1.325 | 11.56 | 6.319 |
| escalones_03 | Integración directa | 2 | 0.1959 | 0 | 0 | 4.152 | 0.9675 | 14.44 | 6.319 |
| escalones_03 | Media móvil N=5 + Euler | 1 | 0.1499 | 20 | 19.06 | 1.542 | 1.324 | 5.008 | 20.31 |
| escalones_03 | Media móvil N=5 + Euler | 2 | 0.1492 | 20 | 19.72 | 4.152 | 0.9674 | 5.247 | 20.31 |
| escalones_03 | Media móvil N=21 + Euler | 1 | 0.08352 | 100 | 98.77 | 1.546 | 1.323 | 1.054 | 19.99 |
| escalones_03 | Media móvil N=21 + Euler | 2 | 0.08168 | 100 | 99.56 | 4.141 | 0.9671 | 1.096 | 19.99 |
| escalones_03 | Kalman Q_media | 1 | 0.133 | 20.33 | 3.795 | 1.537 | 1.324 | 4.366 | 84.76 |
| escalones_03 | Kalman Q_media | 2 | 0.1287 | 18.61 | 3.474 | 4.151 | 0.9675 | 4.467 | 84.76 |
| seno_lento_02 | Integración directa | 1 | 0.03564 | 0 | 0 | 0.4114 | -0.6302 | 4.557 | 6.088 |
| seno_lento_02 | Integración directa | 2 | 0.04478 | 0 | 0 | 1.871 | 1.861 | 6.286 | 6.088 |
| seno_lento_02 | Media móvil N=5 + Euler | 1 | 0.01804 | 19.83 | 18.8 | 0.4116 | -0.6656 | 1.125 | 13.06 |
| seno_lento_02 | Media móvil N=5 + Euler | 2 | 0.01866 | 19.97 | 19.49 | 1.871 | 1.869 | 1.353 | 13.06 |
| seno_lento_02 | Media móvil N=21 + Euler | 1 | 0.008307 | 96.98 | 98.65 | 0.4119 | -0.8603 | 0.2327 | 15.01 |
| seno_lento_02 | Media móvil N=21 + Euler | 2 | 0.00916 | 98.76 | 97.81 | 1.871 | 1.944 | 0.2956 | 15.01 |
| seno_lento_02 | Kalman Q_media | 1 | 0.01571 | 14.89 | 3.637 | 0.4114 | -0.6398 | 1.06 | 62.43 |
| seno_lento_02 | Kalman Q_media | 2 | 0.01636 | 15.98 | 3.709 | 1.871 | 1.864 | 1.262 | 62.43 |
| seno_rapido_02 | Integración directa | 1 | 0.1794 | 0 | 0 | 0.06618 | -0.1038 | 14.62 | 3.454 |
| seno_rapido_02 | Integración directa | 2 | 0.2025 | 0 | 0 | 3.076 | 3.945 | 20.5 | 3.454 |
| seno_rapido_02 | Media móvil N=5 + Euler | 1 | 0.1435 | 18.5 | 19.28 | 0.06718 | -0.1702 | 3.95 | 11.93 |
| seno_rapido_02 | Media móvil N=5 + Euler | 2 | 0.1469 | 19.83 | 19 | 3.076 | 3.945 | 4.884 | 11.93 |
| seno_rapido_02 | Media móvil N=21 + Euler | 1 | 0.1075 | 95.3 | 97.43 | 0.06976 | -0.5655 | 1.239 | 15.01 |
| seno_rapido_02 | Media móvil N=21 + Euler | 2 | 0.1101 | 98.31 | 96.51 | 3.077 | 3.968 | 1.407 | 15.01 |
| seno_rapido_02 | Kalman Q_media | 1 | 0.1349 | 14.82 | 4.375 | 0.06636 | -0.1224 | 3.904 | 59.11 |
| seno_rapido_02 | Kalman Q_media | 2 | 0.1363 | 19.33 | 3.926 | 3.076 | 3.946 | 4.532 | 59.11 |

Generado por código · commit 54720e5+cambios_sin_commit · manifiesto datos/crudos/manifiesto.json
