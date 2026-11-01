# Repetibilidad del ensayo dinámico

| perfil | eslabon | consigna_coincide_frac | rms_diferencia_entre_repeticiones_deg | error_estacionario_rep1_deg | error_estacionario_rep2_deg |
| --- | --- | --- | --- | --- | --- |
| escalones | 1 | 1 | 0.07616 | 0.641 | 0.6145 |
| escalones | 2 | 1 | 0.126 | 0.8071 | 0.9006 |
| seno_lento | 1 | 1 | 0.1261 | 0.09191 | 0.1845 |
| seno_lento | 2 | 1 | 0.06891 | 0.04268 | 0.01991 |
| seno_rapido | 1 | 1 | 0.1518 | 0.1583 | 0.01821 |
| seno_rapido | 2 | 1 | 0.1136 | 0.3084 | 0.175 |

Se comparan las dos repeticiones alineadas por tiempo (la consigna la genera el firmware en función del tiempo) con integración directa. consigna_coincide < 1 aparece en los bordes de cada cambio por la fluctuación de ±1 muestra.
