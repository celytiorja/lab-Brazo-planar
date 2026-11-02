# Repetibilidad del ensayo dinámico

| perfil | eslabon | consigna_coincide_frac | rms_diferencia_entre_repeticiones_deg | error_estacionario_rep1_deg | error_estacionario_rep2_deg |
| --- | --- | --- | --- | --- | --- |
| escalones | 1 | 0.9964 | 0.5085 | 0.6587 | 0.6477 |
| escalones | 2 | 0.9964 | 0.5225 | 0.8674 | 0.8863 |
| seno_lento | 1 | 0.9996 | 0.1121 | 0.09885 | 0.1779 |
| seno_lento | 2 | 0.9996 | 0.07149 | 0.07774 | 0.04855 |
| seno_rapido | 1 | 1 | 0.1608 | 0.1936 | 0.009551 |
| seno_rapido | 2 | 1 | 0.1193 | 0.3385 | 0.1864 |

Se comparan las dos repeticiones alineadas por tiempo (la consigna la genera el firmware en función del tiempo) con integración directa. consigna_coincide < 1 aparece en los bordes de cada cambio por la fluctuación de ±1 muestra.
