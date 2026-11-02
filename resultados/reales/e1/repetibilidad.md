# Repetibilidad del ensayo dinámico

| perfil | eslabon | consigna_coincide_frac | rms_diferencia_entre_repeticiones_deg | error_estacionario_rep1_deg | error_estacionario_rep2_deg |
| --- | --- | --- | --- | --- | --- |
| escalones | 1 | 0.9964 | 4.491 | 5.759 | 1.536 |
| escalones | 2 | 0.9964 | 1.81 | 4.425 | 4.152 |
| seno_lento | 1 | 0.5372 | 1.341 | 0.2648 | 0.4114 |
| seno_lento | 2 | 0.5372 | 2.773 | 0.8032 | 1.871 |
| seno_rapido | 1 | 0.3627 | 0.8667 | 0.6475 | 0.06618 |
| seno_rapido | 2 | 0.3627 | 2.143 | 3.816 | 3.076 |

Se comparan las dos repeticiones alineadas por tiempo (la consigna la genera el firmware en función del tiempo) con integración directa. consigna_coincide < 1 aparece en los bordes de cada cambio por la fluctuación de ±1 muestra.
