# Integrar con Δt_k real vs Δt = 1/fs

| archivo | eslabon | perdidas | dt_max_ms | diferencia_final_deg | diferencia_max_deg |
| --- | --- | --- | --- | --- | --- |
| estatico_01 | 1 | 1 | 20.06 | 0.0005371 | 0.0005463 |
| estatico_01 | 2 | 1 | 20.06 | 0.0002195 | 0.0002328 |
| escalones_01 | 1 | 1 | 20.01 | 0.01807 | 0.02606 |
| escalones_01 | 2 | 1 | 20.01 | -0.0004867 | 0.02784 |

Con Δt nominal, cada muestra perdida hace 'desaparecer' 10 ms de giro y el ángulo queda corrido; con el Δt_k del timestamp ese tramo se integra completo.
