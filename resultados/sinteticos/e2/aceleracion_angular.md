# Aceleración angular numérica — ruido en reposo (eslabón 1, seno_rapido_01)

| fuente | sigma_alfa_reposo_dps2 |
| --- | --- |
| giro crudo, diferencia hacia atrás | 8.551 |
| giro crudo, diferencia central | 3.885 |
| Media móvil N=5 + Euler, hacia atrás | 1.631 |
| Media móvil N=21 + Euler, hacia atrás | 0.4562 |
| Kalman Q_baja, hacia atrás | 1.824 |
| Kalman Q_media, hacia atrás | 1.658 |
| Kalman Q_alta, hacia atrás | 4.272 |
| TEÓRICO hacia atrás: √2·σω/Δt | 7.989 |
| TEÓRICO central: σω/(√2·Δt) | 3.995 |

σω en reposo = 0.0565 °/s, Δt = 10.00 ms. Derivar divide por Δt: el ruido se multiplica por ≈ 141.
