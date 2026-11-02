# Métricas con registros de AJUSTE

| archivo | metodo | eslabon | ruido_omega_reposo_dps | retraso_omega_ms | retraso_theta_ms | error_estacionario_rms_deg | deriva_final_deg | ruido_alfa_reposo_dps2 | t_calculo_us |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| escalones_01 | Integración directa | 1 | 0.3625 | 0 | 0 | 5.759 | 6.004 | 27.11 | 3.595 |
| escalones_01 | Integración directa | 2 | 0.4219 | 0 | 0 | 4.425 | 7.698 | 36.29 | 3.595 |
| escalones_01 | Media móvil N=5 + Euler | 1 | 0.2482 | 20 | 19.2 | 5.758 | 6.002 | 10.37 | 13.52 |
| escalones_01 | Media móvil N=5 + Euler | 2 | 0.272 | 20 | 19.81 | 4.425 | 7.697 | 12.03 | 13.52 |
| escalones_01 | Media móvil N=21 + Euler | 1 | 0.1162 | 100 | 98.95 | 5.763 | 5.995 | 2.512 | 22.43 |
| escalones_01 | Media móvil N=21 + Euler | 2 | 0.1202 | 100 | 99.72 | 4.421 | 7.691 | 2.887 | 22.43 |
| escalones_01 | Kalman Q_baja | 1 | 0.1182 | 58.32 | 2.565 | 5.762 | 6.004 | 3.385 | 114.5 |
| escalones_01 | Kalman Q_baja | 2 | 0.1178 | 58.1 | 2.192 | 4.429 | 7.699 | 3.666 | 114.5 |
| escalones_01 | Kalman Q_media | 1 | 0.213 | 20.59 | 3.887 | 5.759 | 6.004 | 9.692 | 96.89 |
| escalones_01 | Kalman Q_media | 2 | 0.2238 | 19.64 | 3.721 | 4.425 | 7.698 | 10.84 | 96.89 |
| escalones_01 | Kalman Q_alta | 1 | 0.3089 | 4.945 | 4.265 | 5.759 | 6.003 | 19.43 | 120.8 |
| escalones_01 | Kalman Q_alta | 2 | 0.3415 | 4.372 | 4.542 | 4.425 | 7.698 | 23.29 | 120.8 |
| seno_lento_01 | Integración directa | 1 | 1.103 | 0 | 0 | 0.2648 | -0.1226 | 55.55 | 3.958 |
| seno_lento_01 | Integración directa | 2 | 1.29 | 0 | 0 | 0.8032 | -1.022 | 63.21 | 3.958 |
| seno_lento_01 | Media móvil N=5 + Euler | 1 | 0.9036 | 19.67 | 18.16 | 0.2609 | -0.1355 | 31.33 | 14.68 |
| seno_lento_01 | Media móvil N=5 + Euler | 2 | 1.073 | 19.99 | 19.26 | 0.8027 | -0.9965 | 35.99 | 14.68 |
| seno_lento_01 | Media móvil N=21 + Euler | 1 | 0.5074 | 85.83 | 98.23 | 0.2498 | -0.2585 | 7.39 | 23.08 |
| seno_lento_01 | Media móvil N=21 + Euler | 2 | 0.6104 | 100.2 | 98.12 | 0.8008 | -0.8847 | 8.68 | 23.08 |
| seno_lento_01 | Kalman Q_baja | 1 | 0.5141 | 32.11 | 2.913 | 0.2637 | -0.1314 | 9.696 | 110 |
| seno_lento_01 | Kalman Q_baja | 2 | 0.5833 | 34.1 | 3.091 | 0.8028 | -1.015 | 10.44 | 110 |
| seno_lento_01 | Kalman Q_media | 1 | 0.786 | 15.21 | 3.277 | 0.2636 | -0.1269 | 25.53 | 101.5 |
| seno_lento_01 | Kalman Q_media | 2 | 0.9119 | 16.31 | 3.676 | 0.803 | -1.015 | 27.63 | 101.5 |
| seno_lento_01 | Kalman Q_alta | 1 | 1.012 | 4.624 | 3.529 | 0.2637 | -0.1256 | 44.78 | 140.4 |
| seno_lento_01 | Kalman Q_alta | 2 | 1.178 | 5.084 | 4.247 | 0.803 | -1.016 | 49.48 | 140.4 |
| seno_rapido_01 | Integración directa | 1 | 0.04644 | 0 | 0 | 0.6475 | -1.078 | 4.895 | 6.567 |
| seno_rapido_01 | Integración directa | 2 | 0.05404 | 0 | 0 | 3.816 | 4.146 | 6.477 | 6.567 |
| seno_rapido_01 | Media móvil N=5 + Euler | 1 | 0.03092 | 18.83 | 18.92 | 0.6477 | -1.156 | 1.409 | 20.97 |
| seno_rapido_01 | Media móvil N=5 + Euler | 2 | 0.03162 | 19.86 | 17.43 | 3.816 | 4.179 | 1.79 | 20.97 |
| seno_rapido_01 | Media móvil N=21 + Euler | 1 | 0.0171 | 94.41 | 97.12 | 0.6484 | -1.589 | 0.5238 | 27.61 |
| seno_rapido_01 | Media móvil N=21 + Euler | 2 | 0.02001 | 95.37 | 96.89 | 3.816 | 4.224 | 0.6875 | 27.61 |
| seno_rapido_01 | Kalman Q_baja | 1 | 0.1797 | 76.92 | 3.584 | 0.6478 | -1.105 | 1.93 | 128.3 |
| seno_rapido_01 | Kalman Q_baja | 2 | 0.06669 | 72.24 | 2.26 | 3.817 | 4.145 | 0.7456 | 128.3 |
| seno_rapido_01 | Kalman Q_media | 1 | 0.02708 | 14.8 | 4.157 | 0.6476 | -1.099 | 1.248 | 105.1 |
| seno_rapido_01 | Kalman Q_media | 2 | 0.02652 | 18.96 | 3.205 | 3.816 | 4.153 | 1.425 | 105.1 |
| seno_rapido_01 | Kalman Q_alta | 1 | 0.03725 | 3.998 | 4.289 | 0.6476 | -1.097 | 2.846 | 94.42 |
| seno_rapido_01 | Kalman Q_alta | 2 | 0.03941 | 5.01 | 3.527 | 3.816 | 4.154 | 3.476 | 94.42 |

Generado por código · commit 54720e5+cambios_sin_commit · manifiesto datos/crudos/manifiesto.json
