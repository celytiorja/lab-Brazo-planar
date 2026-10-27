# Métricas con registros de AJUSTE

| archivo | metodo | eslabon | ruido_omega_reposo_dps | retraso_omega_ms | retraso_theta_ms | error_estacionario_rms_deg | deriva_final_deg | ruido_alfa_reposo_dps2 | t_calculo_us | rmse_vs_verdad_deg |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| escalones_01 | Integración directa | 1 | 0.05865 | 0 | 0 | 0.641 | 0.02791 | 8.448 | 2.509 | 0.755 |
| escalones_01 | Integración directa | 2 | 0.0551 | 0 | 0 | 0.8071 | -1.339 | 7.597 | 2.509 | 0.8722 |
| escalones_01 | Media móvil N=5 + Euler | 1 | 0.02599 | 20.01 | 19.27 | 0.6412 | 0.01863 | 1.664 | 9.123 | 0.8796 |
| escalones_01 | Media móvil N=5 + Euler | 2 | 0.02545 | 20.01 | 19.82 | 0.8011 | -1.331 | 1.599 | 9.123 | 0.9922 |
| escalones_01 | Media móvil N=21 + Euler | 1 | 0.0124 | 100 | 98.96 | 0.641 | 0.01304 | 0.3969 | 12.13 | 3.74 |
| escalones_01 | Media móvil N=21 + Euler | 2 | 0.01303 | 100 | 99.79 | 0.7995 | -1.332 | 0.3831 | 12.13 | 3.994 |
| escalones_01 | Kalman Q_baja | 1 | 0.01213 | 51.39 | 2.184 | 0.6407 | 0.01181 | 0.5359 | 69.92 | 0.6875 |
| escalones_01 | Kalman Q_baja | 2 | 0.01267 | 54.74 | 2.618 | 0.8022 | -1.34 | 0.5086 | 69.92 | 0.8074 |
| escalones_01 | Kalman Q_media | 1 | 0.02277 | 17.36 | 3.574 | 0.6421 | 0.01247 | 1.689 | 64.75 | 0.6733 |
| escalones_01 | Kalman Q_media | 2 | 0.02255 | 17.94 | 4.098 | 0.8034 | -1.341 | 1.597 | 64.75 | 0.7954 |
| escalones_01 | Kalman Q_alta | 1 | 0.03831 | 3.524 | 4.199 | 0.6412 | 0.01628 | 4.308 | 69.34 | 0.6663 |
| escalones_01 | Kalman Q_alta | 2 | 0.03736 | 3.496 | 4.666 | 0.8038 | -1.339 | 4.003 | 69.34 | 0.7912 |
| seno_lento_01 | Integración directa | 1 | 0.06175 | 0 | 0 | 0.09191 | 0.08465 | 8.416 | 2.912 | 0.192 |
| seno_lento_01 | Integración directa | 2 | 0.06027 | 0 | 0 | 0.04268 | 0.07689 | 8.498 | 2.912 | 0.4916 |
| seno_lento_01 | Media móvil N=5 + Euler | 1 | 0.02949 | 5.186 | 17.56 | 0.1089 | 0.08884 | 1.632 | 8.93 | 0.3423 |
| seno_lento_01 | Media móvil N=5 + Euler | 2 | 0.027 | 3.774 | 19.6 | 0.02093 | 0.02372 | 1.74 | 8.93 | 0.6944 |
| seno_lento_01 | Media móvil N=21 + Euler | 1 | 0.01438 | 74.91 | 98.32 | 0.1255 | -0.03149 | 0.4159 | 11.69 | 2.175 |
| seno_lento_01 | Media móvil N=21 + Euler | 2 | 0.01688 | 73.75 | 99.3 | 0.01339 | -0.3129 | 0.4624 | 11.69 | 3.329 |
| seno_lento_01 | Kalman Q_baja | 1 | 0.07599 | 62.74 | 3.133 | 0.09968 | 0.08533 | 0.9224 | 64.59 | 0.139 |
| seno_lento_01 | Kalman Q_baja | 2 | 0.1647 | 68.51 | 4.329 | 0.06064 | 0.08888 | 1.735 | 64.59 | 0.4889 |
| seno_lento_01 | Kalman Q_media | 1 | 0.02614 | 2.861 | 3.212 | 0.09772 | 0.08686 | 1.742 | 66.79 | 0.1298 |
| seno_lento_01 | Kalman Q_media | 2 | 0.02356 | 2.795 | 4.534 | 0.04444 | 0.07339 | 1.767 | 66.79 | 0.4693 |
| seno_lento_01 | Kalman Q_alta | 1 | 0.04184 | 1.253 | 3.255 | 0.1051 | 0.09865 | 4.388 | 66.92 | 0.1296 |
| seno_lento_01 | Kalman Q_alta | 2 | 0.04019 | 1.016 | 4.574 | 0.04074 | 0.08188 | 4.427 | 66.92 | 0.4646 |
| seno_rapido_01 | Integración directa | 1 | 0.05635 | 0 | 0 | 0.1583 | 0.1211 | 8.4 | 2.622 | 0.4036 |
| seno_rapido_01 | Integración directa | 2 | 0.0566 | 0 | 0 | 0.3084 | -0.4674 | 8.16 | 2.622 | 0.6664 |
| seno_rapido_01 | Media móvil N=5 + Euler | 1 | 0.02409 | 14.36 | 19.74 | 0.1608 | 0.08022 | 1.627 | 8.998 | 0.8004 |
| seno_rapido_01 | Media móvil N=5 + Euler | 2 | 0.02527 | 14.05 | 19.68 | 0.3102 | -0.5717 | 1.581 | 8.998 | 1.236 |
| seno_rapido_01 | Media móvil N=21 + Euler | 1 | 0.01681 | 94 | 98.58 | 0.1602 | -0.2382 | 0.4433 | 11.61 | 4.761 |
| seno_rapido_01 | Media móvil N=21 + Euler | 2 | 0.02644 | 95.02 | 98.4 | 0.3105 | -1.323 | 0.63 | 11.61 | 6.836 |
| seno_rapido_01 | Kalman Q_baja | 1 | 0.1639 | 89.93 | 4.088 | 0.16 | 0.1027 | 1.655 | 63.93 | 0.3154 |
| seno_rapido_01 | Kalman Q_baja | 2 | 0.3316 | 83.97 | 3.578 | 0.3089 | -0.5119 | 3.283 | 63.93 | 0.5783 |
| seno_rapido_01 | Kalman Q_media | 1 | 0.02101 | 19.52 | 4.726 | 0.1604 | 0.1108 | 1.639 | 65.62 | 0.2964 |
| seno_rapido_01 | Kalman Q_media | 2 | 0.02274 | 19.83 | 4.675 | 0.309 | -0.4972 | 1.654 | 65.62 | 0.5495 |
| seno_rapido_01 | Kalman Q_alta | 1 | 0.03593 | 2.055 | 4.802 | 0.1605 | 0.1137 | 4.212 | 65.84 | 0.2937 |
| seno_rapido_01 | Kalman Q_alta | 2 | 0.03728 | 2.243 | 4.805 | 0.3094 | -0.4907 | 4.207 | 65.84 | 0.5467 |

Generado por código · commit 379fa91+cambios_sin_commit · manifiesto datos/sinteticos/manifiesto.json
