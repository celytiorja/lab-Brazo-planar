# VALIDACIÓN final (Q elegida: Q_media)

| archivo | metodo | eslabon | ruido_omega_reposo_dps | retraso_omega_ms | retraso_theta_ms | error_estacionario_rms_deg | deriva_final_deg | ruido_alfa_reposo_dps2 | t_calculo_us | rmse_vs_verdad_deg |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| escalones_02 | Integración directa | 1 | 0.06098 | 0 | 0 | 0.6145 | 0.1602 | 8.44 | 4.847 | 0.731 |
| escalones_02 | Integración directa | 2 | 0.05842 | 0 | 0 | 0.9006 | -1.386 | 8.074 | 4.847 | 0.9554 |
| escalones_02 | Media móvil N=5 + Euler | 1 | 0.03036 | 20.01 | 19.27 | 0.6105 | 0.1711 | 1.754 | 16.17 | 0.8548 |
| escalones_02 | Media móvil N=5 + Euler | 2 | 0.028 | 20.01 | 19.81 | 0.8954 | -1.363 | 1.668 | 16.17 | 1.065 |
| escalones_02 | Media móvil N=21 + Euler | 1 | 0.01601 | 100 | 98.95 | 0.6091 | 0.1664 | 0.4061 | 17.99 | 3.733 |
| escalones_02 | Media móvil N=21 + Euler | 2 | 0.01481 | 100 | 99.77 | 0.8898 | -1.358 | 0.4002 | 17.99 | 4.01 |
| escalones_02 | Kalman Q_media | 1 | 0.02642 | 17.35 | 3.568 | 0.6116 | 0.1655 | 1.727 | 48.11 | 0.6419 |
| escalones_02 | Kalman Q_media | 2 | 0.02499 | 17.95 | 4.085 | 0.8929 | -1.363 | 1.679 | 48.11 | 0.8812 |
| seno_lento_02 | Integración directa | 1 | 0.05903 | 0 | 0 | 0.1845 | 0.2206 | 8.177 | 4.006 | 0.2357 |
| seno_lento_02 | Integración directa | 2 | 0.06097 | 0 | 0 | 0.01991 | 0.18 | 8.745 | 4.006 | 0.4496 |
| seno_lento_02 | Media móvil N=5 + Euler | 1 | 0.02638 | 5.192 | 17.46 | 0.1364 | 0.1346 | 1.64 | 11.12 | 0.3427 |
| seno_lento_02 | Media móvil N=5 + Euler | 2 | 0.02729 | 3.771 | 19.62 | 0.006232 | 0.03436 | 1.661 | 11.12 | 0.6779 |
| seno_lento_02 | Media móvil N=21 + Euler | 1 | 0.01316 | 74.58 | 98.21 | 0.1902 | 0.07371 | 0.4092 | 15 | 2.172 |
| seno_lento_02 | Media móvil N=21 + Euler | 2 | 0.02133 | 73.49 | 99.48 | 0.1502 | -0.4448 | 0.4953 | 15 | 3.325 |
| seno_lento_02 | Kalman Q_media | 1 | 0.02318 | 2.87 | 3.167 | 0.1324 | 0.1411 | 1.7 | 56.89 | 0.1475 |
| seno_lento_02 | Kalman Q_media | 2 | 0.02471 | 2.8 | 4.529 | 0.03034 | 0.1071 | 1.78 | 56.89 | 0.4374 |
| seno_rapido_02 | Integración directa | 1 | 0.05702 | 0 | 0 | 0.01821 | -0.1323 | 8.131 | 2.763 | 0.4069 |
| seno_rapido_02 | Integración directa | 2 | 0.06213 | 0 | 0 | 0.175 | -0.5268 | 8.741 | 2.763 | 0.6035 |
| seno_rapido_02 | Media móvil N=5 + Euler | 1 | 0.02578 | 14.46 | 19.73 | 0.01952 | -0.1782 | 1.636 | 9.436 | 0.8019 |
| seno_rapido_02 | Media móvil N=5 + Euler | 2 | 0.02794 | 14.02 | 19.68 | 0.1719 | -0.6315 | 1.766 | 9.436 | 1.207 |
| seno_rapido_02 | Media móvil N=21 + Euler | 1 | 0.02115 | 94.11 | 98.58 | 0.01913 | -0.4965 | 0.4807 | 12.31 | 4.761 |
| seno_rapido_02 | Media móvil N=21 + Euler | 2 | 0.035 | 95.04 | 98.39 | 0.1716 | -1.382 | 0.7856 | 12.31 | 6.833 |
| seno_rapido_02 | Kalman Q_media | 1 | 0.02302 | 19.52 | 4.72 | 0.02004 | -0.1484 | 1.638 | 43.27 | 0.3012 |
| seno_rapido_02 | Kalman Q_media | 2 | 0.02511 | 19.81 | 4.674 | 0.1725 | -0.5581 | 1.814 | 43.27 | 0.4756 |

Generado por código · commit 379fa91+cambios_sin_commit · manifiesto datos/sinteticos/manifiesto.json
