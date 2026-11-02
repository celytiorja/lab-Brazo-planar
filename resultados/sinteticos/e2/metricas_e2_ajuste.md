# Métricas con registros de AJUSTE

| archivo | metodo | eslabon | ruido_omega_reposo_dps | retraso_omega_ms | retraso_theta_ms | error_estacionario_rms_deg | deriva_final_deg | ruido_alfa_reposo_dps2 | t_calculo_us | rmse_vs_verdad_deg |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| escalones_01 | Integración directa | 1 | 0.05851 | 0 | 0 | 0.6587 | 0.01602 | 8.449 | 6.039 | 0.7714 |
| escalones_01 | Integración directa | 2 | 0.05639 | 0 | 0 | 0.8674 | -1.433 | 7.863 | 6.039 | 0.9241 |
| escalones_01 | Media móvil N=5 + Euler | 1 | 0.02618 | 20.01 | 19.27 | 0.6586 | 0.006762 | 1.636 | 13.52 | 0.8981 |
| escalones_01 | Media móvil N=5 + Euler | 2 | 0.02524 | 20.01 | 19.82 | 0.8612 | -1.425 | 1.629 | 13.52 | 1.042 |
| escalones_01 | Media móvil N=21 + Euler | 1 | 0.01291 | 100 | 98.97 | 0.6581 | 0.001291 | 0.3978 | 17.81 | 3.815 |
| escalones_01 | Media móvil N=21 + Euler | 2 | 0.01324 | 100 | 99.79 | 0.8583 | -1.426 | 0.39 | 17.81 | 4.081 |
| escalones_01 | Kalman Q_baja | 1 | 0.01252 | 51.39 | 2.184 | 0.6584 | -7.502e-05 | 0.5329 | 108.8 | 0.7026 |
| escalones_01 | Kalman Q_baja | 2 | 0.013 | 54.74 | 2.618 | 0.8623 | -1.434 | 0.5204 | 108.8 | 0.8604 |
| escalones_01 | Kalman Q_media | 1 | 0.02304 | 17.36 | 3.574 | 0.6598 | 0.0005812 | 1.68 | 101.1 | 0.6882 |
| escalones_01 | Kalman Q_media | 2 | 0.0226 | 17.94 | 4.098 | 0.8636 | -1.435 | 1.641 | 101.1 | 0.8488 |
| escalones_01 | Kalman Q_alta | 1 | 0.03827 | 3.524 | 4.199 | 0.6588 | 0.0044 | 4.292 | 102.9 | 0.681 |
| escalones_01 | Kalman Q_alta | 2 | 0.0378 | 3.496 | 4.666 | 0.864 | -1.433 | 4.127 | 102.9 | 0.8447 |
| seno_lento_01 | Integración directa | 1 | 0.0633 | 0 | 0 | 0.09885 | 0.07922 | 8.622 | 3.423 | 0.1954 |
| seno_lento_01 | Integración directa | 2 | 0.06151 | 0 | 0 | 0.07774 | 0.1122 | 8.818 | 3.423 | 0.5167 |
| seno_lento_01 | Media móvil N=5 + Euler | 1 | 0.03039 | 5.186 | 17.56 | 0.1175 | 0.08342 | 1.651 | 11.7 | 0.3488 |
| seno_lento_01 | Media móvil N=5 + Euler | 2 | 0.02711 | 3.774 | 19.6 | 0.05327 | 0.05901 | 1.784 | 11.7 | 0.7185 |
| seno_lento_01 | Media móvil N=21 + Euler | 1 | 0.01487 | 74.92 | 98.33 | 0.1345 | -0.03691 | 0.4229 | 16.4 | 2.218 |
| seno_lento_01 | Media móvil N=21 + Euler | 2 | 0.01807 | 73.75 | 99.3 | 0.04386 | -0.2779 | 0.4855 | 16.4 | 3.398 |
| seno_lento_01 | Kalman Q_baja | 1 | 0.08403 | 62.74 | 3.134 | 0.1075 | 0.07991 | 0.9976 | 112.9 | 0.141 |
| seno_lento_01 | Kalman Q_baja | 2 | 0.183 | 68.51 | 4.329 | 0.09785 | 0.1242 | 1.916 | 112.9 | 0.515 |
| seno_lento_01 | Kalman Q_media | 1 | 0.02698 | 2.861 | 3.212 | 0.1052 | 0.08143 | 1.782 | 118.9 | 0.1316 |
| seno_lento_01 | Kalman Q_media | 2 | 0.0238 | 2.795 | 4.534 | 0.07964 | 0.1087 | 1.804 | 118.9 | 0.4948 |
| seno_lento_01 | Kalman Q_alta | 1 | 0.04294 | 1.253 | 3.255 | 0.1135 | 0.09323 | 4.489 | 136.6 | 0.1312 |
| seno_lento_01 | Kalman Q_alta | 2 | 0.04057 | 1.016 | 4.575 | 0.07555 | 0.1172 | 4.554 | 136.6 | 0.49 |
| seno_rapido_01 | Integración directa | 1 | 0.05649 | 0 | 0 | 0.1936 | 0.1441 | 8.551 | 3.586 | 0.4181 |
| seno_rapido_01 | Integración directa | 2 | 0.05771 | 0 | 0 | 0.3385 | -0.4378 | 8.3 | 3.586 | 0.6848 |
| seno_rapido_01 | Media móvil N=5 + Euler | 1 | 0.02281 | 14.36 | 19.74 | 0.1958 | 0.1032 | 1.631 | 11.63 | 0.8274 |
| seno_rapido_01 | Media móvil N=5 + Euler | 2 | 0.0262 | 14.05 | 19.68 | 0.3391 | -0.542 | 1.622 | 11.63 | 1.274 |
| seno_rapido_01 | Media móvil N=21 + Euler | 1 | 0.0172 | 94 | 98.58 | 0.1939 | -0.2155 | 0.4562 | 15.42 | 4.917 |
| seno_rapido_01 | Media móvil N=21 + Euler | 2 | 0.02916 | 95.02 | 98.4 | 0.3395 | -1.293 | 0.6801 | 15.42 | 7.06 |
| seno_rapido_01 | Kalman Q_baja | 1 | 0.1819 | 89.93 | 4.088 | 0.1954 | 0.1257 | 1.824 | 96.74 | 0.3274 |
| seno_rapido_01 | Kalman Q_baja | 2 | 0.3689 | 83.97 | 3.578 | 0.3391 | -0.4822 | 3.644 | 96.74 | 0.5933 |
| seno_rapido_01 | Kalman Q_media | 1 | 0.01985 | 19.52 | 4.726 | 0.1959 | 0.1338 | 1.658 | 113.2 | 0.3079 |
| seno_rapido_01 | Kalman Q_media | 2 | 0.02363 | 19.83 | 4.675 | 0.3391 | -0.4675 | 1.679 | 113.2 | 0.5634 |
| seno_rapido_01 | Kalman Q_alta | 1 | 0.03538 | 2.055 | 4.802 | 0.196 | 0.1367 | 4.272 | 94.76 | 0.3052 |
| seno_rapido_01 | Kalman Q_alta | 2 | 0.03811 | 2.243 | 4.805 | 0.3393 | -0.4611 | 4.272 | 94.76 | 0.5602 |

Generado por código · commit 54720e5+cambios_sin_commit · manifiesto datos/sinteticos/manifiesto.json
