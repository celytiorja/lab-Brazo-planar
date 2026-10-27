# Selección de Q (promedios de ajuste)

| metodo | retraso_omega_ms | ruido_omega_reposo_dps | error_estacionario_rms_deg | deriva_final_deg |
| --- | --- | --- | --- | --- |
| Kalman Q_alta | 2.264 | 0.03848 | 0.3435 | 0.3567 |
| Kalman Q_baja | 68.54 | 0.1268 | 0.3453 | 0.3567 |
| Kalman Q_media | 13.38 | 0.02313 | 0.3429 | 0.3535 |

Elegida: **Q_media** (f_c = 5.0 Hz, q = 0.03586 °²/s³). Regla: menor ruido de ω en reposo entre las configuraciones con retraso de ω ≤ 40.0 ms (promedio en registros de ajuste).
