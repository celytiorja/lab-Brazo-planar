# Selección de Q (promedios de ajuste)

| metodo | retraso_omega_ms | ruido_omega_reposo_puro_dps | ruido_omega_reposo_dps | error_estacionario_rms_deg | deriva_final_deg |
| --- | --- | --- | --- | --- | --- |
| Kalman Q_alta | 2.264 | 0.03979 | 0.03885 | 0.3745 | 0.3743 |
| Kalman Q_baja | 68.55 | 0.01275 | 0.1406 | 0.3768 | 0.3743 |
| Kalman Q_media | 13.38 | 0.02346 | 0.02332 | 0.3739 | 0.3712 |

Elegida: **Q_media** (f_c = 5.0 Hz, q = 0.03586 °²/s³). Regla: menor ruido de ω en reposo PURO (estatico_01) entre las configuraciones con retraso de ω ≤ 40.0 ms (retraso promedio en registros de ajuste).
