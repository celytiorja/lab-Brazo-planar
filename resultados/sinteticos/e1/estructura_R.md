# Estructura de R: estacionariedad y correlación

| canal | ventanas_5s | varianza_total | varianza_min | varianza_max | cociente_max_min | media_min | media_max | levene_p | varianza_estacionaria |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| w1 | 7 | 0.003665 | 0.003209 | 0.004131 | 1.287 | 0.354 | 0.3583 | 0.02492 | False |
| w2 | 7 | 0.003541 | 0.00317 | 0.003922 | 1.237 | 0.1077 | 0.1179 | 0.296 | True |

Correlación w1–w2 = +0.017 → |ρ| < 0.1: R **diagonal** es suficiente. Levene p > 0.05 = no hay evidencia de que la varianza cambie entre tramos (ruido estacionario).
