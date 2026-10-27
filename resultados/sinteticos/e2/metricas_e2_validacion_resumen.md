# Validación: promedio de |métrica| sobre archivos y eslabones

| metodo | ruido_omega_reposo_dps | retraso_omega_ms | retraso_theta_ms | error_estacionario_rms_deg | deriva_final_deg | ruido_alfa_reposo_dps2 | t_calculo_us | rmse_vs_verdad_deg |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Integración directa | 0.05976 | 0 | 0 | 0.3188 | 0.4342 | 8.385 | 3.872 | 0.5637 |
| Kalman Q_media | 0.02457 | 13.38 | 4.124 | 0.3099 | 0.4139 | 1.723 | 49.43 | 0.4808 |
| Media móvil N=21 + Euler | 0.02024 | 89.55 | 98.9 | 0.3383 | 0.6536 | 0.4962 | 15.1 | 4.139 |
| Media móvil N=5 + Euler | 0.02763 | 12.91 | 19.26 | 0.3067 | 0.4188 | 1.688 | 12.24 | 0.825 |

Generado por código · commit 379fa91+cambios_sin_commit · manifiesto datos/sinteticos/manifiesto.json
