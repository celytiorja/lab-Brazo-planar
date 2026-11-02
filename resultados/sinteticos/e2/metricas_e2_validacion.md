# VALIDACIÓN final (Q elegida: Q_media)

| archivo | metodo | eslabon | ruido_omega_reposo_dps | retraso_omega_ms | retraso_theta_ms | error_estacionario_rms_deg | deriva_final_deg | ruido_alfa_reposo_dps2 | t_calculo_us | rmse_vs_verdad_deg |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| escalones_02 | Integración directa | 1 | 0.06168 | 0 | 0 | 0.6477 | 0.04413 | 8.574 | 3.243 | 0.7616 |
| escalones_02 | Integración directa | 2 | 0.05824 | 0 | 0 | 0.8863 | -1.429 | 8.137 | 3.243 | 0.942 |
| escalones_02 | Media móvil N=5 + Euler | 1 | 0.03056 | 20.01 | 19.27 | 0.6426 | 0.05515 | 1.795 | 11.43 | 0.8853 |
| escalones_02 | Media móvil N=5 + Euler | 2 | 0.02729 | 20.01 | 19.81 | 0.8811 | -1.406 | 1.675 | 11.43 | 1.058 |
| escalones_02 | Media móvil N=21 + Euler | 1 | 0.01454 | 100 | 98.95 | 0.6414 | 0.05084 | 0.41 | 14.37 | 3.811 |
| escalones_02 | Media móvil N=21 + Euler | 2 | 0.01339 | 100 | 99.77 | 0.8766 | -1.401 | 0.3977 | 14.37 | 4.082 |
| escalones_02 | Kalman Q_media | 1 | 0.02618 | 17.35 | 3.568 | 0.644 | 0.0495 | 1.755 | 56.3 | 0.6722 |
| escalones_02 | Kalman Q_media | 2 | 0.0241 | 17.95 | 4.085 | 0.8786 | -1.406 | 1.685 | 56.3 | 0.864 |
| seno_lento_02 | Integración directa | 1 | 0.05898 | 0 | 0 | 0.1779 | 0.1812 | 8.147 | 3.289 | 0.2284 |
| seno_lento_02 | Integración directa | 2 | 0.05985 | 0 | 0 | 0.04855 | 0.1786 | 8.581 | 3.289 | 0.4719 |
| seno_lento_02 | Media móvil N=5 + Euler | 1 | 0.02635 | 5.192 | 17.46 | 0.1239 | 0.09524 | 1.602 | 11.33 | 0.3446 |
| seno_lento_02 | Media móvil N=5 + Euler | 2 | 0.02757 | 3.772 | 19.62 | 0.02379 | 0.03294 | 1.619 | 11.33 | 0.6997 |
| seno_lento_02 | Media móvil N=21 + Euler | 1 | 0.0138 | 74.58 | 98.21 | 0.186 | 0.0346 | 0.4167 | 14.4 | 2.214 |
| seno_lento_02 | Media móvil N=21 + Euler | 2 | 0.02316 | 73.49 | 99.49 | 0.1459 | -0.4462 | 0.5048 | 14.4 | 3.392 |
| seno_lento_02 | Kalman Q_media | 1 | 0.02339 | 2.87 | 3.167 | 0.1195 | 0.1017 | 1.695 | 56.68 | 0.1391 |
| seno_lento_02 | Kalman Q_media | 2 | 0.02505 | 2.801 | 4.529 | 0.06021 | 0.1056 | 1.738 | 56.68 | 0.4602 |
| seno_rapido_02 | Integración directa | 1 | 0.05764 | 0 | 0 | 0.009551 | -0.1174 | 8.175 | 3.246 | 0.4181 |
| seno_rapido_02 | Integración directa | 2 | 0.06297 | 0 | 0 | 0.1864 | -0.4973 | 8.813 | 3.246 | 0.6194 |
| seno_rapido_02 | Media móvil N=5 + Euler | 1 | 0.02635 | 14.46 | 19.73 | 0.01077 | -0.1635 | 1.648 | 11.52 | 0.827 |
| seno_rapido_02 | Media móvil N=5 + Euler | 2 | 0.02806 | 14.02 | 19.68 | 0.1835 | -0.602 | 1.768 | 11.52 | 1.245 |
| seno_rapido_02 | Media móvil N=21 + Euler | 1 | 0.0228 | 94.11 | 98.58 | 0.01062 | -0.4818 | 0.503 | 14.39 | 4.917 |
| seno_rapido_02 | Media móvil N=21 + Euler | 2 | 0.03884 | 95.04 | 98.39 | 0.185 | -1.353 | 0.8548 | 14.39 | 7.056 |
| seno_rapido_02 | Kalman Q_media | 1 | 0.02357 | 19.52 | 4.72 | 0.01147 | -0.1336 | 1.654 | 56.5 | 0.3081 |
| seno_rapido_02 | Kalman Q_media | 2 | 0.02564 | 19.81 | 4.674 | 0.1837 | -0.5286 | 1.837 | 56.5 | 0.4863 |

Generado por código · commit 54720e5+cambios_sin_commit · manifiesto datos/sinteticos/manifiesto.json
