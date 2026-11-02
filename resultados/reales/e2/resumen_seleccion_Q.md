# Selección de Q (promedios de ajuste)

| metodo | retraso_omega_ms | ruido_omega_reposo_puro_dps | ruido_omega_reposo_dps | error_estacionario_rms_deg | deriva_final_deg |
| --- | --- | --- | --- | --- | --- |
| Kalman Q_alta | 4.672 | 0.02247 | 0.4861 | 2.619 | 3.349 |
| Kalman Q_baja | 55.3 | 0.008479 | 0.2633 | 2.62 | 3.35 |
| Kalman Q_media | 17.59 | 0.01444 | 0.3647 | 2.619 | 3.349 |

Elegida: **Q_media** (f_c = 5.0 Hz, q = 0.00972 °²/s³). Regla: menor ruido de ω en reposo PURO (estatico_03) entre las configuraciones con retraso de ω ≤ 40.0 ms (retraso promedio en registros de ajuste).
