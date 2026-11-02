# Ruido en reposo vs en movimiento

| archivo | eslabon | ruido_aparente_reposo_dps | ruido_aparente_movimiento_dps | cociente_mov_reposo |
| --- | --- | --- | --- | --- |
| escalones_01 | 1 | 0.05225 | 12.57 | 240.5 |
| escalones_01 | 2 | 0.04914 | 13.6 | 276.8 |
| seno_lento_01 | 1 | 0.0949 | 4.211 | 44.37 |
| seno_lento_01 | 2 | 0.1814 | 5.891 | 32.48 |
| seno_rapido_01 | 1 | 0.1913 | 3.851 | 20.13 |
| seno_rapido_01 | 2 | 0.4157 | 5.45 | 13.11 |

Residuo de alta frecuencia: w − Savitzky–Golay (ventana 11, orden 3). Un cociente > 1 indica que la R medida en reposo SUBESTIMA el ruido real durante el movimiento. El residuo en movimiento incluye vibración del servo, los pasos de 1° de la consigna (el servo solo acepta grados enteros) y, en 'escalones', los arranques bruscos: todo eso es 'ruido' para un modelo de velocidad casi constante.
