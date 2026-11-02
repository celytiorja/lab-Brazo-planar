# Validación: promedio de |métrica| sobre archivos y eslabones

| metodo | ruido_omega_reposo_dps | retraso_omega_ms | retraso_theta_ms | error_estacionario_rms_deg | deriva_final_deg | ruido_alfa_reposo_dps2 | t_calculo_us | rmse_vs_verdad_deg |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Integración directa | 0.05989 | 0 | 0 | 0.3261 | 0.4079 | 8.405 | 3.259 | 0.5736 |
| Kalman Q_media | 0.02466 | 13.38 | 4.124 | 0.3162 | 0.3876 | 1.727 | 56.49 | 0.4883 |
| Media móvil N=21 + Euler | 0.02109 | 89.55 | 98.9 | 0.3409 | 0.628 | 0.5145 | 14.39 | 4.246 |
| Media móvil N=5 + Euler | 0.0277 | 12.91 | 19.26 | 0.3109 | 0.3925 | 1.685 | 11.43 | 0.8433 |

Generado por código · commit 54720e5+cambios_sin_commit · manifiesto datos/sinteticos/manifiesto.json
