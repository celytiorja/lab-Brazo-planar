# Aceleración angular numérica — ruido en reposo (eslabón 1, seno_rapido_01)

| fuente | sigma_alfa_reposo_dps2 |
| --- | --- |
| giro crudo, diferencia hacia atrás | 8.4 |
| giro crudo, diferencia central | 3.881 |
| Media móvil N=5 + Euler, hacia atrás | 1.627 |
| Media móvil N=21 + Euler, hacia atrás | 0.4433 |
| Kalman Q_baja, hacia atrás | 1.655 |
| Kalman Q_media, hacia atrás | 1.639 |
| Kalman Q_alta, hacia atrás | 4.212 |
| TEÓRICO hacia atrás: √2·σω/Δt | 7.97 |
| TEÓRICO central: σω/(√2·Δt) | 3.985 |

σω en reposo = 0.0564 °/s, Δt = 10.00 ms. Derivar divide por Δt: el ruido se multiplica por ≈ 141.
