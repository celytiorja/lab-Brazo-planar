# Aceleración angular numérica — ruido en reposo (eslabón 1, seno_rapido_01)

| fuente | sigma_alfa_reposo_dps2 |
| --- | --- |
| giro crudo, diferencia hacia atrás | 4.895 |
| giro crudo, diferencia central | 2.989 |
| Media móvil N=5 + Euler, hacia atrás | 1.409 |
| Media móvil N=21 + Euler, hacia atrás | 0.5238 |
| Kalman Q_baja, hacia atrás | 1.93 |
| Kalman Q_media, hacia atrás | 1.248 |
| Kalman Q_alta, hacia atrás | 2.846 |
| TEÓRICO hacia atrás: √2·σω/Δt | 6.567 |
| TEÓRICO central: σω/(√2·Δt) | 3.284 |

σω en reposo = 0.0464 °/s, Δt = 10.00 ms. Derivar divide por Δt: el ruido se multiplica por ≈ 141.
