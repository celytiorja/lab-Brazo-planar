# Estructura de R: estacionariedad y correlación

| canal | ventanas_5s | varianza_total | varianza_min | varianza_max | cociente_max_min | media_min | media_max | levene_p | varianza_estacionaria |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| w1 | 8 | 0.0008918 | 0.0008313 | 0.0009366 | 1.127 | 0.2521 | 0.2643 | 0.8297 | True |
| w2 | 8 | 0.001062 | 0.00098 | 0.001176 | 1.2 | -0.5069 | -0.5009 | 0.7194 | True |

Correlación w1–w2 = -0.000 → |ρ| < 0.1: R **diagonal** es suficiente. Levene p > 0.05 = no hay evidencia de que la varianza cambie entre tramos (ruido estacionario).
