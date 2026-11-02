# Ruido en reposo vs en movimiento

| archivo | eslabon | ruido_aparente_reposo_dps | ruido_aparente_movimiento_dps | cociente_mov_reposo |
| --- | --- | --- | --- | --- |
| escalones_01 | 1 | 0.233 | 3.477 | 14.92 |
| escalones_01 | 2 | 0.2967 | 12.22 | 41.17 |
| seno_lento_01 | 1 | 0.3975 | 3.167 | 7.969 |
| seno_lento_01 | 2 | 0.4439 | 6.605 | 14.88 |
| seno_rapido_01 | 1 | 0.0303 | 4.364 | 144 |
| seno_rapido_01 | 2 | 0.03907 | 9.565 | 244.8 |

Residuo de alta frecuencia: w − Savitzky–Golay (ventana 11, orden 3). Un cociente > 1 indica que la R medida en reposo SUBESTIMA el ruido real durante el movimiento. El residuo en movimiento incluye vibración del servo, los pasos de 1° de la consigna (el servo solo acepta grados enteros) y, en 'escalones', los arranques bruscos: todo eso es 'ruido' para un modelo de velocidad casi constante.
