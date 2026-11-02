# Integrar con Δt_k real vs Δt = 1/fs

| archivo | eslabon | perdidas | dt_max_ms | diferencia_final_deg | diferencia_max_deg |
| --- | --- | --- | --- | --- | --- |
| estatico_03 | 1 | 0 | 10 | 4.984e-15 | 5.807e-15 |
| estatico_03 | 2 | 0 | 10 | -3.948e-15 | 3.948e-15 |
| escalones_01 | 1 | 0 | 10.06 | -0.0009514 | 0.001284 |
| escalones_01 | 2 | 0 | 10.06 | -0.001044 | 0.002267 |

Con Δt nominal, cada muestra perdida hace 'desaparecer' 10 ms de giro y el ángulo queda corrido; con el Δt_k del timestamp ese tramo se integra completo.
