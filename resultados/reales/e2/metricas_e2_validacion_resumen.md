# Validación: promedio de |métrica| sobre archivos y eslabones

| metodo | ruido_omega_reposo_dps | retraso_omega_ms | retraso_theta_ms | error_estacionario_rms_deg | deriva_final_deg | ruido_alfa_reposo_dps2 | t_calculo_us |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Integración directa | 0.141 | 0 | 0 | 1.852 | 1.472 | 11.99 | 5.287 |
| Kalman Q_media | 0.09417 | 17.33 | 3.819 | 1.852 | 1.477 | 3.265 | 68.77 |
| Media móvil N=21 + Euler | 0.06671 | 98.22 | 98.12 | 1.853 | 1.605 | 0.8874 | 16.67 |
| Media móvil N=5 + Euler | 0.1044 | 19.69 | 19.22 | 1.853 | 1.49 | 3.594 | 15.1 |

Generado por código · commit 54720e5+cambios_sin_commit · manifiesto datos/crudos/manifiesto.json
